from fastapi import APIRouter

from app.services.analyzer_graph import ANALYZER_GRAPH_REVISION
from app.utils.build_info import get_git_commit_short
from app.utils.settings import settings

router = APIRouter()


def _version_payload() -> dict:
    return {
        "app_build_id": settings.app_build_id or "dev",
        "env": settings.env,
        "git_commit": get_git_commit_short(),
        "analyzer_graph_revision": ANALYZER_GRAPH_REVISION,
    }


@router.get("/health")
def health():
    return {"status": "ok", **_version_payload()}


@router.get("/version")
def version():
    """Deploy proof: git SHA (when available), static analyzer revision, APP_BUILD_ID."""
    return _version_payload()

