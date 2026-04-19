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
import concurrent.futures
import asyncio

register_heif_opener()

app = FastAPI(title="Convertisseur HEIC → PNG/JPG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

def convert_single_file(file_content: bytes, filename: str, output_format: str):
    try:
        heif_file = open_heif(io.BytesIO(file_content), convert_hdr_to_8bit=True)
        image = heif_file.to_pillow()
        output = io.BytesIO()
        
        if output_format.lower() == "jpg":
            image = image.convert("RGB")
            image.save(output, format="JPEG", quality=85, optimize=True)
            ext = "jpg"
            media_type = "image/jpeg"
        else:
            image.save(output, format="PNG", optimize=False, compress_level=4)
            ext = "png"
            media_type = "image/png"
        
        output.seek(0)
        original_name = os.path.splitext(filename)[0]
        new_filename = f"{original_name}_converted.{ext}"
        return (new_filename, output.getvalue(), media_type)
    except Exception:
        return None

@app.post("/convert")
async def convert_heic(files: List[UploadFile] = File(...), format: str = "png"):
    if len(files) > 5:
        raise HTTPException(400, detail="Maximum 5 fichiers à la fois.")

    file_data = []
    for file in files:
        if file.filename.lower().endswith(('.heic', '.heif')):
            content = await file.read()
            file_data.append((content, file.filename))

    if not file_data:
        raise HTTPException(400, detail="Aucun fichier HEIC valide.")

    converted_files = []
    loop = asyncio.get_running_loop()
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(len(file_data), os.cpu_count() or 4)) as executor:
        futures = [loop.run_in_executor(executor, convert_single_file, content, filename, format) for content, filename in file_data]
        results = await asyncio.gather(*futures)

    converted_files = [r for r in results if r]

    if not converted_files:
        raise HTTPException(500, detail="Échec de la conversion.")

    if len(converted_files) == 1:
        filename, data, media_type = converted_files[0]
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for filename, data, _ in converted_files:
            z.writestr(filename, data)
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="heic_converted_files.zip"'}
    )