"""WebSocket para atualizações em tempo real (com fallback por polling no frontend)."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime import manager

router = APIRouter(tags=["Tempo real"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    channels = [
        c.strip()
        for c in (websocket.query_params.get("channels") or "").split(",")
        if c.strip()
    ]
    token = websocket.query_params.get("token")
    if token:
        channels.append(f"user:token:{token}")
    await manager.connect(websocket, channels)
    try:
        while True:
            # o cliente pode enviar "ping" ou novos canais para assinar
            data = await websocket.receive_json()
            if data.get("action") == "subscribe":
                await manager.connect(websocket, data.get("channels") or [])
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
