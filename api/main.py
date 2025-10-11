from __future__ import annotations
from typing import List, Optional
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # usado só para contar páginas de PDFs



from pydantic import BaseModel

import io
from PIL import Image

from .schemas import EstimateIn, ProcessIn
from .jobs import save_job, pop_job, purge_expired_jobs
from engine.pdf_ops import estimate_pdf_page_size, estimate_image_pdf_size, merge_pages
from .storage import SESSIONS, Session, new_token, purge_expired
from .thumbs import pdf_page_thumb, image_thumb

# ---- Config mínimos (ambiente ou default) ----
FILE_MAX_MB  = int(os.getenv("FILE_MAX_MB", "50"))
BATCH_MAX_MB = int(os.getenv("BATCH_MAX_MB", "75"))

origins_env = (os.getenv("CORS_ALLOW_ORIGINS", "*") or "*").strip()
allow_all = (origins_env == "*")
CORS_ALLOW_ORIGINS = ["*"] if allow_all else [o.strip() for o in origins_env.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = False if allow_all else True

app = FastAPI(title="PDF Fácil — API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=".*",
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)




def _bytes_mb(n: int) -> float:
    return n / (1024 * 1024)

def _ensure_limits(blobs: List[bytes]):
    sizes = [_bytes_mb(len(b)) for b in blobs]
    if any(sz > FILE_MAX_MB for sz in sizes):
        raise HTTPException(status_code=413, detail=f"Arquivo excede {FILE_MAX_MB} MB.")
    if sum(sizes) > BATCH_MAX_MB:
        raise HTTPException(status_code=413, detail=f"Lote excede {BATCH_MAX_MB} MB.")

def _is_pdf(name: str, blob: bytes) -> bool:
    return (name.lower().endswith(".pdf") or blob[:5] == b"%PDF-")

def _before_size_approx(src_bytes: bytes, is_pdf: bool, page_ix: int, page_count: int, areas: list[int] | None) -> int:
    """
    Estima o tamanho 'antes' por página.
    - Imagem: tamanho total do arquivo.
    - PDF: distribui pelo share da área da página no total (melhor que dividir por N).
    """
    if not is_pdf:
        return len(src_bytes)
    # areas foi calculada uma única vez por PDF no próprio endpoint
    total_area = max(1, sum(areas or []))
    share = (areas[page_ix] / total_area) if areas else (1 / max(1, page_count))
    return int(len(src_bytes) * share)


def _levels_apply(level_page: list[str], level_global: str | None, keep: list[bool]) -> list[str]:
    """Normaliza níveis por página e aplica `level_global` quando válido.

    Regras:
    - Se `level_page` vier vazio/curto, completa com 'none' até o tamanho de `keep`.
    - Níveis inválidos viram 'none'.
    - `level_global` só é aplicado se for um dos válidos ('none'|'min'|'med'|'max').
    - Páginas com `keep=False` mantêm o nível da posição (irrelevante no processamento).
    """
    VALID = {"none", "min", "med", "max"}
    lp = (level_page or [])[:]
    # completa para o tamanho de keep
    if len(lp) < len(keep):
        lp += ["none"] * (len(keep) - len(lp))
    # sanitiza conteúdo
    lp = [lv if lv in VALID else "none" for lv in lp]
    if level_global in VALID:
        return [level_global if k else lv for k, lv in zip(keep, lp)]
    return lp[:]

@app.get("/health")
def health():
    purge_expired()
    return {"ok": True}

@app.post("/preview")
async def preview(files: List[UploadFile] = File(...), filename_out: Optional[str] = Form(None)):
    """
    Recebe PDFs/Imagens, retorna thumbnails por página + token de sessão.
    Nada é persistido; blobs ficam em RAM (TTL definido em TTL_MINUTES).
    """
    # 1) ler tudo
    blobs, names = [], []
    for f in files:
        data = await f.read()
        blobs.append(data)
        names.append(f.filename or "file")

    # 2) limites
    _ensure_limits(blobs)

    # 3) construir lista de páginas (items)
    items = []
    for src_id, (data, name) in enumerate(zip(blobs, names)):
        is_pdf = (name.lower().endswith(".pdf") or data[:5] == b"%PDF-")
        if is_pdf:
            doc = fitz.open(stream=data, filetype="pdf")
            for p in range(doc.page_count):
                thumb_b64, w, h = pdf_page_thumb(data, p)
                items.append({
                    "src_id": src_id,
                    "page_index": p,
                    "is_pdf": True,
                    "w": w, "h": h,
                    "thumb_b64": thumb_b64
                })
            doc.close()
        else:
            thumb_b64, w, h = image_thumb(data)
            items.append({
                "src_id": src_id,
                "page_index": 0,
                "is_pdf": False,
                "w": w, "h": h,
                "thumb_b64": thumb_b64
            })

    # 4) criar sessão efêmera
    token = new_token()
    SESSIONS[token] = Session(files=blobs, names=names, items=items)
    purge_expired()

    return JSONResponse({
        "token": token,
        "items": items,
        "page_count_total": len(items),
        "limits": {"max_file_mb": FILE_MAX_MB, "max_batch_mb": BATCH_MAX_MB},
    })

@app.post("/estimate")
def estimate(payload: EstimateIn):
    """
    Simula tamanhos 'before' e 'after' por página e total.
    - 'before': estimado por área da página (PDF) ou tamanho da imagem.
    - 'after': heurística de compressão (JPEG em memória) para páginas-imagem;
               páginas com texto/vetores são tratadas como 'sem ganho' (igual ao before).
    Guard-rail: nunca piora (after <= before).
    """
    purge_expired()
    s = SESSIONS.get(payload.token)
    if not s:
        raise HTTPException(status_code=404, detail="Sessão expirada.")

    # normaliza níveis
    levels = _levels_apply(payload.level_page, payload.level_global, payload.keep)

    # Pré-calcula metadados por arquivo PDF (page_count e áreas) só 1x
    # Mapeia src_id -> (is_pdf, page_count, areas[])
    import fitz
    pdf_meta = {}
    for src_id, (blob, name) in enumerate(zip(s.files, s.names)):
        if _is_pdf(name, blob):
            doc = fitz.open(stream=blob, filetype="pdf")
            areas = [int(doc.load_page(i).rect.width * doc.load_page(i).rect.height) for i in range(doc.page_count)]
            pdf_meta[src_id] = (True, doc.page_count, areas)
            doc.close()
        else:
            pdf_meta[src_id] = (False, 1, None)

    total_before = 0
    total_after  = 0
    per_page = []

    for keep, rot, lv, ord_item in zip(payload.keep, payload.rotate, levels, payload.order):
        if not keep:
            per_page.append({"before": 0, "after": 0})
            continue

        src_id  = ord_item.src_id
        page_ix = ord_item.page_index
        blob    = s.files[src_id]
        name    = s.names[src_id]

        is_pdf, page_count, areas = pdf_meta[src_id]
        before = _before_size_approx(blob, is_pdf, page_ix, page_count, areas)

        # ======= estimativa 'after' (via pdf_ops) =======
        if lv not in ("none","min","med","max"):
            lv = "none"

        if not is_pdf:
            after = estimate_image_pdf_size(blob, lv)
        else:
            after = estimate_pdf_page_size(blob, page_ix, lv)


        # guard-rail
        after = min(after, before)

        total_before += before
        total_after  += after
        per_page.append({"before": before, "after": after})

    return JSONResponse({
        "total_before_bytes": total_before,
        "total_after_bytes": total_after,
        "per_page": per_page,
        "notes": []
    })

@app.post("/process")
def process(payload: ProcessIn):
    """
    Gera o PDF final chamando merge_pages (engine/pdf_ops) e retorna link one-time.
    Regras:
    - Usa mesmos arrays do /estimate: order/keep/rotate/level_page/level_global.
    - Níveis por página são aplicados com _levels_apply.
    - Artefato fica em RAM (TTL) e é apagado no download.
    """
    purge_expired()            # sessões
    purge_expired_jobs()       # jobs

    s = SESSIONS.get(payload.token)
    if not s:
        raise HTTPException(status_code=404, detail="Sessão expirada.")

    levels = _levels_apply(payload.level_page, payload.level_global, payload.keep)

    # Monta sequência final (apenas páginas keep=True), preservando a ordem
    pages_flat = []   # (name, data, kind, page_idx, level)
    rotation_seq = [] # [int]
    for k, rot, lv, ord_item in zip(payload.keep, payload.rotate, levels, payload.order):
        if not k:
            continue
        src_id  = ord_item.src_id
        page_ix = ord_item.page_index
        name    = s.names[src_id]
        blob    = s.files[src_id]
        kind    = "pdf" if (name.lower().endswith(".pdf") or blob[:5] == b"%PDF-") else "image"

        if lv not in ("none","min","med","max"):
            lv = "none"

        pages_flat.append((name, blob, kind, page_ix, lv))
        rotation_seq.append(int(rot or 0))

    if not pages_flat:
        raise HTTPException(status_code=400, detail="Nenhuma página selecionada.")

    # Gera bytes finais
    out_bytes = merge_pages(pages_flat, rotation_seq)
    filename = (payload.filename_out or "arquivo_final.pdf").strip()
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"


    # Guarda job (one-time)
    job_id = save_job(out_bytes, filename)
    return JSONResponse({
        "job_id": job_id,
        "download_url": f"/download/one-time/{job_id}",
        "filename": filename,
        "size_bytes": len(out_bytes),
    })

@app.get("/download/one-time/{job_id}")
def download(job_id: str):
    """
    Serve o PDF final e apaga da RAM (one-time). Expirado ou já baixado → 404.
    """
    purge_expired_jobs()
    item = pop_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="job não encontrado/expirado.")
    data, filename = item
    return StreamingResponse(
        __import__("io").BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
