import asyncio
import json
import websockets

PUBSUB_URL = "wss://pubsub-edge.twitch.tv"
CHANNEL_ID = "ВАШ_CHANNEL_ID"  # замените на ID вашего канала
OAUTH_TOKEN = "ВАШ_OAUTH_TOKEN"  # должен включать scope channel:read:redemptions


async def listen_pubsub():
    async with websockets.connect(PUBSUB_URL) as ws:
        # Отправляем запрос на подписку
        listen_message = {
            "type": "LISTEN",
            "nonce": "unique_nonce_123",  # уникальное значение, например, UUID
            "data": {
                "topics": [f"channel-points-channel-v1.{CHANNEL_ID}"],
                "auth_token": OAUTH_TOKEN
            }
        }
        await ws.send(json.dumps(listen_message))
        print("Подписка отправлена")

        while True:
            response = await ws.recv()
            data = json.loads(response)
            print("Получено сообщение из PubSub:", data)
            if data.get("type") == "MESSAGE":
                # Здесь можно обрабатывать события редемпшена
                redemption_data = json.loads(data["data"]["message"])
                print("Редемпшен получен:", redemption_data)
            elif data.get("type") == "RESPONSE":
                # Ответ на запрос подписки
                if data.get("error"):
                    print("Ошибка подписки:", data["error"])
                else:
                    print("Подписка успешна")


async def main():
    # Запускаем PubSub слушатель параллельно с вашим TwitchIO ботом
    pubsub_task = asyncio.create_task(listen_pubsub())

    # Здесь можно запускать ваш TwitchIO бот (если бот не блокирует основной цикл)
    # Например, если вы запускаете bot.run() в отдельном процессе или потоке
    # await bot.start()

    await pubsub_task


if __name__ == '__main__':
    asyncio.run(main())
