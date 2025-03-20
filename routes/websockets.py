import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from orjson import orjson
from managers.manager import PLAYLIST, player_clients, playlist_clients
from managers.ws_utils import send_player_update, send_playlist_update
from managers.auth import get_client_token

SERVER_START_TS: int = int(time.time())
router = APIRouter(
    prefix="/ws",
    dependencies=[Depends(get_client_token)]
)

async def ping_loop(ws: WebSocket):
    while True:
        await asyncio.sleep(5)
        await ws.send_text("ping")

@router.websocket("/player")
async def websocket_player(ws: WebSocket, client_token: str = Depends(get_client_token)):
    """
    Вебсокет для плеера: получение текущего трека и обработка команд (например, "skip").
    """
    await ws.accept()

    # Проверяем время обновления файлов на фронте
    client_start_ts = (await ws.receive_text()).strip().lower()
    files_load_ago: int = SERVER_START_TS - int(client_start_ts[:-3])
    if files_load_ago > 10:
        await ws.send_text('reload_client')
    else:
        await ws.send_text(f'{files_load_ago} - it\'s OK!')
    # Запускаем фоновый цикл пинга
    ping_task = asyncio.create_task(ping_loop(ws))

    player_clients[client_token] = ws
    await send_player_update(ws)

    try:
        while True:
            data = (await ws.receive_text()).strip().lower()
            if data in ["skip", "ended"]:
                PLAYLIST.finish_current_track()
                await send_player_update(ws)
                await send_playlist_update(playlist_clients[client_token])
    except WebSocketDisconnect:
        player_clients.pop(client_token, None)
    finally:
        ping_task.cancel()  # Отменяем задачу пинга при отключении

@router.websocket("/playlist")
async def websocket_playlist(ws: WebSocket, client_token: str = Depends(get_client_token)):
    """
    Вебсокет для плейлиста: получение обновлений списка треков и обработка команд удаления.
    Формат команды: "remove:<track_id>"
    """
    await ws.accept()

    # Проверяем время обновления файлов на фронте
    client_start_ts = (await ws.receive_text()).strip().lower()
    files_load_ago: int = SERVER_START_TS - int(client_start_ts[:-3])
    if files_load_ago > 10:
        await ws.send_text('reload_client')
    else:
        await ws.send_text(f'{files_load_ago} - it\'s OK!')

    # Запускаем фоновый цикл пинга
    ping_task = asyncio.create_task(ping_loop(ws))

    playlist_clients[client_token] = ws
    await send_playlist_update(ws)

    try:
        while True:
            data = await ws.receive_text()
            if data.startswith("remove:"):
                try:
                    track_id = int(data.split("remove:")[1])
                    PLAYLIST.remove_track_by_id(track_id)
                    await send_playlist_update(ws)
                    await send_player_update(player_clients[client_token])
                except Exception as e:
                    error_msg = {"action": "error", "detail": str(e)}
                    await ws.send_text(orjson.dumps(error_msg).decode('utf-8'))
    except WebSocketDisconnect:
        playlist_clients.pop(client_token, None)
    finally:
        ping_task.cancel()  # Отменяем задачу пинга при отключении
