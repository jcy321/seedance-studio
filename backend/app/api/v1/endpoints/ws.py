"""WebSocket endpoint for real-time generation progress"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

router = APIRouter()

# 管理WebSocket连接：user_id -> set of WebSocket connections
active_connections: dict[int, Set[WebSocket]] = {}


async def broadcast_progress(user_id: int, data: dict):
    """向用户的所有连接广播进度"""
    connections = active_connections.get(user_id, set())
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception:
            connections.discard(ws)


@router.websocket("/ws/generation/{user_id}")
async def generation_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in active_connections:
        active_connections[user_id] = set()
    active_connections[user_id].add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # 客户端可以发送ping保持连接
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections.get(user_id, set()).discard(websocket)
        if not active_connections.get(user_id):
            active_connections.pop(user_id, None)
    except Exception:
        active_connections.get(user_id, set()).discard(websocket)
