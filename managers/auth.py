from fastapi import Request, WebSocket, HTTPException, status


async def get_client_token(request: Request = None, websocket: WebSocket = None) -> str:
    """
    Универсальная зависимость для извлечения client_token.
    Если request передан (HTTP‑эндпоинт), извлекает token из query-параметров.
    Если websocket передан (WebSocket‑эндпоинт), делает то же самое и закрывает соединение при отсутствии token.
    """
    if request is not None:
        token = request.query_params.get("client_token")
        if not token:
            raise HTTPException(status_code=400, detail="client_token обязателен")
    elif websocket is not None:
        token = websocket.query_params.get("client_token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise Exception("client_token обязателен")
    else:
        raise Exception("Не удалось определить источник запроса")

    return token
