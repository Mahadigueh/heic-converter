from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
import zipfile
from typing import List
from PIL import Image
from pillow_heif import register_heif_opener, open_heif
import fitz  # PyMuPDF
from docx import Document

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
    if not files:
        raise HTTPException(400, detail="Aucun fichier envoyé")

    converted_images = []
    for file in files:
        content = await file.read()
        heif_file = open_heif(content)
        img = heif_file.to_pillow()
        converted_images.append(img)

    if len(converted_images) > 1:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, img in enumerate(converted_images):
                buf = io.BytesIO()
                img.save(buf, format=format.upper(), quality=95)
                zip_file.writestr(f"image_{i+1}.{format}", buf.getvalue())
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=heic_converted.zip"}
        )
    else:
        buf = io.BytesIO()
        converted_images[0].save(buf, format=format.upper(), quality=95)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type=f"image/{format}",
            headers={"Content-Disposition": f"attachment; filename=converted.{format}"}
        )

# ==================== FUSION PDF (avec fitz - plus stable) ====================
@app.post("/merge-pdf")
async def merge_pdf(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, detail="Minimum 2 fichiers PDF requis")

    merger = fitz.open()
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        merger.insert_pdf(doc)
        doc.close()

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
