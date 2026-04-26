from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
from typing import List
import fitz  # PyMuPDF
from docx import Document
from pypdf import PdfReader, PdfWriter  # On enlève PdfMerger temporairement

# Pour la fusion, on utilise fitz (plus stable)
def merge_pdfs_with_fitz(files):
    merger = fitz.open()
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        content = file.file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        merger.insert_pdf(doc)
        doc.close()
    return merger

app = FastAPI(title="Outil Tout-en-Un - replygen.ca")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# ==================== FUSION PDF (avec fitz) ====================
@app.post("/merge-pdf")
async def merge_pdf(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, detail="Vous devez envoyer au moins 2 fichiers PDF")

    merger = merge_pdfs_with_fitz(files)
    output = io.BytesIO()
    merger.save(output)
    merger.close()
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="document_fusionne.pdf"'}
    )

# ==================== PDF TO WORD ====================
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, detail="Le fichier doit être un PDF")

    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    word_doc = Document()

    for page in doc:
        text = page.get_text()
        word_doc.add_paragraph(text)

    output = io.BytesIO()
    word_doc.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{file.filename.replace(".pdf", "")}.docx"'}
    )

# ==================== COMPRESS PDF ====================
@app.post("/compress-pdf")
async def compress_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, detail="Le fichier doit être un PDF")

    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")

    output = io.BytesIO()
    doc.save(output, garbage=4, deflate=True, clean=True)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="compressed_{file.filename}"'}
    )

@app.get("/health")
async def health():
    return {"status": "ok"}