import json
import httpx
from typing import Generator

from services.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE


def chat_stream(messages: list[dict]) -> Generator[str, None, None]:
    """
    Envia mensagens ao Ollama e retorna um gerador de chunks de texto (streaming).
    Cada chunk é uma string parcial da resposta do modelo.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }

    with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
        with client.stream("POST", OLLAMA_URL, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


def warmup() -> bool:
    """
    Faz uma chamada simples ao Ollama para garantir que o modelo está carregado.
    Retorna True se bem-sucedido.
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": "ok"}],
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
        print(f"[Ollama] Warmup concluído. Modelo: {OLLAMA_MODEL}")
        return True
    except Exception as e:
        print(f"[Ollama] Warmup falhou: {e}")
        return False


def is_available() -> bool:
    """Verifica se o servidor Ollama está respondendo."""
    try:
        base_url = OLLAMA_URL.replace("/api/chat", "")
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
