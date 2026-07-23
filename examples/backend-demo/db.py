"""Proveedor de Engine para el ejemplo (SQLite demo.db).
En una app real esto apunta a PostgreSQL (réplica de lectura) vía DATABASE_URL."""
from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DATABASE_URL = os.environ.get("ANALYTICS_DB_URL", "sqlite:///demo.db")


@lru_cache
def get_engine() -> Engine:
    kwargs = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, **kwargs)
