# -*- coding: utf-8 -*-
"""DBをNAS共有フォルダへ日次バックアップする（要件定義書 5章 / DB設計書 4章）。

    python scripts/backup.py "\\\\NAS\\販売管理\\backup"

VACUUM INTO で整合性を保って取得し、`sales_YYYYMMDD.db` として保存する。
既定で7世代を残し、古いものから削除する。タスクスケジューラ/cron から日次実行する。
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402

KEEP_GENERATIONS = 7


def run(dest_dir: str, keep: int = KEEP_GENERATIONS) -> Path:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    conn = db.connect()
    try:
        out = db.backup_to(conn, dest / "sales_{}.db".format(date.today().strftime("%Y%m%d")))
    finally:
        conn.close()
    backups = sorted(dest.glob("sales_*.db"))
    for old in backups[:-keep]:
        old.unlink()
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    keep = int(sys.argv[2]) if len(sys.argv) > 2 else KEEP_GENERATIONS
    print("backup done:", run(sys.argv[1], keep))
