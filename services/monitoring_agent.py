from dataclasses import dataclass
from collections import Counter

from services.config import AGENT_EVENT_LIMIT
from services.event_repository import list_events

# ─── Perfil do agente ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AgentProfile:
    name: str
    role: str
    goal: str


AGENT_PROFILE = AgentProfile(
    name="Agente AgroVision",
    role="triagem operacional de eventos",
    goal="Analisar detecções recentes, explicar riscos e sugerir a próxima ação.",
)

MAX_HISTORY_MESSAGES = 8

# ─── System prompt ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    f"Você é o {AGENT_PROFILE.name}, um agente de {AGENT_PROFILE.role}. "
    f"Objetivo: {AGENT_PROFILE.goal} "
    "Trate os dados como monitoramento operacional autorizado de ambiente real. "
    "Responda em português do Brasil, de forma direta e útil. "
    "Use os eventos fornecidos como fonte principal. "
    "Não invente dados que não aparecem no contexto. "
    "Não tente identificar pessoas; fale apenas sobre eventos, riscos e próximas ações. "
    "Quando fizer sentido, organize a resposta em: Leitura, Risco e Recomendação."
)

# ─── Construção do contexto ───────────────────────────────────────────────────

def build_event_context(events: list[dict]) -> str:
    """
    Transforma a lista de eventos em um resumo operacional legível
    para ser enviado ao modelo como contexto.
    """
    if not events:
        return "Contexto operacional: nenhum evento registrado até o momento."

    labels = [e["label"] for e in events]
    distribution = Counter(labels)
    most_recent = events[0]
    confidences = [e["confidence"] for e in events if e.get("confidence")]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    lines = [
        "Contexto operacional para o agente:",
        f"- Eventos considerados: {len(events)}",
        f"- Evento mais recente: {most_recent['label']} em {most_recent['event_time']}",
        f"- Distribuição recente: {', '.join(f'{k}: {v}' for k, v in distribution.most_common())}",
        f"- Confiança média: {avg_conf:.2f}",
        "",
        "Eventos recentes:",
    ]

    for e in events:
        lines.append(
            f"  - #{e['id']} | {e['event_time']} | {e['label']} | conf={e['confidence']:.2f}"
        )

    return "\n".join(lines)


# ─── Normalização do histórico ────────────────────────────────────────────────

def normalize_history(history: list[dict]) -> list[dict]:
    """
    Filtra e limita as mensagens do histórico ao que faz sentido enviar ao modelo.
    Mantém apenas mensagens com role 'user' ou 'assistant'.
    """
    valid = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content", "").strip()
    ]
    return valid[-MAX_HISTORY_MESSAGES:]



def build_agent_messages(question: str, history: list[dict]) -> list[dict]:
    """
    Monta a sequência completa de mensagens que será enviada ao Ollama:
    1. System prompt com identidade e regras do agente
    2. Contexto operacional dos eventos recentes
    3. Histórico recente da conversa
    4. Pergunta atual do usuário
    """
    events = list_events(AGENT_EVENT_LIMIT)
    event_context = build_event_context(events)

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "system", "content": event_context},
        *normalize_history(history),
        {"role": "user", "content": question},
    ]



def get_agent_status() -> dict:
    """Retorna informações de inspeção do agente para a rota /agent/status."""
    events = list_events(AGENT_EVENT_LIMIT)
    context_preview = build_event_context(events)

    return {
        "name": AGENT_PROFILE.name,
        "role": AGENT_PROFILE.role,
        "goal": AGENT_PROFILE.goal,
        "events_in_context": len(events),
        "max_history_messages": MAX_HISTORY_MESSAGES,
        "context_preview": context_preview,
    }
