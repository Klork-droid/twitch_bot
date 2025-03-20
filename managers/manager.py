from store import Playlist

# Глобальное состояние: плейлист и словари клиентов
PLAYLIST = Playlist()

# Словари для хранения client_token: WebSocket для каждого пользователя
player_clients = {}  # клиенты плеера
playlist_clients = {}  # клиенты плейлиста
