"""Utilitários gerais."""

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_dict(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {k: as_dict(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_dict(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta (great-circle), em quilômetros."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def normalize_text(value: str) -> str:
    """Remove acentos e normaliza para comparação."""
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def paginate(items: Iterable[Any], page: int = 1, page_size: int = 20):
    items = list(items)
    total = len(items)
    start = (page - 1) * page_size
    return items[start : start + page_size], total


def coalesce(value: Optional[Any], default: Any) -> Any:
    return default if value is None else value
