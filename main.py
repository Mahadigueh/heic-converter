from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
import zipfile
from typing import List
from PIL import Image
from pillow_heif import register_heif_opener, open_heif

register_heif_opener()

app = FastAPI(title="replygen.ca")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/convert-heic")
async def convert_heic(files: List[UploadFile] = File(...), format: str = "png"):
    if not files:
        raise HTTPException(400, detail="Aucun fichier")

    converted = []
    for file in files:
        content = await file.read()
        heif = open_heif(content)
        img = heif.to_pillow()
        converted.append(img)

    if len(converted) > 1:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            for i, img in enumerate(converted):
                buf = io.BytesIO()
                img.save(buf, format=format.upper(), quality=95)
                z.writestr(f"image_{i+1}.{format}", buf.getvalue())
        zip_buffer.seek(0)
        return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=converted.zip"})
    else:
        buf = io.BytesIO()
        converted[0].save(buf, format=format.upper(), quality=95)
        buf.seek(0)
        return StreamingResponse(buf, media_type=f"image/{format}", headers={"Content-Disposition": f"attachment; filename=converted.{format}"})

@app.get("/health")
async def health():
    return {"status": "ok"}