// player.js: Логика работы медиа плеера
const LOAD_FILE_TS = Date.now();

document.addEventListener("DOMContentLoaded", function () {
    const clientToken = getTokenFromURL();
    const playerContainer = document.getElementById('player-container');
    const mediaPlayer = document.getElementById('mediaPlayer');
    const mediaSource = document.getElementById('mediaSource');
    const RECONNECT_INTERVAL = 5000; // интервал переподключения (5 секунд)
    const PING_TIMEOUT = 10000;      // время ожидания пинга (10 секунд)

    function processPlayerData(data) {
        console.log("Получено сообщение от WS плеера:", data);
        if (data.action === "update" && data.current_track) {
            playerContainer.style.display = "block";
            mediaSource.src = `/track?client_token=${clientToken}`;
            mediaPlayer.poster = data.current_track.poster_url || "";
            const clipTitleElement = document.getElementById("clipTitle");
            clipTitleElement.innerText = data.current_track.track_title + ' [от ' + data.current_track.user_name + ']';
            mediaPlayer.load();
            mediaPlayer.play();
            // Подкорректируем позицию текста относительно видео
            adjustClipTitlePosition();
        } else if (data.action === "hide") {
            mediaPlayer.pause();
            playerContainer.style.display = "none";
        }
    }

    let wsPlayer;
    let pingTimeout;

    function connectPlayerSocket() {
        wsPlayer = new WebSocket(`ws://${window.location.host}/ws/player?client_token=${clientToken}`);

        wsPlayer.onopen = () => {
            console.log("Соединение WS плеера установлено");
            wsPlayer.send(LOAD_FILE_TS);
            resetPingTimeout();
        };

        wsPlayer.onmessage = (event) => {
            resetPingTimeout();
            try {
                if (event.data === "ping") {
                    wsPlayer.send("pong");
                    return;
                }

                if (event.data === "reload_client") {
                    console.log("Обнаружено обновление статичных файлов, перезагружаем страницу");
                    window.location.reload();
                    return;
                }

                const data = JSON.parse(event.data);
                processPlayerData(data);
            } catch (e) {
                console.error("Ошибка парсинга JSON:", event.data, e);
            }
        };

        wsPlayer.onerror = (error) => {
            console.error("Ошибка WS плеера:", error);
        };

        wsPlayer.onclose = () => {
            console.warn("WS плеер закрыт, переподключаемся через " + RECONNECT_INTERVAL + " мс");
            clearTimeout(pingTimeout);
            setTimeout(connectPlayerSocket, RECONNECT_INTERVAL);
        };
    }

    function resetPingTimeout() {
        clearTimeout(pingTimeout);
        pingTimeout = setTimeout(() => {
            console.warn("Отсутствие активности, закрываем WS плеера для переподключения");
            wsPlayer.close();
        }, PING_TIMEOUT);
    }

    // Функция для корректировки позиции clip-title
    function adjustClipTitlePosition() {
        // Получаем границы видео относительно окна
        const videoRect = mediaPlayer.getBoundingClientRect();
        const containerRect = playerContainer.getBoundingClientRect();
        // Вычисляем смещение: left видео относительно контейнера
        const offsetLeft = videoRect.left - containerRect.left;
        // Устанавливаем left для clip-title равным offsetLeft
        const clipTitle = document.getElementById("clipTitle");
        clipTitle.style.left = offsetLeft + "px";
    }

    // Используем событие изменения размеров окна
    window.addEventListener("resize", adjustClipTitlePosition);

    // Инициализация соединения
    connectPlayerSocket();

    // Отправляем команду ended при завершении воспроизведения
    mediaPlayer.addEventListener('ended', () => {
        console.log("Медиа трек закончил воспроизведение");
        if (wsPlayer && wsPlayer.readyState === WebSocket.OPEN) {
            wsPlayer.send("ended");
        }
    });
});
