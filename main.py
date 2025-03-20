import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from routes import pages, track, websockets

app = FastAPI()
# Монтирование статики без каких-либо зависимостей
app.mount("/static", StaticFiles(directory="static"), name="static")

# app.add_middleware(ZstdCompressionMiddleware, minimum_size=500)
app.include_router(pages.router)
app.include_router(track.router)
app.include_router(websockets.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        # reload=True,
        # reload_dirs=["templates", "static"]
    )
