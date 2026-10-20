import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from config import config
from routes.posts import posts_router
from routes.tags import tags_router
from routes.favorites import favorites_router
from routes.users import users_router
from routes.proxy import proxy_router
from routes.admin import admin_router
from services.http_client import close_http_client

VERSION_FILE = Path(__file__).parent / "VERSION"
__version__ = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "0.1.6"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks
    await close_http_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SzuruRelay",
        description="Danbooru to Szurubooru API Translation Proxy",
        version=__version__,
        lifespan=lifespan,
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse(
            {
                "status": "healthy",
                "version": __version__,
                "backend_url": config.SZURUBOORU_URL,
                "reverse_proxy_mode": config.REVERSE_PROXY_MODE,
            },
            status_code=200,
        )

    # Register API routers
    app.include_router(posts_router)
    app.include_router(tags_router)
    app.include_router(favorites_router)
    app.include_router(users_router)
    app.include_router(proxy_router)
    app.include_router(admin_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", config.SERVICE_PORT))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=config.DEBUG)
