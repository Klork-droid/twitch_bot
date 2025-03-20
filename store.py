import asyncio
from asyncio import Queue, Event
from collections import OrderedDict
from itertools import count

from constants import load_config, SourceType

CONFIG = load_config()
CHUNK_SIZE = CONFIG["CHUNK_SIZE"]
IMAGE_SIZE = CONFIG["IMAGE_SIZE"]


class Track:
    _id_counter = count(1)

    def __init__(
            self,
            user_id: str,
            user_name: str,
            source_type: SourceType,
            track_bytes: bytes = b'',
            track_title: str | None = None,
            artist_name: str | None = None,
            track_name: str | None = None,
            poster_url: str | None = None,
    ):
        self.track_id = next(Track._id_counter)
        self.source_type = source_type
        if track_title:
            self.track_title = track_title
        else:
            self.track_title = f'{artist_name} — {track_name}'
        self.artist_name = artist_name
        self.track_name = track_name
        self.track_bytes = track_bytes
        self.user_id = user_id
        self.user_name = user_name
        self.poster_url = self.prepare_poster_url(poster_url)

        self.track_bytes_chunks: Queue = Queue()
        self.download_finished = Event()

    def prepare_poster_url(self, poster_url):
        if self.source_type is SourceType.yandex:
            poster_url = poster_url.replace('%%', f'{IMAGE_SIZE}x{IMAGE_SIZE}')
            poster_url = f'https://{poster_url}'
        elif self.source_type is SourceType.soundcloud:
            poster_url = poster_url.replace('large', 't500x500')
        else:
            poster_url = ''
        return poster_url

    async def stream_bytes(self):
        if self.download_finished.is_set():
            for i in range(0, len(self.track_bytes), CHUNK_SIZE):
                yield self.track_bytes[i:i + CHUNK_SIZE]
                await asyncio.sleep(0)  # позволяет event loop переключаться
        else:
            while True:
                # Ожидаем следующий чанк из очереди текущего трека
                chunk = await self.track_bytes_chunks.get()
                if chunk is None:  # Используем None как маркер завершения передачи
                    break
                yield chunk
                await asyncio.sleep(0)  # переключение между задачами


class Playlist:
    def __init__(self):
        self.tracks = OrderedDict()
        self.current = None  # ID текущего трека

    def add_track(self, track: Track):
        """
        Добавляет новый трек в конец очереди.
        Если трек с таким track_id уже существует, выбрасывает исключение.
        """
        if track.track_id in self.tracks:
            raise ValueError(f"Трек с id {track.track_id} уже существует.")
        self.tracks[track.track_id] = track

    def get_first_track(self):
        """
        Возвращает текущий трек для воспроизведения (первый в очереди).
        Если очередь пуста, возвращает None.
        """
        if self.tracks:
            first_key = next(iter(self.tracks))
            return self.tracks[first_key]

        return None

    def finish_current_track(self):
        """
        Удаляет текущий трек (если он доиграл до конца) и возвращает его.
        Это имитирует завершение воспроизведения текущего трека.
        """
        if self.tracks:
            first_key = next(iter(self.tracks))
            return self.tracks.pop(first_key)
        return None

    def skip_current_track(self):
        """
        Пропускает текущий трек: удаляет его из очереди и возвращает следующий трек для воспроизведения.
        """
        self.finish_current_track()
        return self.get_first_track()

    def remove_track_by_id(self, track_id: str):
        """
        Удаляет трек с заданным track_id из очереди.
        Это может быть использовано, если пользователь решил пропустить определённый трек,
        даже если он уже играет.
        """
        if track_id in self.tracks:
            return self.tracks.pop(track_id)
        else:
            raise KeyError(f"Трек с id {track_id} не найден.")

    def list_tracks(self):
        """
        Возвращает список треков в очереди в порядке их добавления.
        """
        return list(self.tracks.values())
