# 📄 PDF Fácil — Web App + API

**PDF Fácil** é uma ferramenta gratuita e aberta que permite **unir, comprimir e organizar PDFs e imagens (JPG/PNG)** diretamente no navegador — sem instalar nada.  
Tudo é feito **em memória**, com total privacidade: os arquivos expiram automaticamente após alguns minutos.

---

## 🌐 Acesse agora

- 🔗 **App Web:** [https://romanbrocki.github.io/PDF_Facil_API/](https://romanbrocki.github.io/PDF_Facil_API/)  
- ⚙️ **Backend (API):** [https://pdf-facil.onrender.com](https://pdf-facil.onrender.com)

---

## 🧩 Arquitetura

O sistema é dividido em duas partes independentes:

| Camada | Hospedagem | Função |
|---------|-------------|--------|
| **Frontend** (`index.html`) | GitHub Pages | Interface em HTML + JavaScript puro. Envia os arquivos e baixa o PDF final. |
| **Backend** (`api/`) | Render | API em FastAPI responsável por compressão, merge e geração do PDF. |

---

## ⚙️ Estrutura do repositório

```
PDF_Facil_API/
├─ api/
│  ├─ main.py          # Endpoints principais (preview, estimate, process, download)
│  ├─ storage.py       # Sessões temporárias em RAM com TTL
│  ├─ thumbs.py        # Miniaturas de PDFs e imagens
│  ├─ schemas.py       # Modelos de entrada/saída (Pydantic)
│  └─ jobs.py          # PDFs finais armazenados até o download (one-time)
├─ engine/
│  ├─ engine_config.py # Presets de compressão (none|min|med|max)
│  └─ pdf_ops.py       # Motor principal de compressão, merge e estimativas
├─ index.html          # Interface web
├─ requirements.txt    # Dependências Python
├─ runtime.txt         # Versão Python (Render usa python-3.11.9)
└─ README_API.md / README_ENGINE.md  # Documentação modular
```

---

## 🚀 Fluxo completo

```text
1. Usuário envia arquivos → /preview
2. API gera miniaturas e devolve token
3. Usuário define ordem, rotação e compressão
4. App envia → /estimate (opcional)
5. API estima tamanho e mostra redução
6. App envia → /process
7. API gera PDF e retorna link temporário
8. Usuário baixa → /download/one-time/{job_id}
```

- O **token** identifica a sessão temporária.  
- O **job_id** identifica o PDF final (válido apenas até o download).

---

## 📦 Níveis de compressão

| Nível | Modo | Efeito | Uso indicado |
|-------|-------|--------|---------------|
| **none** | — | sem compressão | preservar qualidade máxima |
| **min** | smart | rasteriza só páginas imagem-only | documentos leves |
| **med** | all | rasteriza todas as páginas (DPI 150, JPEG 70) | PDFs pesados |
| **max** | all | rasteriza tudo (DPI 110, JPEG 50) | reduzir ao mínimo possível |

Guard-rails garantem que **nunca se aumente o tamanho**:  
se o resultado for maior que o original, o backend mantém o arquivo original.

---

## 💻 Execução local

1️⃣ **Instalar dependências**
```bash
pip install -r requirements.txt
```

2️⃣ **Rodar localmente**
```bash
uvicorn api.main:app --reload --port 8765
```

3️⃣ **Abrir a interface**
```text
http://127.0.0.1:5500/index.html?api=http://127.0.0.1:8765
```
*(basta rodar também um `python -m http.server 5500` na pasta raiz)*

4️⃣ **Testar endpoints**
Acesse [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs)

---

## 🔧 Variáveis de ambiente (Render)

| Variável | Descrição | Padrão |
|-----------|------------|--------|
| `FILE_MAX_MB` | Tamanho máximo por arquivo | 50 |
| `BATCH_MAX_MB` | Limite total por upload | 75 |
| `TTL_MINUTES` | Tempo de vida das sessões | 15 |
| `CORS_ALLOW_ORIGINS` | Domínios permitidos | `*` |

Exemplo:
```env
FILE_MAX_MB=50
BATCH_MAX_MB=75
TTL_MINUTES=15
CORS_ALLOW_ORIGINS=https://romanbrocki.github.io,https://romanbrocki.github.io/PDF_Facil_API/
```

---

## 🧠 Tecnologias utilizadas

| Tipo | Biblioteca |
|------|-------------|
| Backend | FastAPI, Uvicorn |
| PDFs e imagens | PyMuPDF, Pillow, img2pdf, pypdf |
| Frontend | HTML + JavaScript |
| Hospedagem | Render + GitHub Pages |

---

## 🔒 Privacidade

- Nenhum arquivo é salvo no servidor.  
- Tudo é mantido apenas **em memória RAM**.  
- O link de download é **válido uma única vez**.  
- Sessões e arquivos expiram após `TTL_MINUTES` (padrão: 15).

---

## 🧩 Documentações complementares

- [README_API.md](api/README_API.md) — Detalhes técnicos da API  
- [README_ENGINE.md](engine/README_ENGINE.md) — Lógica interna e compressão  
- [index.html](index.html) — Frontend pronto para deploy  

---

## 👨‍💻 Autor

Desenvolvido por **Roman Brocki**  
Backend em Python • Frontend em HTML/JS  
Hospedagem gratuita no **Render** e **GitHub Pages**

---

## 📜 Licenças

Este projeto utiliza bibliotecas open source sob licenças permissivas.

- **PyMuPDF (AGPL-3.0)** — © Artifex Software, Inc.  
  Uso permitido em software aberto; este projeto mantém código-fonte público conforme a AGPL.  
- **Demais bibliotecas** (FastAPI, Pillow, Pydantic, Uvicorn etc.) — MIT/BSD/Apache-2.0, livres para uso interno e comercial.

O código-fonte completo está disponível em  
➡️ [https://github.com/RomanBrocki/PDF_Facil_API](https://github.com/RomanBrocki/PDF_Facil_API)

---

## 🧾 Versões e compatibilidade

| Componente | Versão mínima |
|-------------|----------------|
| Python | 3.11.9 |
| Pillow | 10+ |
| PyMuPDF | 1.24+ |
| FastAPI | 0.110+ |
| Uvicorn | 0.29+ |

---

**PDF Fácil — simples, rápido e seguro.**
