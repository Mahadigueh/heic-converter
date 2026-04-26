from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
from PIL import Image
from pillow_heif import register_heif_opener, open_heif
import os
import zipfile
from datetime import datetime
from typing import List
import fitz  # PyMuPDF
from docx import Document
from pypdf import PdfMerger, PdfReader, PdfWriter

register_heif_opener()

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

# ==================== HEIC ====================
@app.post("/convert-heic")
async def convert_heic(files: List[UploadFile] = File(...), format: str = "png"):
    # ... (ton code HEIC précédent, je peux le remettre si besoin)
    pass  # Je te le remettrai complet si tu veux

# ==================== FUSION PDF ====================
@app.post("/merge-pdf")
async def merge_pdf(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, detail="Vous devez envoyer au moins 2 fichiers PDF")

    merger = PdfMerger()
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        content = await file.read()
        merger.append(io.BytesIO(content))

    output = io.BytesIO()
    merger.write(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="merged_document.pdf"'}
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