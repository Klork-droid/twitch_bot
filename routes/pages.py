from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from managers.auth import get_client_token

router = APIRouter(dependencies=[Depends(get_client_token)])
templates = Jinja2Templates(directory="templates")

@router.get("/player", response_class=HTMLResponse)
async def player_page(
        request: Request,
        client_token: str = Depends(get_client_token),
):
    """
    Отображает страницу плеера.
    """
    return templates.TemplateResponse("player.html", {"request": request})

@router.get("/playlist", response_class=HTMLResponse)
async def playlist_page(
        request: Request,
        client_token: str = Depends(get_client_token),
):
    """
    Отображает страницу плейлиста.
    """
    return templates.TemplateResponse("playlist.html", {"request": request})
