from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, health, analysis, logs, agents
from app.services.socketio_app import sio_asgi_app
from app.services.db_init import init_db
from app.utils.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(analysis.router, tags=["analysis"])
    app.include_router(agents.router, tags=["agents"])
    app.include_router(logs.router, tags=["logs"])

    # Mount Socket.IO under /ws
    app.mount("/ws", sio_asgi_app)

    @app.on_event("startup")
    async def _startup():
        await init_db()

    return app


app = create_app()

