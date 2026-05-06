import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, health, analysis, logs, agents, family
from app.services.socketio_app import sio_asgi_app
from app.services.db_init import init_db
from app.services.analyzer_graph import ANALYZER_GRAPH_REVISION
from app.utils.build_info import get_git_commit_short
from app.utils.logging import configure_logging
from app.utils.settings import settings

_startup_log = logging.getLogger("app.main")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await init_db()
    _startup_log.info(
        "SafeNest API ready env=%s app_build_id=%s git=%s analyzer_graph=%s — GET /health /version",
        settings.env,
        settings.app_build_id or "dev",
        get_git_commit_short() or "(none)",
        ANALYZER_GRAPH_REVISION,
    )
    yield


def create_app() -> FastAPI:
    # Psycopg async on Windows requires Selector event loop.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version=(settings.app_build_id or "dev"),
        lifespan=_lifespan,
    )

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
    app.include_router(family.router)
    app.include_router(analysis.router, tags=["analysis"])
    app.include_router(agents.router, tags=["agents"])
    app.include_router(logs.router, tags=["logs"])

    # Mount Socket.IO under /ws
    app.mount("/ws", sio_asgi_app)

    return app


app = create_app()

