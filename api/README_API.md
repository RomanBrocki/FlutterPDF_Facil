# ⚙️ API — PDF Fácil

A **API do PDF Fácil** é o coração do sistema: recebe arquivos, gera miniaturas, estima compressão, cria o PDF final e oferece o download único (one-time).  
Desenvolvida em **FastAPI**, opera 100% em **memória RAM** com tempo de vida limitado (TTL).

---

## 📁 Estrutura

```
api/
├─ main.py      # Endpoints principais e fluxo completo da API
├─ storage.py   # Gerenciamento de sessões temporárias
├─ thumbs.py    # Geração de miniaturas (PDF/Imagens)
├─ schemas.py   # Modelos de entrada e saída (Pydantic)
└─ jobs.py      # Armazenamento dos PDFs finais (one-time)
```

---

## 🌐 Endpoints Principais

| Método | Rota | Descrição |
|--------|------|------------|
| **GET** | `/health` | Verifica se o backend está online |
| **POST** | `/preview` | Recebe arquivos e gera miniaturas com token |
| **POST** | `/estimate` | Calcula tamanho antes/depois de compressão |
| **POST** | `/process` | Gera o PDF final e retorna URL temporária |
| **GET** | `/download/one-time/{job_id}` | Baixa o PDF e o apaga da memória |

---

## 🔹 Fluxo resumido

```text
upload → preview (gera token)
        ↓
  estimate (opcional)
        ↓
  process (gera PDF)
        ↓
  download (one-time)
```

---

## 🧱 Schemas (modelos de entrada)

### EstimateIn
```python
class EstimateIn(BaseModel):
    token: str
    order: List[OrderItem]
    keep:  List[bool]
    rotate: List[int]
    level_page: List[str]
    level_global: Optional[str] = None
```

### ProcessIn (herda de EstimateIn)
```python
class ProcessIn(EstimateIn):
    filename_out: Optional[str] = None
```

**Campos importantes:**
- `order`: ordem das páginas (com `src_id` e `page_index`)
- `keep`: define quais páginas serão mantidas
- `rotate`: ângulo de rotação (0, 90, 180, 270)
- `level_page`: compressão individual por página
- `level_global`: compressão global (sobrescreve `level_page`)
- `filename_out`: nome do arquivo final (opcional)

---

## 🔧 Sessões e Jobs

| Componente | Arquivo | Função |
|-------------|----------|---------|
| Sessões | `storage.py` | Guarda arquivos e miniaturas, expira por TTL |
| Jobs | `jobs.py` | Guarda PDFs prontos até o download |

Ambos são armazenados em **dicionários de memória** e limpos automaticamente por tempo de vida (`TTL_MINUTES`).

---

## 🧪 Exemplo de fluxo completo

```bash
# 1. Upload e preview
curl -X POST -F "files=@arquivo.pdf" https://pdf-facil.onrender.com/preview

# 2. Estimativa
curl -X POST https://pdf-facil.onrender.com/estimate      -H "Content-Type: application/json"      -d '{
          "token":"abc123",
          "order":[{"src_id":0,"page_index":0}],
          "keep":[true],
          "rotate":[0],
          "level_page":["med"]
         }'

# 3. Processamento
curl -X POST https://pdf-facil.onrender.com/process      -H "Content-Type: application/json"      -d '{
          "token":"abc123",
          "order":[{"src_id":0,"page_index":0}],
          "keep":[true],
          "rotate":[0],
          "level_page":["med"],
          "filename_out":"resultado.pdf"
         }'
```

---

## 🧩 Configurações via variáveis de ambiente

| Variável | Descrição | Padrão |
|-----------|------------|--------|
| `FILE_MAX_MB` | Tamanho máximo por arquivo | 50 |
| `BATCH_MAX_MB` | Tamanho máximo do lote de upload | 75 |
| `TTL_MINUTES` | Tempo de vida das sessões e jobs | 15 |
| `CORS_ALLOW_ORIGINS` | Domínios permitidos para frontend | `*` |

---

## ⚠️ Observações importantes

- Se `level_page` for menor que o número de páginas, o backend completa com `"none"` automaticamente.  
- Se `level_global` for informado, ele sobrescreve todos os níveis individuais.  
- O arquivo final **sempre termina em `.pdf`** (o backend adiciona se faltar).  
- Após o download, o PDF é removido da RAM (one-time).

---

## 👨‍💻 Tecnologias

- **FastAPI** — framework backend
- **Pydantic** — validação de dados
- **PyMuPDF**, **Pillow**, **img2pdf** — manipulação de PDFs e imagens
- **Uvicorn** — servidor ASGI

---

## 🔗 Links úteis

- 🌐 App Web: [https://romanbrocki.github.io/PDF_Facil_API/](https://romanbrocki.github.io/PDF_Facil_API/)  
- ⚙️ API online: [https://pdf-facil.onrender.com](https://pdf-facil.onrender.com)
