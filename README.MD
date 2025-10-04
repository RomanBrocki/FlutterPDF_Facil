# PDF_Fácil API (FlutterFlow + Render)

Backend em **FastAPI** que expõe o seu motor existente (`engine/pdf_ops.py`) para:
- Upload & **pré-visualização** (thumbnails por página)
- **Estimativa** de tamanho antes/depois (por página e total)
- **Processamento** (gera PDF final com compressão/rotação/ordem)
- **Download** por link one-time (artefato em RAM com TTL)

Stateless, sem banco de dados. Ideal para front em **FlutterFlow** via Custom API.

---

## Objetivo

Reaproveitar o `pdf_ops.py` do projeto antigo (Streamlit) como um backend HTTP simples, mantendo a UX: upload, preview, ordenação, rotação, compressão por página/global, simulação e download.

---

## Estrutura do Código

```
FlutterPDF_Facil/
├─ api/
│  ├─ __init__.py
│  ├─ main.py          # FastAPI: /health, /preview, /estimate, /process, /download
│  ├─ storage.py       # Sessões efêmeras (arquivos + páginas) com TTL
│  ├─ thumbs.py        # Thumbnails (PDF/Imagem) com PyMuPDF + Pillow
│  ├─ schemas.py       # Modelos Pydantic dos payloads
│  └─ jobs.py          # Artefatos finais em RAM (one-time) com TTL
├─ engine/
│  ├─ __init__.py
│  ├─ engine_config.py # Mapas de níveis ("none"|"min"|"med"|"max")
│  └─ pdf_ops.py       # Motor existente (reaproveitado)
├─ requirements.txt
├─ requirements-dev.txt   # opcional (testes)
├─ environment.yml        # opcional (Conda)
└─ runtime.txt            # versão Python para Render
```

**Níveis de compressão:** definidos em `engine/engine_config.py`  
`"none" | "min" | "med" | "max"`

---

## Componentes da API

### Sessões (api/storage.py)
- Criadas em **/preview**; guardam **blobs** originais e **lista de páginas**.
- Expiradas por `TTL_MINUTES` (RAM apenas).

### Thumbnails (api/thumbs.py)
- Geração de `thumb_b64` para cada página (PDF/Imagem) usando PyMuPDF + Pillow.

### Estimativa (POST /estimate)
- Usa diretamente o motor:
  - `engine.pdf_ops.estimate_pdf_page_size(pdf_bytes, page_idx, level)`
  - `engine.pdf_ops.estimate_image_pdf_size(img_bytes, level)`
- Guard-rail: `after <= before`.

### Processamento (POST /process)
- Monta `pages_flat` + `rotation_seq` e chama:
  - `engine.pdf_ops.merge_pages(pages_flat, rotation_seq)`
- Salva o resultado em **api/jobs.py** (RAM + TTL).
- Download por **/download/one-time/{job_id}** (one-time).

---

## Endpoints

### `GET /health`
Retorna:
```json
{ "ok": true }
```

### `POST /preview` (multipart/form-data)
Campos:
- `files[]`: múltiplos arquivos (PDF/JPG/PNG)
- `filename_out` (opcional)

Resposta (resumo):
```json
{
  "token": "abc123",
  "items": [
    {
      "src_id": 0,
      "page_index": 0,
      "is_pdf": true,
      "w": 1240,
      "h": 1754,
      "thumb_b64": "data:image/jpeg;base64,..."
    }
  ],
  "page_count_total": 12,
  "limits": { "max_file_mb": 50, "max_batch_mb": 75 }
}
```

### `POST /estimate` (application/json)
Body:
```json
{
  "token": "abc123",
  "order": [ {"src_id":0,"page_index":0}, {"src_id":0,"page_index":1} ],
  "keep":   [ true, true ],
  "rotate": [ 0, 0 ],
  "level_page": [ "none", "none" ],
  "level_global": "med"   // opcional (aplica a todas com keep=true)
}
```
Resposta (resumo):
```json
{
  "total_before_bytes": 12345678,
  "total_after_bytes":  4567890,
  "per_page": [ {"before": 123456, "after": 78901}, ... ],
  "notes": []
}
```

### `POST /process` (application/json)
Body (mesmo do /estimate + `filename_out`):
```json
{
  "token": "abc123",
  "order": [ {"src_id":0,"page_index":0}, {"src_id":0,"page_index":1} ],
  "keep":   [ true, true ],
  "rotate": [ 0, 0 ],
  "level_page": [ "none", "none" ],
  "level_global": "max",
  "filename_out": "resultado.pdf"
}
```
Resposta:
```json
{
  "job_id": "xyz987",
  "download_url": "/download/one-time/xyz987",
  "filename": "resultado.pdf",
  "size_bytes": 4567890
}
```

### `GET /download/one-time/{job_id}`
Baixa o PDF e apaga da RAM. Se expirado/baixado → 404.  
Headers: `Content-Disposition: attachment; filename="{filename}"`

> Observação: o `download_url` é relativo; prefixe com host (ex.: `http://127.0.0.1:8000`).

---

## Variáveis de Ambiente

- `FILE_MAX_MB` (padrão `50`)
- `BATCH_MAX_MB` (padrão `75`)
- `TTL_MINUTES` (padrão `15`)
- `CORS_ALLOW_ORIGINS` (ex.: `https://app.flutterflow.io,https://<seu>.flutterflow.app`)

---

## Instalação

### Conda (opcional)
`environment.yml`:
```yaml
name: pdf_facil_api
channels: [conda-forge]
dependencies:
  - python=3.11
  - pip
  - pip:
      - -r requirements.txt
```
Comandos:
```bash
conda env create -f environment.yml
conda activate pdf_facil_api
# opcional
pip install -r requirements-dev.txt
```

### Pip
`requirements.txt`:
```
fastapi
uvicorn[standard]
python-multipart
pydantic>=2
Pillow
PyMuPDF
img2pdf
pypdf
```

---

## Executar (local)

```bash
uvicorn api.main:app --reload
# http://127.0.0.1:8000/health
# http://127.0.0.1:8000/docs
```

Fluxo de teste no `/docs`:
1. **POST /preview** → pegue `token`.
2. **POST /estimate** → use `level_global` ("min"/"med"/"max") ou `level_page`.
3. **POST /process** → recebe `job_id` e `download_url`.
4. **GET /download/one-time/{job_id}** → baixa o PDF (one-time).

---

## Deploy (Render)

1) Código + `requirements.txt` + `runtime.txt` (ex.: `python-3.11.9`)  
2) Variáveis: `FILE_MAX_MB`, `BATCH_MAX_MB`, `TTL_MINUTES`, `CORS_ALLOW_ORIGINS`  
3) Start command:
```
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

---

## Integração (FlutterFlow)

- **Custom API Calls**:
  - `POST /preview` (multipart) → guarda `token` e páginas
  - `POST /estimate` (JSON) → “antes/depois”
  - `POST /process` (JSON) → `download_url`
  - `GET /download/one-time/{job_id}` → download
- Os arrays `order/keep/rotate/level_page` devem ter **mesmo tamanho do total de páginas**.
- Para compressão global, use `level_global` e mantenha `level_page` como `"none"`.

---

## Observações

- Sessões e jobs expiram por TTL (RAM; sem persistência).  
- O `/process` **não** lê estado do `/estimate`: reenvie tudo no body.  
- Para garantir extensão no arquivo final, envie `filename_out` com `.pdf`.  
- Para URL absoluta no `/process`, use `request.url_for("download", job_id=...)`.

---
