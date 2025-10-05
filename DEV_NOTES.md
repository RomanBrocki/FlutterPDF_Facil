# 🧩 PDF Fácil — Notas de Desenvolvimento (DEV_NOTES)

Este documento serve como **referência técnica interna** para desenvolvedores.  
Ele complementa os READMEs principais (`README.md`, `README_API.md`, `README_ENGINE.md`), focando em **integração entre módulos**, **boas práticas** e **detalhes internos** do backend.

---

## 🧠 Arquitetura geral

```
PDF_Facil_API/
├─ api/                # Lógica de rede (FastAPI)
│  ├─ main.py          # Endpoints principais
│  ├─ storage.py       # Sessões efêmeras em RAM
│  ├─ jobs.py          # Armazenamento dos PDFs prontos (one-time)
│  ├─ thumbs.py        # Geração de miniaturas
│  └─ schemas.py       # Modelos Pydantic de entrada/saída
├─ engine/             # Motor puro de PDF
│  ├─ engine_config.py # Presets de compressão
│  └─ pdf_ops.py       # Lógica de compressão, merge e split
├─ index.html          # Frontend (GitHub Pages)
├─ requirements.txt    # Dependências Python
└─ runtime.txt         # Versão Python (Render)
```

---

## 🔄 Integração entre API e Engine

| Camada | Função | Comunicação |
|--------|---------|--------------|
| **API (FastAPI)** | Gera tokens, controla sessões, recebe e envia JSON | Chama funções da engine |
| **Engine (pdf_ops)** | Faz compressão, merge, split e estimativas | Opera em bytes (sem estado) |

> A API nunca armazena arquivos em disco: tudo é mantido em **RAM** até expirar (`TTL_MINUTES`).

---

## ⚙️ Sessões e Jobs

- **Sessões (`storage.py`)**: criadas no `/preview`, armazenam os bytes originais e metadados de páginas.  
  - Dicionário: `SESSIONS[token] = Session(files, names, items)`  
  - Expiram conforme `TTL_MINUTES`.

- **Jobs (`jobs.py`)**: criados no `/process`, armazenam o PDF final pronto para download.  
  - Dicionário: `JOBS[job_id] = (bytes, timestamp, filename)`  
  - São apagados após o download (one-time).

Ambos são limpos por funções periódicas `purge_expired()` e `purge_expired_jobs()` chamadas automaticamente.

---

## ⚡ Convenções e Padrões

### Padrões de compressão
- Definidos em `engine/engine_config.py`
- Mapeiam `"none" | "min" | "med" | "max"` para `{mode, dpi, jpg_q}`

### Padrões de API
- `level_global` sobrescreve todos os níveis por página.  
- `level_page` é completado automaticamente com `"none"` se vier curto.  
- `filename_out` recebe `.pdf` se o usuário omitir a extensão.

### Padrões de design
- Guard-rail: nunca aumenta o tamanho do arquivo (`after <= before`).  
- TTL padrão: **15 minutos**.  
- Máximo de upload: **50 MB por arquivo / 75 MB por lote** (configurável via env).

---

## 🧮 Processamento interno

Fluxo do `/process` em pseudocódigo simplificado:

```python
def process(payload):
    session = SESSIONS[payload.token]
    levels = _levels_apply(payload.level_page, payload.level_global, payload.keep)
    pages_flat = [(name, data, kind, page_index, level) for cada página mantida]
    rotation_seq = payload.rotate

    # Geração do PDF
    out_bytes = merge_pages(pages_flat, rotation_seq)
    job_id = save_job(out_bytes, filename)

    return { "job_id": job_id, "download_url": f"/download/one-time/{job_id}" }
```

---

## 🔒 Segurança e privacidade

- **Stateless**: nenhum dado persistido em disco.  
- **One-time downloads**: o PDF é excluído da RAM após ser baixado.  
- **CORS controlado**: apenas domínios autorizados podem acessar via navegador.  
- **Sem dependência de banco de dados.**

---

## 🧰 Dependências principais

| Tipo | Biblioteca | Uso |
|------|-------------|-----|
| Servidor | FastAPI / Uvicorn | Backend HTTP e roteamento |
| PDF | PyMuPDF (fitz) | Leitura, renderização e compressão |
| Imagens | Pillow | Processamento de miniaturas e JPEGs |
| PDF wrapper | img2pdf / pypdf | Montagem e merge de PDFs |
| Tipagem | Pydantic | Validação de modelos JSON |

---

## 🧪 Testes locais recomendados

```bash
uvicorn api.main:app --reload
# http://127.0.0.1:8000/docs
```

Ordem de teste:
1. `/preview` → gera thumbs e token  
2. `/estimate` → calcula tamanhos antes/depois  
3. `/process` → gera PDF final e devolve link  
4. `/download/one-time/{job_id}` → baixa o arquivo (one-time)

---

## 🧩 Boas práticas de desenvolvimento

- Documente alterações em README_API.md e README_ENGINE.md.  
- Mantenha funções puras e modulares (sem dependência circular).  
- Evite gravação em disco — use bytes e memória.  
- Prefira `BytesIO` em vez de arquivos temporários.  
- Atualize `requirements.txt` e `runtime.txt` sempre que novas libs forem adicionadas.

---

## 👨‍💻 Autor

**Roman Brocki** — desenvolvimento completo da arquitetura, API e engine.  
Hospedagem gratuita em **Render** (backend) e **GitHub Pages** (frontend).

---

> Este documento é voltado a desenvolvedores que pretendem entender ou expandir o projeto.
