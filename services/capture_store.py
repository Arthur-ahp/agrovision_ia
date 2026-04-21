import os
from services.config import SAVE_DIR


def list_captures(limit: int = 20) -> list[str]:
    """
    Retorna os caminhos públicos das capturas mais recentes,
    ordenadas da mais nova para a mais antiga.
    """
    if not os.path.isdir(SAVE_DIR):
        return []

    files = [
        f for f in os.listdir(SAVE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    files.sort(reverse=True)

    return [f"/static/captures/{f}" for f in files[:limit]]
