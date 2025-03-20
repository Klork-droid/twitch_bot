// common.js: Общие функции для всех страниц

/**
 * Извлекает параметр 'token' из URL.
 * @returns {string|null} Значение token или null, если не найден.
 */
function getTokenFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('client_token');
}
