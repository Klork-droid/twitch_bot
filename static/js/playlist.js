// playlist.js: Логика работы плейлиста
const LOAD_FILE_TS = Date.now();

document.addEventListener("DOMContentLoaded", function () {
    const clientToken = getTokenFromURL();
    const trackListEl = document.getElementById('trackList');
    const RECONNECT_INTERVAL = 5000; // интервал переподключения (5 секунд)
    const PING_TIMEOUT = 10000;      // время ожидания пинга (15 секунд)

    function processPlaylistData(data) {
        console.log("Получено сообщение от WS плейлиста:", data);
        if (data.action === "update_list" && data.tracks) {
            if (data.tracks.length === 0) {
                trackListEl.innerHTML = "<div>Список заказов пуст</div>";
            } else {
                trackListEl.innerHTML = "";
                data.tracks.forEach(track => {
                    const div = document.createElement('div');
                    div.className = "track-item";
                    div.textContent = `${track.track_title} [от ${track.user_name}]`;

                    const removeBtn = document.createElement('button');
                    removeBtn.textContent = "Удалить";
                    removeBtn.addEventListener('click', () => {
                        wsPlaylist.send(`remove:${track.track_id}`);
                    });

                    div.appendChild(removeBtn);
                    trackListEl.appendChild(div);
                });
            }
        }
    }

    let wsPlaylist;
    let pingTimeout;

    function connectPlaylistSocket() {
        wsPlaylist = new WebSocket(`ws://${window.location.host}/ws/playlist?client_token=${clientToken}`);

        wsPlaylist.onopen = () => {
            console.log("Соединение WS плейлиста установлено");
            wsPlaylist.send(LOAD_FILE_TS)
            resetPingTimeout();
        };

        wsPlaylist.onmessage = (event) => {
            // Сбрасываем таймаут при получении любого сообщения
            resetPingTimeout();
            try {
                if (event.data === "ping") {
                    wsPlaylist.send("pong");
                    return;
                }

                if (event.data === "reload_client") {
                    console.log("Обнаружено обновление статичных файлов, перезагружаем страницу");
                    window.location.reload();
                }

                const data = JSON.parse(event.data);
                processPlaylistData(data);
            } catch (e) {
                console.error("Ошибка парсинга JSON:", e);
            }
        };

        wsPlaylist.onerror = (error) => {
            console.error("Ошибка WS плейлиста:", error);
        };

        wsPlaylist.onclose = () => {
            console.warn("WS плейлист закрыт, переподключаемся через " + RECONNECT_INTERVAL + " мс");
            clearTimeout(pingTimeout);
            setTimeout(connectPlaylistSocket, RECONNECT_INTERVAL);
        };
    }

    function resetPingTimeout() {
        clearTimeout(pingTimeout);
        pingTimeout = setTimeout(() => {
            console.warn("Отсутствие активности, закрываем WS плейлиста для переподключения");
            wsPlaylist.close();
        }, PING_TIMEOUT);
    }

    // Инициализация соединения
    connectPlaylistSocket();
});
