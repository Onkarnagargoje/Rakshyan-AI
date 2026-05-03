import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.utils.settings import settings


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@dataclass(frozen=True)
class HashChainEntry:
    ts_ms: int
    event_type: str
    payload: Dict[str, Any]
    prev_hash: str
    hash: str


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_chain_hash(prev_hash: str, event_type: str, payload: Dict[str, Any]) -> str:
    ts_ms = int(time.time() * 1000)
    base = {
        "ts_ms": ts_ms,
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
        "salt": settings.log_hash_chain_salt,
    }
    return hashlib.sha256(_stable_json(base).encode("utf-8")).hexdigest()


def build_chain_entry(
    *,
    prev_hash: str,
    event_type: str,
    payload: Dict[str, Any],
    ts_ms: Optional[int] = None,
) -> HashChainEntry:
    ts_ms = ts_ms or int(time.time() * 1000)
    base = {
        "ts_ms": ts_ms,
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
        "salt": settings.log_hash_chain_salt,
    }
    h = hashlib.sha256(_stable_json(base).encode("utf-8")).hexdigest()
    return HashChainEntry(ts_ms=ts_ms, event_type=event_type, payload=payload, prev_hash=prev_hash, hash=h)

