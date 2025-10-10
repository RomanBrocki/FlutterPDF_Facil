# 📄 PDF Fácil — API + Web App

**PDF Fácil** é uma ferramenta gratuita que permite **unir, comprimir e organizar arquivos PDF e imagens (JPG/PNG)** diretamente do navegador.  
Nenhum dado é salvo: tudo acontece **em memória**, e os arquivos são apagados automaticamente após alguns minutos.

---

## 🌍 Site oficial

🔗 **Acesse o app web:**  
👉 [https://romanbrocki.github.io/PDF_Facil_API/](https://romanbrocki.github.io/PDF_Facil_API/)

O site se comunica com o backend hospedado no Render:  
🔧 [https://pdf-facil.onrender.com](https://pdf-facil.onrender.com)

---

## 🧩 Como o sistema funciona

O projeto é dividido em duas partes:

| Parte | Hospedagem | Descrição |
|-------|-------------|------------|
| **Frontend (index.html)** | GitHub Pages | Interface web feita em HTML + JavaScript. Envia arquivos e recebe o PDF pronto. |
| **Backend (FastAPI)** | Render | API em Python que faz o trabalho pesado (compressão, merge e geração do arquivo final). |

---

## ⚙️ Estrutura do Projeto

```
PDF_Facil_API/
├─ api/
│  ├─ main.py          # Endpoints e lógica principal
│  ├─ storage.py       # Sessões em memória (RAM + tempo de vida)
│  ├─ thumbs.py        # Geração de miniaturas
│  ├─ schemas.py       # Modelos de entrada/saída
│  └─ jobs.py          # Geração e exclusão dos PDFs finais
├─ engine/
│  ├─ engine_config.py # Presets de compressão
│  └─ pdf_ops.py       # Funções de compressão, união e rotação
├─ index.html          # Interface Web
├─ requirements.txt    # Dependências Python
├─ runtime.txt         # Versão Python usada no Render
└─ DOCS.md             # Documentação técnica complementar
```

---

## 🚀 Fluxo completo

```text
1. Usuário envia arquivos → /preview
2. API gera miniaturas e devolve token
3. Usuário define ordem, rotação e compressão
4. App envia tudo → /estimate (opcional)
5. API estima tamanho final e mostra redução
6. App envia → /process
7. API gera PDF e devolve link temporário
8. Usuário baixa o arquivo → /download/one-time/{job_id}
```

O **token** identifica temporariamente a sessão (fica em memória).  
O **job_id** identifica o PDF final (também em memória, até o download).

---

## 📦 Níveis de compressão

| Nível | Efeito | Uso indicado |
|-------|---------|---------------|
| **none** | sem compressão | preservar qualidade máxima |
| **min** | leve compressão (rasteriza só imagens) | documentos mistos |
| **med** | compressão moderada (rasteriza tudo) | PDFs pesados |
| **max** | compressão máxima | reduzir ao mínimo possível |

---

## 🧪 Exemplos de uso da API

### 🔹 Upload e preview
```bash
curl -X POST -F "files=@documento.pdf" https://pdf-facil.onrender.com/preview
```

Retorno (resumo):
```json
{
  "token": "abc123",
  "page_count_total": 12,
  "items": [
    {"src_id":0,"page_index":0,"is_pdf":true,"thumb_b64":"data:image/jpeg;base64,..."} 
  ]
}
```

### 🔹 Estimar tamanho
```bash
curl -X POST https://pdf-facil.onrender.com/estimate      -H "Content-Type: application/json"      -d '{
          "token":"abc123",
          "order":[{"src_id":0,"page_index":0}],
          "keep":[true],
          "rotate":[0],
          "level_page":["med"]
         }'
```

### 🔹 Gerar PDF final
```bash
curl -X POST https://pdf-facil.onrender.com/process      -H "Content-Type: application/json"      -d '{
          "token":"abc123",
          "order":[{"src_id":0,"page_index":0}],
          "keep":[true],
          "rotate":[0],
          "level_page":["med"],
          "filename_out":"resultado.pdf"
         }'
```

Resposta:
```json
{
  "download_url": "/download/one-time/xyz789",
  "filename": "resultado.pdf"
}
```

---

### 🔸 Exemplo JavaScript (`fetch`)
```js
const payload = { token, order, keep, rotate, level_page, filename_out: "meu_arquivo.pdf" };

const res = await fetch("https://pdf-facil.onrender.com/process", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
});

const data = await res.json();
window.location.href = "https://pdf-facil.onrender.com" + data.download_url;
```

---

## ⚠️ Erros comuns

| Mensagem | Causa | Solução |
|-----------|--------|---------|
| **Sessão expirada (404)** | Passaram mais de 15 minutos sem uso | Refazer upload e gerar novo token |
| **job não encontrado/expirado** | O PDF já foi baixado ou o TTL expirou | Gerar novamente |
| **Arquivo excede X MB** | Tamanho maior que permitido por `FILE_MAX_MB` | Enviar arquivo menor ou aumentar variável no backend |
| **CORS error (bloqueio no navegador)** | Domínio do frontend não está autorizado | Adicionar domínio em `CORS_ALLOW_ORIGINS` |

---

## 🔧 Configuração do backend (Render)

```env
FILE_MAX_MB=50
BATCH_MAX_MB=75
TTL_MINUTES=15
CORS_ALLOW_ORIGINS=https://romanbrocki.github.io,https://romanbrocki.github.io/PDF_Facil_API/
```

Comando de inicialização:
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

---

## 💻 Execução local

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Acesse: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧠 Tecnologias utilizadas

| Componente | Biblioteca |
|-------------|-------------|
| Backend | FastAPI, Uvicorn |
| PDF | PyMuPDF, Pillow, img2pdf, pypdf |
| Frontend | HTML + JavaScript puro |
| Hospedagem | Render + GitHub Pages |

---

## 🔒 Segurança e privacidade

- Nenhum arquivo é salvo no servidor.  
- Tudo é mantido **em memória temporária**.  
- Os links de download são válidos **uma única vez**.  
- As sessões e arquivos expiram automaticamente após o tempo configurado (`TTL_MINUTES`, padrão 15).  

---

## 🔗 Links oficiais

- 🌐 **App Web:** [https://romanbrocki.github.io/PDF_Facil_API/](https://romanbrocki.github.io/PDF_Facil_API/)  
- ⚙️ **Backend:** [https://pdf-facil.onrender.com](https://pdf-facil.onrender.com)  
- 💻 **Repositório:** [https://github.com/RomanBrocki/PDF_Facil_API](https://github.com/RomanBrocki/PDF_Facil_API)  
- 🧱 **Versão antiga (Streamlit):** [https://pdf-facil.streamlit.app](https://pdf-facil.streamlit.app)

---

## 👨‍💻 Autor

Desenvolvido por **Roman Brocki**  
Backend em Python • Frontend em HTML/JS  
Hospedagem gratuita no **Render** e **GitHub Pages**


---

## Licenças e Créditos

Este projeto utiliza bibliotecas open source sob licenças permissivas.  
Em especial, inclui o **PyMuPDF**, distribuído sob licença **AGPL-3.0**.

- **PyMuPDF (AGPL-3.0)** — © Artifex Software, Inc.  
  Uso permitido em software aberto; este projeto mantém seu código-fonte público conforme os termos da AGPL.  
- **Demais bibliotecas** (FastAPI, Pillow, Pydantic, Uvicorn, etc.) — sob licenças MIT, BSD ou Apache 2.0, livres para uso comercial.

O código-fonte completo deste projeto está disponível publicamente, cumprindo todas as exigências de licenciamento.
