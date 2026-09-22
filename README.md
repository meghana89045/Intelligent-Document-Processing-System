# AI-Powered Multi-Document Intelligence and Information Retrieval System

## 50–60% Working MVP

Implemented pipeline:
Upload multiple documents -> preprocessing -> OCR/text extraction -> document classification -> information extraction -> validation -> SQLite storage -> metadata/full-text search -> dashboard/export.

Supported: PDF, PNG, JPG/JPEG.

Document types: Invoice, Receipt, Purchase Order, Contract, KYC, Form, Unknown.

## Run

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

For scanned images/PDFs install Tesseract OCR and put `tesseract` on PATH. Text PDFs work without Tesseract.

## Remaining 40–50%
- Transformer/LLM classification
- Layout-aware extraction
- Embeddings/vector search
- Semantic search
- RAG / Ask Your Documents
- Authentication and organization isolation
- Advanced duplicate/anomaly detection
- Cloud/API/ERP integrations
