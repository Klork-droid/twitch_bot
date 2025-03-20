import asyncio
import os
import re
import sys

from orjson import orjson
from soundcloud import SoundCloud
from yandex_music import ClientAsync

from constants import load_config, SourceType
from managers.manager import PLAYLIST, player_clients, playlist_clients
from managers.ws_utils import send_player_update, send_playlist_update
from store import Track

CONFIG = load_config()

TRACK_ID_REGEX = re.compile(r"track/(\d+)")
yandex_music_token = CONFIG["YToken"]
YCLIENT = asyncio.run(ClientAsync(yandex_music_token).init())

CHUNK_SIZE = CONFIG["CHUNK_SIZE"]


def select_track_data_function(url: str, **kwargs):
    track_sources = {
        SourceType.yandex: get_yandex_track_data,
        SourceType.youtube: get_youtube_track_data,
        SourceType.soundcloud: get_soundcloud_track_data,
    }
    for key, func in track_sources.items():
        if key in url:
            return func
    return None


async def get_yandex_track_data(
        url: str,
        user_name: str,
        user_id: str,
        client_token: str,
) -> Track | None:
    match = TRACK_ID_REGEX.search(url)
    if not match:
        return None

    track_id = match.group(1)
    yandex_track = (await YCLIENT.tracks(track_id))[0]
    artist_name = ', '.join(artist.name for artist in yandex_track.artists)

    track_source = await yandex_track.download_bytes_async()

    track = Track(
        source_type=SourceType.yandex,
        artist_name=artist_name,
        track_name=yandex_track.title,
        user_id=user_id,
        user_name=user_name,
        track_bytes=track_source,
        poster_url=yandex_track.og_image
    )
    track.download_finished.set()

    PLAYLIST.add_track(track)

    if client_token in player_clients:
        await send_player_update(player_clients[client_token])
    if client_token in playlist_clients:
        await send_playlist_update(playlist_clients[client_token])

    return track


async def get_soundcloud_track_data(
        url: str,
        user_name: str,
        user_id: str,
        client_token: str,
) -> Track | None:
    client = SoundCloud()
    track = client.resolve(url)

    poster_url = track.artwork_url

    track = Track(
        source_type=SourceType.soundcloud,
        user_id=user_id,
        user_name=user_name,
        track_title=track.title,
        poster_url=poster_url,
    )

    PLAYLIST.add_track(track)

    error_file = open('error_logs', "w", encoding="utf-8")
    venv_dir = os.path.dirname(sys.executable)
    scdl_executable = os.path.join(venv_dir, "scdl.exe")

    process = await asyncio.create_subprocess_exec(
        scdl_executable,
        '-l', url,  # URL трека
        '--name-format', '-',  # выводим трек в stdout (по аналогии с yt-dlp -o -)=
        stdout=asyncio.subprocess.PIPE,
        stderr=error_file,
    )

    await streaming_download(
        track=track,
        process=process,
        client_token=client_token,
    )

    return track


async def get_youtube_track_data(
        url: str,
        user_name: str,
        user_id: str,
        client_token: str,
) -> Track | None:
    process_json = await asyncio.create_subprocess_exec(
        'yt-dlp.exe',
        '-J', url,
        stdout=asyncio.subprocess.PIPE
    )
    process_json, _ = await process_json.communicate()
    info_dict = orjson.loads(process_json)
    track = Track(
        source_type=SourceType.youtube,
        user_id=user_id,
        user_name=user_name,
        track_title=info_dict['title']
    )

    PLAYLIST.add_track(track)

    process = await asyncio.create_subprocess_exec(
        'yt-dlp.exe',
        # '-f', 'bestvideo[height<=480]+mp3/best',
        '-f',
        '(bestvideo[height<=480][vcodec*=av01]/bestvideo[height<=480][vcodec*=hevc]/bestvideo[height<=480][vcodec*=vp9]/bestvideo[height<=480][vcodec*=avc])+bestaudio/best',
        # '--external-downloader', 'ffmpeg',
        # '--ffmpeg-location', r'C:\Users\Klork\Downloads\ffmpeg\bin\ffmpeg.exe',
        # '--merge-output-format', 'mp4',
        # '--remux-video', 'mp4',
        '-o', '-',  # Сохраняем в поток
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    await streaming_download(
        track=track,
        process=process,
        client_token=client_token,
    )

    return track


async def streaming_download(
        track: Track,
        process,
        client_token: str,
):
    first_chunk_received = False
    while True:
        chunk = await process.stdout.read(CHUNK_SIZE)
        if not chunk:
            # Сигнализируем о завершении скачивания
            track.download_finished.set()
            await track.track_bytes_chunks.put(None)  # сигнал завершения
            break

        # Добавляем полученный чанк к накопленному буферу (если нужно сохранить весь файл)
        track.track_bytes += chunk

        # Если это первый ненулевой чанк, отправляем обновление клиентам
        if not first_chunk_received and chunk:
            first_chunk_received = True
            if client_token in player_clients:
                await send_player_update(player_clients[client_token])
            if client_token in playlist_clients:
                await send_playlist_update(playlist_clients[client_token])

        # Передаём чанк в очередь для дальнейшей обработки
        await track.track_bytes_chunks.put(chunk)
