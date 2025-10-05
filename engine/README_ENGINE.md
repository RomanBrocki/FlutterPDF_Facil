# 🧠 Engine — PDF Fácil

A **engine** é o núcleo de processamento do PDF Fácil.  
Aqui estão todas as funções responsáveis por **compressão, união, rotação, split e estimativas de tamanho**.  
Ela é usada pela API (`api/main.py`), mas é totalmente independente — pode ser chamada isoladamente em outros projetos.

---

## 📁 Estrutura

```
engine/
├─ engine_config.py  # Define níveis de compressão (none|min|med|max)
└─ pdf_ops.py        # Implementa o motor principal
```

---

## ⚙️ engine_config.py

Define os quatro níveis de compressão usados no app:

| Nível | Modo | Descrição | DPI | JPEG Q |
|-------|------|------------|-----|---------|
| `none` | none | sem compressão | — | — |
| `min`  | smart | rasteriza apenas páginas imagem-only | 200 | 85 |
| `med`  | all | rasteriza todas as páginas | 150 | 70 |
| `max`  | all | rasteriza todas com máxima compressão | 110 | 50 |

Esses valores são lidos pelo motor (`pdf_ops.py`) e aplicados automaticamente.

---

## ⚙️ pdf_ops.py — funções principais

| Função | Descrição |
|---------|------------|
| `estimate_pdf_size()` | Estima o tamanho total de um PDF após compressão |
| `estimate_pdf_page_size()` | Estima o tamanho de uma única página |
| `estimate_image_pdf_size()` | Calcula o tamanho do PDF gerado a partir de uma imagem |
| `compress_pdf()` | Aplica compressão real em um PDF completo |
| `image_to_pdf_bytes()` | Converte JPG/PNG em PDF de 1 página |
| `merge_items()` | Junta PDFs e imagens em um único arquivo final |
| `merge_pages()` | Junta páginas individuais respeitando rotação e níveis |
| `split_pdf()` | Gera novo PDF contendo apenas páginas selecionadas |

---

## 🧠 Lógica de compressão

A engine usa **PyMuPDF (fitz)** para rasterizar páginas e **img2pdf** para remontar o resultado.  
Ela inclui **guard-rails**: se o PDF comprimido ficar maior que o original, mantém o original.

```python
if len(out_bytes) < len(pdf_bytes):
    return out_bytes
else:
    return pdf_bytes
```

---

## 🔍 Exemplo de uso direto

```python
from engine.pdf_ops import merge_items, compress_pdf

# Compressão simples
with open("arquivo.pdf","rb") as f:
    original = f.read()

comprimido = compress_pdf(original, "med")

# Salvando resultado
with open("saida.pdf","wb") as f:
    f.write(comprimido)
```

---

## 📚 Tecnologias usadas

- **PyMuPDF (fitz)** — leitura e renderização de PDFs  
- **Pillow (PIL)** — manipulação e conversão de imagens  
- **img2pdf** — montagem final de PDFs  
- **pypdf** — manipulação e merge de páginas

---

## 🔗 Integração com API

A API chama funções da engine como:

```python
from engine.pdf_ops import estimate_pdf_page_size, estimate_image_pdf_size, merge_pages
```

Essas funções recebem apenas bytes e metadados simples, o que torna a engine **independente do FastAPI**.

---

## 👨‍💻 Autor

Desenvolvido por **Roman Brocki**  
Código modular, independente e reutilizável.
