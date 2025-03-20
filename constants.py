from enum import StrEnum

from orjson import orjson


def load_config():
    with open("config.json", "rb") as f:
        config = orjson.loads(f.read())
    return config


class SourceType(StrEnum):
    yandex = 'yandex'
    youtube = 'youtube'
    soundcloud = 'soundcloud'
    spotify = 'spotify'
