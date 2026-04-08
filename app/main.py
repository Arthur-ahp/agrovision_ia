from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os

app = FastAPI(title="AgroVision")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"mensagem": "AgroVision está rodando com sucesso!"}
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload_imagem(request: Request, file: UploadFile = File(...)):
    caminho_arquivo = os.path.join(UPLOAD_DIR, file.filename)
    with open(caminho_arquivo, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"mensagem": f"Imagem enviada com sucesso: {file.filename}"}
    )