# -*- coding: utf-8 -*-
"""SQLite 接続とスキーマ初期化。

DBファイルはアプリ稼働マシンのローカルディスクに置く。
NAS共有フォルダへ直接置くとファイルロックが効かず破損するため禁止（DB設計書 冒頭）。
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = APP_DIR / "schema.sql"
DEFAULT_DB_PATH = APP_DIR.parent / "data" / "sales.db"


def db_path() -> Path:
    """DBファイルの場所。環境変数 SALES_DB_PATH で上書きできる。"""
    return Path(os.environ.get("SALES_DB_PATH", DEFAULT_DB_PATH))


def connect(path=None) -> sqlite3.Connection:
    target = Path(path) if path else db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # 社内数名の同時利用に耐えるため
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


@contextmanager
def transaction(conn: sqlite3.Connection):
    """BEGIN IMMEDIATE で書き込みを直列化する（管理No. 採番の重複防止）。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def backup_to(conn: sqlite3.Connection, dest) -> Path:
    """VACUUM INTO で整合性を保ったバックアップを取る（NAS共有フォルダ向け）。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    conn.execute("VACUUM INTO ?", (str(dest),))
    return dest
