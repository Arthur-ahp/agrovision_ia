import os
import cv2
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.config import SAVE_DIR
from services.event_repository import init_db, list_events, count_events
from services.capture_store import list_captures
from services.video_monitor import process_stream, get_last_frame, get_camera_status, generate_mjpeg
from services.monitoring_agent import build_agent_messages, get_agent_status
from services.ollama_client import chat_stream, warmup, is_available
from services.schemas import ChatRequest

@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs(SAVE_DIR, exist_ok=True)

    
    thread = threading.Thread(target=process_stream, daemon=True)
    thread.start()

    
    threading.Thread(target=warmup, daemon=True).start()

    yield

app = FastAPI(title="AgroVision AI", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    events = list_events(20)
    captures = list_captures(12)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"events": events, "captures": captures},
    )

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AgroVision AI",
        "total_events": count_events(),
    }


@app.get("/camera/status")
def camera_status():
    return JSONResponse(content=get_camera_status())


@app.get("/agent/status")
def agent_status():
    return JSONResponse(content=get_agent_status())


@app.get("/events")
def get_events():
    return JSONResponse(content=list_events(50))


@app.get("/frame")
def get_frame():
    frame = get_last_frame()
    if frame is None:
        return JSONResponse(
            content={"message": "Ainda sem frame disponível."},
            status_code=503,
        )
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return JSONResponse(
            content={"message": "Erro ao converter frame."},
            status_code=500,
        )
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@app.get("/video_feed")
def video_feed():
    """Stream MJPEG consumido pelo dashboard via <img src='/video_feed'>."""
    return StreamingResponse(
        generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@app.post("/chat")
def chat(body: ChatRequest):
    """
    Recebe uma pergunta e o histórico, monta o contexto do agente
    e retorna a resposta do Ollama em streaming (text/plain).
    """
    if not is_available():
        return JSONResponse(
            content={"error": "Ollama não está disponível. Verifique se o serviço está rodando."},
            status_code=503,
        )

    history = [{"role": m.role, "content": m.content} for m in body.history]
    messages = build_agent_messages(body.question, history)

    def stream():
        for chunk in chat_stream(messages):
            yield chunk

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")
