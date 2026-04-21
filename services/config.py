import os
from dotenv import load_dotenv

load_dotenv()

# --- Ollama ---
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# --- Agente ---
AGENT_EVENT_LIMIT: int = int(os.getenv("AGENT_EVENT_LIMIT", "12"))

# --- Câmera ---
CAMERA_SOURCE: str | int = os.getenv("CAMERA_SOURCE", "0")
if CAMERA_SOURCE == "0":
    CAMERA_SOURCE = 0  # webcam local
CAMERA_RECONNECT_SECONDS: int = int(os.getenv("CAMERA_RECONNECT_SECONDS", "5"))

# --- YOLO ---
MODEL_PATH: str = os.getenv("MODEL_PATH", "yolov8n.pt")
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
MIN_CONSECUTIVE_FRAMES: int = int(os.getenv("MIN_CONSECUTIVE_FRAMES", "3"))
ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "20"))

TARGET_CLASSES: set[str] = set(
    os.getenv("TARGET_CLASSES", "person,car,truck,bus,motorcycle").split(",")
)

# --- Persistência ---
DB_PATH: str = os.getenv("DB_PATH", "detections.db")
SAVE_DIR: str = os.getenv("SAVE_DIR", "static/captures")
