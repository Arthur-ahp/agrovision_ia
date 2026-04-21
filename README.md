# AgroVision AI

Sistema de monitoramento com visão computacional e agente de linguagem local.

## O que o sistema faz

1. Lê uma câmera local ou stream público/autorizado
2. Detecta objetos com YOLO (person, car, truck, bus, motorcycle)
3. Salva eventos com label, confiança, horário e imagem no SQLite
4. Exibe monitoramento ao vivo no dashboard
5. Responde perguntas em linguagem natural via agente (Ollama + llama3)

## Estrutura de arquivos

```
agrovision_ia/
├── app.py                        # Rotas FastAPI e lifespan
├── requirements.txt
├── .env.example                  # Variáveis de ambiente (copie para .env)
├── services/
│   ├── config.py                 # Leitura do .env e valores padrão
│   ├── schemas.py                # Modelos Pydantic (ChatRequest)
│   ├── event_repository.py       # SQLite: salvar e listar eventos
│   ├── capture_store.py          # Listagem de capturas salvas
│   ├── video_monitor.py          # Câmera, OpenCV, YOLO, stream MJPEG
│   ├── ollama_client.py          # Comunicação HTTP com Ollama
│   └── monitoring_agent.py       # Perfil do agente e contexto operacional
└── templates/
    └── index.html                # Dashboard (vídeo + eventos + chat)
```

## Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com/download) instalado e rodando
- Modelo llama3 baixado

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Arthur-ahp/agrovision_ia.git
cd agrovision_ia

# 2. Crie e ative o ambiente virtual
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o ambiente
cp .env.example .env
# Edite o .env conforme necessário

# 5. Baixe o modelo Ollama
ollama pull llama3

# 6. Suba o backend
python -m uvicorn app:app --reload
```

## Rotas disponíveis

| Rota | Descrição |
|------|-----------|
| `GET /` | Dashboard principal |
| `GET /health` | Status da aplicação e total de eventos |
| `GET /camera/status` | Status da câmera (online, tipo, frame disponível) |
| `GET /agent/status` | Inspeção do agente (contexto atual, eventos) |
| `GET /events` | Lista os 50 eventos mais recentes (JSON) |
| `GET /frame` | Último frame capturado (JPEG) |
| `GET /video_feed` | Stream MJPEG ao vivo |
| `POST /chat` | Chat com o agente (streaming) |

## Configuração da câmera

Edite `CAMERA_SOURCE` no `.env`:

```env
# Webcam local
CAMERA_SOURCE=0

# Stream HLS público (Caltrans - exemplo didático)
CAMERA_SOURCE=https://wzmedia.dot.ca.gov/D11/C214_SB_5_at_Via_De_San_Ysidro.stream/playlist.m3u8

# Câmera IP/RTSP autorizada
CAMERA_SOURCE=rtsp://usuario:senha@192.168.1.100:554/stream
```

> Use somente câmeras públicas oficiais ou privadas com autorização.

## Perguntas para testar o agente

- `Leia os eventos recentes, avalie o risco e recomende a próxima ação.`
- `Existe algum padrão no monitoramento atual?`
- `Avalie o risco operacional agora.`
- `Resuma a situação da câmera em 3 pontos.`
- `Com base nos eventos recentes, isso parece normal ou exige atenção?`

## Cuidados éticos e legais

- Usar somente câmeras públicas oficiais ou privadas com autorização
- Sem identificação facial ou de indivíduos
- Sem armazenamento de dados sensíveis desnecessários
- O agente fala sobre eventos, objetos, risco operacional e próximas ações
