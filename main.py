from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
import zipfile
from typing import List
from PIL import Image
from pillow_heif import register_heif_opener, open_heif
import fitz
from docx import Document

register_heif_opener()

app = FastAPI(title="replygen.ca")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Pages HTML avec URLs propres
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

# ==================== HEIC ====================
@app.post("/convert-heic")
async def convert_heic(files: List[UploadFile] = File(...), format: str = "png"):
    # (ton code HEIC actuel)
    if not files:
        raise HTTPException(400, detail="Aucun fichier envoyé")
    # ... (le reste de ton code HEIC)
    pass  # Remplace par ton code HEIC complet si besoin

# ==================== Autres endpoints (déjà existants) ====================
@app.post("/merge-pdf")
async def merge_pdf(files: List[UploadFile] = File(...)):
    # ton code actuel
    pass

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    # ton code actuel
    pass

@app.post("/compress-pdf")
async def compress_pdf(file: UploadFile = File(...)):
    # ton code actuel
    pass

@app.get("/health")
async def health():
    return {"status": "ok"}