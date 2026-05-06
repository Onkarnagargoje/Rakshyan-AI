"""Runtime build identity (git + deploy markers). Lazy-resolve git once per process."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_cached_git: str | None = None


def get_git_commit_short() -> str:
    """Short SHA from GIT_COMMIT env, else `git rev-parse` from repo root, else empty."""
    global _cached_git
    if _cached_git is not None:
        return _cached_git
    env_g = os.environ.get("GIT_COMMIT", "").strip()
    if env_g:
        _cached_git = env_g[:40]
        return _cached_git
    here = Path(__file__).resolve()
    for root in (here.parents[3], here.parents[2]):
        try:
            if (root / ".git").exists():
                r = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                if r.returncode == 0 and (sha := r.stdout.strip()):
                    _cached_git = sha
                    return _cached_git
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    _cached_git = ""
    return ""
