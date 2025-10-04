# Documentação do Projeto (PDF_Fácil API)

Este documento comenta cada arquivo do projeto, explica responsabilidades, funções públicas principais, fluxos e convenções de uso.

> **Resumo**: Backend FastAPI stateless para *preview → estimativa → processamento → download one-time*,
reutilizando um motor puro (engine/pdf_ops.py). Tudo em RAM, com TTL.

---

## api/main.py
- **O que é:** aplicação FastAPI, endpoints `/health`, `/preview`, `/estimate`, `/process`, `/download/one-time/{job_id}`.
- **Pontos-chave:**
  - Limites por arquivo e por lote via `FILE_MAX_MB` e `BATCH_MAX_MB`.
  - Gera **thumbnails** por página (PDF/Imagem) e **token** de sessão efêmera.
  - **Estimativa**: calcula `before/after` por página com guard-rails (`after <= before`).
  - **Processo**: aplica **ordem**, **keep**, **rotação** e **nível** por página e gera um PDF final em RAM.
  - **Download one-time**: consome e apaga o artefato (RAM + TTL).
- **Padrões:** nível de compressão **padrão é `none`**. O backend completa `level_page` com `none` quando faltante/curto e só aplica `level_global` se informado e válido.

## api/storage.py
- **Sessões** em RAM com TTL, mapeando `token -> Session(files, names, items)`
- **`purge_expired()`** apaga sessões antigas.
- **Uso:** `/preview` cria sessão; `/estimate` e `/process` buscam pelo `token`.

## api/jobs.py
- Armazena **artefatos finais** (PDFs) em RAM com TTL.
- **`save_job()`** retorna `job_id` para **download one-time**.
- **`pop_job()`** retorna e apaga.

## api/schemas.py
- Modelos **Pydantic** de entrada para `/estimate` e `/process`.
- **Observação:** `level_global` é opcional. `level_page` pode vir vazio, o backend preenche `none`.

## api/thumbs.py
- Geração de **thumbnails** JPEG base64 para:
  - Páginas de PDF (`pdf_page_thumb()`)
  - Imagens (`image_thumb()`)
- Respeita *bounding box* e DPI de preview.

## engine/engine_config.py
- Declara presets de compressão:
  - `none` (sem compressão)
  - `min` (smart: rasteriza apenas páginas imagem-only, DPI 200, JPEG 85)
  - `med` (all: rasteriza todas, DPI 150, JPEG 70)
  - `max` (all: rasteriza todas, DPI 110, JPEG 50)

## engine/pdf_ops.py
- **Motor puro** sem dependência de FastAPI/estado.
- Funções principais:
  - `estimate_pdf_page_size`, `estimate_image_pdf_size`, `estimate_pdf_size`
  - `compress_pdf`, `image_to_pdf_bytes`
  - `merge_pages`, `merge_items`, `split_pdf`
- **Guard-rails:** nunca piora o tamanho (se não reduzir, mantém original).

---

## Fluxo recomendado (FlutterFlow)
1. **POST /preview** → obter `token` + páginas (com thumbs) e limites.
2. **UI**: ordenar, marcar `keep`, girar, selecionar níveis (por página ou `level_global`).
3. **POST /estimate** → mostrar *antes/depois* ao usuário (opcional).
4. **POST /process** → receber `download_url` + `filename` + `size_bytes`.
5. **GET /download/one-time/{job_id}`** → realizar o download (one-time).

---

## Convenções e Notas
- Arrays `order`, `keep`, `rotate` e `level_page` devem ter o **mesmo comprimento**. Se `level_page` vier curto ou vazio, o backend completa com `none` (padrão).
- Envie `filename_out` com sufixo `.pdf`; se faltar, o backend adiciona.
- Não há persistência: **RAM + TTL** (configurável via env).

