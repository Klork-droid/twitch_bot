from fastapi import APIRouter, HTTPException, Depends, Body
from starlette.responses import StreamingResponse

from managers.auth import get_client_token
from managers.manager import PLAYLIST
from store import Track
from utils import select_track_data_function

router = APIRouter(dependencies=[Depends(get_client_token)])


@router.get("/track")
async def get_track(
        client_token: str = Depends(get_client_token)
):
    """
    Отдает аудио первого трека плейлиста и помечает его как текущий.
    """
    current_track: Track = PLAYLIST.get_first_track()
    if current_track is None:
        raise HTTPException(status_code=404, detail="Трек не найден")

    PLAYLIST.current = current_track.track_id

    return StreamingResponse(current_track.stream_bytes(), media_type="video/mp4")


@router.post("/add")
async def add_track(
        url: str = Body(..., embed=True, description="URL трека для загрузки"),
        user_name: str = Body('test', embed=True, description="Имя пользователя"),
        user_id: str = Body('test', embed=True, description="ID пользователя"),
        client_token: str = Depends(get_client_token),
):
    """
    Загружает новый трек по URL и добавляет его в плейлист.
    """
    get_track_data = select_track_data_function(url=url, client_token=client_token)
    if not get_track_data:
        raise HTTPException(status_code=404, detail=f"Unknown URL: {url}")

    try:
        track_data: Track | None = await get_track_data(
            url=url,
            user_name=user_name,
            user_id=user_id,
            client_token=client_token,
        )
        if not track_data:
            raise HTTPException(status_code=400, detail="Неверный URL трека")
        return {"detail": "Трек успешно загружен и валидирован"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
