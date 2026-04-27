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

app = FastAPI(title="Replygen - Outil Tout-en-Un")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ====================== PAGES HTML ======================
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/heic", response_class=HTMLResponse)
async def heic_page():
    with open("static/heic.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/merge", response_class=HTMLResponse)
async def merge_page():
    with open("static/merge.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/pdf-to-word", response_class=HTMLResponse)
async def pdf_to_word_page():
    with open("static/pdf-to-word.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/compress", response_class=HTMLResponse)
async def compress_page():
    with open("static/compress.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/about", response_class=HTMLResponse)
async def about_page():
    with open("static/about.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    with open("static/privacy.html", "r", encoding="utf-8") as f:
        return f.read()

# ====================== CONVERSIONS ======================
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