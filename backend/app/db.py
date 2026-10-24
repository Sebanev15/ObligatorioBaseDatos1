import threading
from contextlib import contextmanager
from typing import Any, Iterator, Literal, NamedTuple, Sequence

import pymysql
from dbutils.pooled_db import PooledDB
from pymysql.cursors import DictCursor

from .config import settings

Role = Literal["auth", "administrador", "planillero"]
_pools: dict[str, PooledDB] = {}
_lock = threading.Lock()

def _credentials(role: Role) -> tuple[str, str]:
    return {
        "administrador": (settings.db_admin_user, settings.db_admin_password),
        "planillero": (settings.db_planillero_user, settings.db_planillero_password),
        "auth": (settings.db_auth_user, settings.db_auth_password),
    }[role]

def _get_pool(role: Role) -> PooledDB:
    with _lock:
        if role not in _pools:
            user, password = _credentials(role)
            _pools[role] = PooledDB(
                creator=pymysql, maxconnections=10, blocking=True,
                host=settings.db_host, port=settings.db_port,
                user=user, password=password, database=settings.db_name,
                charset="utf8mb4", cursorclass=DictCursor, autocommit=False,
            )
        return _pools[role]

@contextmanager
def get_connection(role: Role) -> Iterator[Any]:
    """Commit al salir bien, rollback si hay cualquier excepción."""
    conn = _get_pool(role).connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

class ExecResult(NamedTuple):
    rowcount: int
    lastrowid: int

def fetch_all(conn, sql: str, params: Sequence[Any] = ()) -> list[dict]:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return list(cur.fetchall())
    finally:
        cur.close()

def fetch_one(conn, sql: str, params: Sequence[Any] = ()) -> dict | None:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()

def execute(conn, sql: str, params: Sequence[Any] = ()) -> ExecResult:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return ExecResult(cur.rowcount, cur.lastrowid)
    finally:
        cur.close()