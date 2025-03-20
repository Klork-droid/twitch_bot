import zstandard as zstd
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import AsyncGenerator


class ZstdCompressionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, minimum_size: int = 500) -> None:
        super().__init__(app)
        self.minimum_size = minimum_size  # Минимальный размер ответа для сжатия

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Проверяем, поддерживает ли клиент zstd (используем request.headers)
        accept_encoding = request.headers.get("accept-encoding", "")
        if "zstd" not in accept_encoding.lower():
            return response

        # Собираем тело ответа в один блок байтов
        body = b"".join([chunk async for chunk in response.body_iterator])
        if len(body) < self.minimum_size:
            # Если тело меньше порогового размера, не сжимаем
            # Оборачиваем тело в асинхронный генератор
            async def async_iter() -> AsyncGenerator[bytes, None]:
                yield body

            response.body_iterator = async_iter()
            return response

        # Сжимаем тело с помощью zstd
        compressor = zstd.ZstdCompressor()
        compressed_body = compressor.compress(body)

        # Обновляем заголовки ответа
        response.headers["Content-Encoding"] = "zstd"
        response.headers["Content-Length"] = str(len(compressed_body))
        response.headers["Vary"] = "Accept-Encoding"

        # Оборачиваем сжатое тело в асинхронный генератор
        async def async_iter() -> AsyncGenerator[bytes, None]:
            yield compressed_body

        response.body_iterator = async_iter()
        return response
