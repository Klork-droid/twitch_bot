from fastapi import WebSocket
from orjson import orjson
from managers.manager import PLAYLIST
from store import Track


async def send_player_update(ws: WebSocket) -> None:
    """
    Отправляет через вебсокет данные о текущем треке.
    Если трек отсутствует, отправляет команду для скрытия плеера.
    """
    current_track: Track = PLAYLIST.get_first_track()
    if current_track:
        message = {
            "action": "update",
            "current_track": {
                "track_id": current_track.track_id,
                "track_title": current_track.track_title,
                "user_name": current_track.user_name,
                "poster_url": current_track.poster_url,
            }
        }
    else:
        message = {"action": "hide"}
    # orjson.dumps возвращает байты, а send_text ожидает строку,
    # поэтому декодируем результат в UTF-8.
    await ws.send_text(orjson.dumps(message).decode('utf-8')) # TODO: заменить на bytes?

async def send_playlist_update(ws: WebSocket) -> None:
    """
    Отправляет через вебсокет актуальный список треков плейлиста.
    """
    tracks = PLAYLIST.list_tracks()
    data = {
        "action": "update_list",
        "tracks": [
            {
                "track_id": t.track_id,
                "track_title": t.track_title,
                "user_name": t.user_name
            } for t in tracks
        ]
    }
    await ws.send_text(orjson.dumps(data).decode('utf-8'))
