# Sales OS Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 軸C（法人AIコンサル）アウトバウンドの最小MVPを構築し、「毎朝オーナーが10社承認→AIがGmailで送信」のループを稼働させる。

**Architecture:** VPS側にPython製の `sales-ops/` プロジェクトを新設。SQLite（`/opt/sales-ops/data/sales_ops.db`、Google Drive 配下**ではない**）で承認キューと企業DBを管理。Google Maps APIで毎日T2企業リストを取得→Claude APIでDM下書き生成→`approval_queue` にpending投入→朝のClaude Codeセッション（`/sales-briefing` スキル）で承認→Gmail APIで1通/分送信。TDDで進める。

**Tech Stack:** Python 3.10+, SQLite, Google Maps Places API (New), Anthropic SDK (Claude API), Google Gmail API (OAuth 2.0), pytest, Playwright不要（Phase 1スコープ外）, ConoHa VPS cron。

---

## File Structure

### 新規作成ファイル

```
sales-ops/                              # プロジェクトルート（リポジトリ直下に新設）
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                   # 環境変数ロード
│   │   ├── db.py                       # SQLite接続・スキーマ
│   │   ├── approval_queue.py           # pending/approved/sent 管理
│   │   └── senders/
│   │       ├── __init__.py
│   │       └── gmail_sender.py         # Gmail OAuth + 送信
│   └── tracks/
│       ├── __init__.py
│       └── c_outbound/
│           ├── __init__.py
│           ├── list_builder.py         # Google Maps 企業取得
│           └── personalizer.py         # Claude API でDM下書き生成
├── scripts/
│   ├── init_db.py                      # DB初期化CLI
│   ├── run_list_builder.py             # cron エントリー
│   ├── run_personalizer.py             # cron エントリー
│   ├── run_send_approved.py            # 承認済みを送信するCLI
│   └── gmail_oauth_setup.py            # Gmail OAuth 初回トークン取得
└── tests/
    ├── __init__.py
    ├── conftest.py                     # pytest 共通fixture（tmp DB）
    ├── test_db.py
    ├── test_approval_queue.py
    ├── test_list_builder.py
    ├── test_personalizer.py
    └── test_gmail_sender.py
```

### Claude Code スキル（PC側）

```
.claude/skills/sales-briefing/
├── SKILL.md                            # スキル本体
└── references/
    └── approval-ui.md                  # 承認UIフロー詳細
```

### 設計原則

- `core/` は共通基盤、`tracks/` は軸別パイプライン。Phase 2 で軸A・Bを追加する際に `tracks/` に新フォルダを足すだけで拡張可能
- 各モジュールは単一責任、外部I/O（API呼び出し・ファイル書込）はインジェクト可能にして単体テスト容易化
- `config.py` で環境変数を集約、テストでは monkeypatch で差し替え

---

## Task 1: プロジェクト初期化

**Files:**
- Create: `sales-ops/README.md`
- Create: `sales-ops/requirements.txt`
- Create: `sales-ops/.env.example`
- Create: `sales-ops/.gitignore`
- Create: `sales-ops/src/__init__.py`
- Create: `sales-ops/src/core/__init__.py`
- Create: `sales-ops/src/core/senders/__init__.py`
- Create: `sales-ops/src/tracks/__init__.py`
- Create: `sales-ops/src/tracks/c_outbound/__init__.py`
- Create: `sales-ops/tests/__init__.py`
- Create: `sales-ops/tests/conftest.py`

- [ ] **Step 1: ディレクトリ構造と空パッケージを作成**

Run:
```bash
mkdir -p sales-ops/src/core/senders sales-ops/src/tracks/c_outbound sales-ops/scripts sales-ops/tests
touch sales-ops/src/__init__.py sales-ops/src/core/__init__.py sales-ops/src/core/senders/__init__.py
touch sales-ops/src/tracks/__init__.py sales-ops/src/tracks/c_outbound/__init__.py
touch sales-ops/tests/__init__.py
```

- [ ] **Step 2: requirements.txt 作成**

Create `sales-ops/requirements.txt`:
```
anthropic>=0.40.0
google-api-python-client>=2.100.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0
googlemaps>=4.10.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 3: .env.example 作成**

Create `sales-ops/.env.example`:
```
# Claude API
ANTHROPIC_API_KEY=

# Google Maps Places API (New)
GOOGLE_MAPS_API_KEY=

# Gmail API OAuth
GMAIL_OAUTH_CLIENT_SECRET_JSON=./secrets/gmail_client_secret.json
GMAIL_OAUTH_TOKEN_JSON=./secrets/gmail_token.json
GMAIL_SENDER_ADDRESS=yuichi4107@gmail.com
GMAIL_SENDER_NAME=YN Factory / 山田雄一
GMAIL_REPLY_TO=yuichi4107@gmail.com
GMAIL_UNSUBSCRIBE_URL=https://ynfactory.online/unsubscribe

# DB
SALES_OPS_DB_PATH=/opt/sales-ops/data/sales_ops.db

# 送信制御
SALES_OPS_DRY_RUN=true
SALES_OPS_DAILY_SEND_LIMIT=100
SALES_OPS_SEND_INTERVAL_SEC=60

# オーナー情報（DM差し込み用）
OWNER_NAME=山田雄一
OWNER_COMPANY=YN Factory
OWNER_WEBSITE=https://tools.ynfactory.online
OWNER_BOOK_LINK=https://www.amazon.co.jp/~~~
```

- [ ] **Step 4: .gitignore 作成**

Create `sales-ops/.gitignore`:
```
.env
secrets/
data/
*.db
*.db-journal
__pycache__/
*.pyc
.pytest_cache/
.venv/
```

- [ ] **Step 5: README.md 作成**

Create `sales-ops/README.md`:
```markdown
# Sales OS

営業自律実行システム。3軸（フリーランス/コンテンツ/法人アウトバウンド）の営業オペレーションを自動化する。Phase 1 では軸C（法人アウトバウンド）のMVPを実装。

## セットアップ
```bash
pip install -r requirements.txt
cp .env.example .env  # 値を埋める
python scripts/init_db.py
python scripts/gmail_oauth_setup.py  # 初回のみOAuth承認
```

## cron（VPS本番想定）
- 03:00 `scripts/run_list_builder.py`
- 03:30 `scripts/run_personalizer.py`
- 手動or朝セッション承認後 `scripts/run_send_approved.py`

## テスト
```bash
pytest tests/ -v
```
```

- [ ] **Step 6: tests/conftest.py 作成**

Create `sales-ops/tests/conftest.py`:
```python
import os
import sys
import tempfile
from pathlib import Path

import pytest

# src/ をimportパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def tmp_db_path(tmp_path, monkeypatch):
    """Temp SQLite DB path, isolated per test."""
    db_path = tmp_path / "test_sales_ops.db"
    monkeypatch.setenv("SALES_OPS_DB_PATH", str(db_path))
    return str(db_path)


@pytest.fixture
def env_stub(monkeypatch):
    """共通環境変数を stub する。個別テストで上書き可能。"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "gmap-test-dummy")
    monkeypatch.setenv("GMAIL_SENDER_ADDRESS", "test@example.com")
    monkeypatch.setenv("GMAIL_SENDER_NAME", "テスト送信者")
    monkeypatch.setenv("GMAIL_REPLY_TO", "test@example.com")
    monkeypatch.setenv("GMAIL_UNSUBSCRIBE_URL", "https://example.com/unsub")
    monkeypatch.setenv("OWNER_NAME", "山田雄一")
    monkeypatch.setenv("OWNER_COMPANY", "YN Factory")
    monkeypatch.setenv("OWNER_WEBSITE", "https://tools.ynfactory.online")
    monkeypatch.setenv("SALES_OPS_DRY_RUN", "true")
    monkeypatch.setenv("SALES_OPS_DAILY_SEND_LIMIT", "100")
    monkeypatch.setenv("SALES_OPS_SEND_INTERVAL_SEC", "0")
    return monkeypatch
```

- [ ] **Step 7: コミット**

```bash
git add sales-ops/
git commit -m "feat(sales-ops): Phase 1 プロジェクト初期化（ディレクトリ・依存・conftest）"
```

---

## Task 2: config.py（環境変数ロード）

**Files:**
- Create: `sales-ops/src/core/config.py`
- Create: `sales-ops/tests/test_config.py`

- [ ] **Step 1: テストを先に書く**

Create `sales-ops/tests/test_config.py`:
```python
import pytest
from core.config import Config, MissingEnvError


def test_config_loads_all_required(env_stub):
    cfg = Config.load()
    assert cfg.anthropic_api_key == "sk-test-dummy"
    assert cfg.google_maps_api_key == "gmap-test-dummy"
    assert cfg.gmail_sender_address == "test@example.com"
    assert cfg.owner_name == "山田雄一"
    assert cfg.dry_run is True
    assert cfg.daily_send_limit == 100
    assert cfg.send_interval_sec == 0


def test_config_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingEnvError) as exc:
        Config.load()
    assert "ANTHROPIC_API_KEY" in str(exc.value)


def test_dry_run_defaults_true_when_unset(env_stub):
    env_stub.delenv("SALES_OPS_DRY_RUN", raising=False)
    cfg = Config.load()
    assert cfg.dry_run is True  # 安全側デフォルト
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core'` or similar

- [ ] **Step 3: 最小実装**

Create `sales-ops/src/core/config.py`:
```python
"""Sales OS 環境設定ローダー。DRY_RUN はデフォルトTrueで安全側。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class MissingEnvError(RuntimeError):
    pass


REQUIRED = [
    "ANTHROPIC_API_KEY",
    "GOOGLE_MAPS_API_KEY",
    "GMAIL_SENDER_ADDRESS",
    "GMAIL_SENDER_NAME",
    "OWNER_NAME",
    "OWNER_COMPANY",
    "OWNER_WEBSITE",
]


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    google_maps_api_key: str
    gmail_oauth_client_secret_json: str
    gmail_oauth_token_json: str
    gmail_sender_address: str
    gmail_sender_name: str
    gmail_reply_to: str
    gmail_unsubscribe_url: str
    db_path: str
    dry_run: bool
    daily_send_limit: int
    send_interval_sec: int
    owner_name: str
    owner_company: str
    owner_website: str
    owner_book_link: str

    @classmethod
    def load(cls) -> "Config":
        missing = [k for k in REQUIRED if not os.getenv(k)]
        if missing:
            raise MissingEnvError(f"Missing env vars: {', '.join(missing)}")

        return cls(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            google_maps_api_key=os.environ["GOOGLE_MAPS_API_KEY"],
            gmail_oauth_client_secret_json=os.getenv(
                "GMAIL_OAUTH_CLIENT_SECRET_JSON", "./secrets/gmail_client_secret.json"
            ),
            gmail_oauth_token_json=os.getenv(
                "GMAIL_OAUTH_TOKEN_JSON", "./secrets/gmail_token.json"
            ),
            gmail_sender_address=os.environ["GMAIL_SENDER_ADDRESS"],
            gmail_sender_name=os.environ["GMAIL_SENDER_NAME"],
            gmail_reply_to=os.getenv("GMAIL_REPLY_TO", os.environ["GMAIL_SENDER_ADDRESS"]),
            gmail_unsubscribe_url=os.getenv(
                "GMAIL_UNSUBSCRIBE_URL", "https://ynfactory.online/unsubscribe"
            ),
            db_path=os.getenv("SALES_OPS_DB_PATH", "./data/sales_ops.db"),
            dry_run=os.getenv("SALES_OPS_DRY_RUN", "true").lower() == "true",
            daily_send_limit=int(os.getenv("SALES_OPS_DAILY_SEND_LIMIT", "100")),
            send_interval_sec=int(os.getenv("SALES_OPS_SEND_INTERVAL_SEC", "60")),
            owner_name=os.environ["OWNER_NAME"],
            owner_company=os.environ["OWNER_COMPANY"],
            owner_website=os.environ["OWNER_WEBSITE"],
            owner_book_link=os.getenv("OWNER_BOOK_LINK", ""),
        )
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: コミット**

```bash
git add sales-ops/src/core/config.py sales-ops/tests/test_config.py
git commit -m "feat(sales-ops): Config ローダー実装（必須env検証・DRY_RUN安全デフォルト）"
```

---

## Task 3: db.py（SQLite スキーマ・接続）

**Files:**
- Create: `sales-ops/src/core/db.py`
- Create: `sales-ops/tests/test_db.py`
- Create: `sales-ops/scripts/init_db.py`

- [ ] **Step 1: テストを先に書く**

Create `sales-ops/tests/test_db.py`:
```python
import sqlite3

import pytest

from core.db import Database, init_schema


def test_init_schema_creates_all_tables(tmp_db_path):
    db = Database(tmp_db_path)
    init_schema(db)
    with db.connect() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "approval_queue" in tables
    assert "companies" in tables
    assert "conversations" in tables
    assert "deals" in tables
    assert "daily_kpi" in tables


def test_init_schema_is_idempotent(tmp_db_path):
    db = Database(tmp_db_path)
    init_schema(db)
    init_schema(db)  # 2回目もエラーなし
    with db.connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
    assert count >= 5


def test_companies_unique_website(tmp_db_path):
    db = Database(tmp_db_path)
    init_schema(db)
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO companies (source, segment, company_name, website_url) "
            "VALUES ('google_maps', 't2_pro_service', 'A社', 'https://a.example.com')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO companies (source, segment, company_name, website_url) "
                "VALUES ('google_maps', 't2_pro_service', 'A社別', 'https://a.example.com')"
            )


def test_approval_queue_status_constraint(tmp_db_path):
    db = Database(tmp_db_path)
    init_schema(db)
    with db.connect() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO approval_queue (track, item_type, payload_json, status) "
                "VALUES ('c', 'dm', '{}', 'invalid_status')"
            )
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.db'`

- [ ] **Step 3: 実装**

Create `sales-ops/src/core/db.py`:
```python
"""SQLite 接続と初期スキーマ。DBファイルはローカル配置（Google Drive配下禁止）。"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS approval_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track TEXT NOT NULL CHECK(track IN ('a', 'b', 'c')),
    item_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'approved', 'rejected', 'sent', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_queue_status ON approval_queue(status, track);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL CHECK(source IN ('google_maps', 'biz_db', 'manual')),
    segment TEXT NOT NULL CHECK(segment IN ('t1_sme', 't2_pro_service')),
    company_name TEXT NOT NULL,
    website_url TEXT UNIQUE NOT NULL,
    contact_email TEXT,
    industry TEXT,
    size_employees INTEGER,
    location TEXT,
    hp_summary TEXT,
    personalization_hints TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    direction TEXT NOT NULL CHECK(direction IN ('outbound', 'inbound')),
    subject TEXT,
    body TEXT,
    gmail_message_id TEXT,
    sent_at TIMESTAMP,
    received_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conv_company ON conversations(company_id);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    stage TEXT NOT NULL CHECK(stage IN ('lead', 'qualified', 'proposal', 'won', 'lost')),
    offer TEXT,
    amount_yen INTEGER,
    stage_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_kpi (
    date DATE NOT NULL,
    track TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (date, track, metric)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_schema(db: Database) -> None:
    with db.connect() as conn:
        conn.executescript(SCHEMA_SQL)
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_db.py -v`
Expected: 4 passed

- [ ] **Step 5: init_db.py CLIスクリプト作成**

Create `sales-ops/scripts/init_db.py`:
```python
"""DB初期化CLI: `python scripts/init_db.py` でスキーマ作成。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv

from core.config import Config
from core.db import Database, init_schema


def main() -> int:
    load_dotenv()
    cfg = Config.load()
    db = Database(cfg.db_path)
    init_schema(db)
    print(f"[OK] schema initialized at {cfg.db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: コミット**

```bash
git add sales-ops/src/core/db.py sales-ops/tests/test_db.py sales-ops/scripts/init_db.py
git commit -m "feat(sales-ops): SQLiteスキーマ（approval_queue/companies/conversations/deals/daily_kpi）"
```

---

## Task 4: approval_queue.py（キュー管理）

**Files:**
- Create: `sales-ops/src/core/approval_queue.py`
- Create: `sales-ops/tests/test_approval_queue.py`

- [ ] **Step 1: テストを先に書く**

Create `sales-ops/tests/test_approval_queue.py`:
```python
import json

import pytest

from core.approval_queue import ApprovalQueue, ItemNotFound, InvalidTransition
from core.db import Database, init_schema


@pytest.fixture
def queue(tmp_db_path):
    db = Database(tmp_db_path)
    init_schema(db)
    return ApprovalQueue(db)


def test_enqueue_returns_id_and_is_pending(queue):
    item_id = queue.enqueue(track="c", item_type="dm", payload={"to": "a@b.com", "body": "hi"})
    assert isinstance(item_id, int) and item_id > 0

    items = queue.list_pending(track="c")
    assert len(items) == 1
    assert items[0]["id"] == item_id
    assert items[0]["status"] == "pending"
    assert json.loads(items[0]["payload_json"])["to"] == "a@b.com"


def test_approve_transitions_pending_to_approved(queue):
    item_id = queue.enqueue(track="c", item_type="dm", payload={"to": "a@b.com"})
    queue.approve(item_id)

    item = queue.get(item_id)
    assert item["status"] == "approved"
    assert item["approved_at"] is not None


def test_reject_marks_status(queue):
    item_id = queue.enqueue(track="c", item_type="dm", payload={"to": "a@b.com"})
    queue.reject(item_id)
    assert queue.get(item_id)["status"] == "rejected"


def test_mark_sent_only_from_approved(queue):
    item_id = queue.enqueue(track="c", item_type="dm", payload={"to": "a@b.com"})
    with pytest.raises(InvalidTransition):
        queue.mark_sent(item_id, gmail_message_id="abc")
    queue.approve(item_id)
    queue.mark_sent(item_id, gmail_message_id="abc")
    assert queue.get(item_id)["status"] == "sent"


def test_mark_failed_records_error(queue):
    item_id = queue.enqueue(track="c", item_type="dm", payload={"to": "a@b.com"})
    queue.approve(item_id)
    queue.mark_failed(item_id, "SMTP timeout")
    item = queue.get(item_id)
    assert item["status"] == "failed"
    assert item["error_message"] == "SMTP timeout"


def test_get_raises_when_missing(queue):
    with pytest.raises(ItemNotFound):
        queue.get(999)


def test_list_approved_returns_only_approved(queue):
    a = queue.enqueue(track="c", item_type="dm", payload={})
    b = queue.enqueue(track="c", item_type="dm", payload={})
    queue.approve(a)
    # b は pending のまま

    approved = queue.list_approved(track="c")
    assert [i["id"] for i in approved] == [a]


def test_auto_reject_stale_pending(queue, monkeypatch):
    """48時間経過した pending を自動 reject"""
    import datetime as dt

    item_id = queue.enqueue(track="c", item_type="dm", payload={})
    # created_at を手動で48時間前に書き換え
    with queue.db.connect() as conn:
        conn.execute(
            "UPDATE approval_queue SET created_at = ? WHERE id = ?",
            ((dt.datetime.utcnow() - dt.timedelta(hours=49)).isoformat(), item_id),
        )

    rejected_count = queue.auto_reject_stale(max_age_hours=48)
    assert rejected_count == 1
    assert queue.get(item_id)["status"] == "rejected"
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_approval_queue.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.approval_queue'`

- [ ] **Step 3: 実装**

Create `sales-ops/src/core/approval_queue.py`:
```python
"""Approval キュー: pending → approved/rejected → sent/failed のステート管理。"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from .db import Database


class ItemNotFound(KeyError):
    pass


class InvalidTransition(RuntimeError):
    pass


class ApprovalQueue:
    def __init__(self, db: Database):
        self.db = db

    def enqueue(self, *, track: str, item_type: str, payload: dict[str, Any]) -> int:
        with self.db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO approval_queue (track, item_type, payload_json, status) "
                "VALUES (?, ?, ?, 'pending')",
                (track, item_type, json.dumps(payload, ensure_ascii=False)),
            )
            return cur.lastrowid

    def get(self, item_id: int) -> dict[str, Any]:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM approval_queue WHERE id = ?", (item_id,)
            ).fetchone()
        if row is None:
            raise ItemNotFound(item_id)
        return dict(row)

    def list_pending(self, *, track: str | None = None) -> list[dict[str, Any]]:
        return self._list_by_status("pending", track=track)

    def list_approved(self, *, track: str | None = None) -> list[dict[str, Any]]:
        return self._list_by_status("approved", track=track)

    def _list_by_status(self, status: str, *, track: str | None) -> list[dict[str, Any]]:
        q = "SELECT * FROM approval_queue WHERE status = ?"
        args: list[Any] = [status]
        if track is not None:
            q += " AND track = ?"
            args.append(track)
        q += " ORDER BY created_at ASC"
        with self.db.connect() as conn:
            return [dict(r) for r in conn.execute(q, args).fetchall()]

    def approve(self, item_id: int) -> None:
        self._transition(item_id, from_status="pending", to_status="approved",
                         ts_column="approved_at")

    def reject(self, item_id: int) -> None:
        self._transition(item_id, from_status="pending", to_status="rejected",
                         ts_column=None)

    def mark_sent(self, item_id: int, *, gmail_message_id: str | None = None) -> None:
        self._transition(item_id, from_status="approved", to_status="sent",
                         ts_column="sent_at", extra_payload={"gmail_message_id": gmail_message_id})

    def mark_failed(self, item_id: int, error_message: str) -> None:
        self._transition(item_id, from_status="approved", to_status="failed",
                         ts_column=None, error_message=error_message)

    def _transition(
        self,
        item_id: int,
        *,
        from_status: str,
        to_status: str,
        ts_column: str | None,
        error_message: str | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        item = self.get(item_id)
        if item["status"] != from_status:
            raise InvalidTransition(
                f"Cannot transition {item['status']} -> {to_status}"
            )

        sets = ["status = ?"]
        args: list[Any] = [to_status]
        if ts_column:
            sets.append(f"{ts_column} = ?")
            args.append(dt.datetime.utcnow().isoformat())
        if error_message is not None:
            sets.append("error_message = ?")
            args.append(error_message)
        if extra_payload:
            # payload_json に gmail_message_id などを追記
            payload = json.loads(item["payload_json"])
            payload.update(extra_payload)
            sets.append("payload_json = ?")
            args.append(json.dumps(payload, ensure_ascii=False))
        args.append(item_id)

        with self.db.connect() as conn:
            conn.execute(
                f"UPDATE approval_queue SET {', '.join(sets)} WHERE id = ?", args
            )

    def auto_reject_stale(self, *, max_age_hours: int = 48) -> int:
        cutoff = (dt.datetime.utcnow() - dt.timedelta(hours=max_age_hours)).isoformat()
        with self.db.connect() as conn:
            cur = conn.execute(
                "UPDATE approval_queue SET status = 'rejected' "
                "WHERE status = 'pending' AND created_at < ?",
                (cutoff,),
            )
            return cur.rowcount
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_approval_queue.py -v`
Expected: 8 passed

- [ ] **Step 5: コミット**

```bash
git add sales-ops/src/core/approval_queue.py sales-ops/tests/test_approval_queue.py
git commit -m "feat(sales-ops): ApprovalQueue（pending/approved/sent/failed ステートマシン）"
```

---

## Task 5: list_builder.py（Google Maps企業リスト取得）

**Files:**
- Create: `sales-ops/src/tracks/c_outbound/list_builder.py`
- Create: `sales-ops/tests/test_list_builder.py`
- Create: `sales-ops/scripts/run_list_builder.py`

- [ ] **Step 1: テストを先に書く（Google Maps API はモック）**

Create `sales-ops/tests/test_list_builder.py`:
```python
from unittest.mock import MagicMock

import pytest

from core.db import Database, init_schema
from tracks.c_outbound.list_builder import ListBuilder, T2_SEARCH_QUERIES


@pytest.fixture
def db(tmp_db_path):
    d = Database(tmp_db_path)
    init_schema(d)
    return d


def _make_mock_gmaps(places):
    gmaps = MagicMock()
    gmaps.places_nearby.return_value = {"results": places}
    # 各 place_id に対して詳細を返す
    details_map = {p["place_id"]: {"result": p} for p in places}
    gmaps.place.side_effect = lambda place_id, fields=None: details_map[place_id]
    return gmaps


def test_fetch_t2_inserts_new_companies(db):
    fake_places = [
        {
            "place_id": "pid_a",
            "name": "A税理士事務所",
            "website": "https://a-tax.example.com",
            "formatted_address": "東京都千代田区1-1",
            "types": ["accounting", "point_of_interest"],
        },
        {
            "place_id": "pid_b",
            "name": "B社労士事務所",
            "website": "https://b-sr.example.com",
            "formatted_address": "東京都新宿区2-2",
            "types": ["lawyer", "point_of_interest"],
        },
    ]
    builder = ListBuilder(db=db, gmaps_client=_make_mock_gmaps(fake_places))
    inserted = builder.fetch_t2(query="税理士 東京", location=(35.68, 139.76), max_results=10)

    assert inserted == 2
    with db.connect() as conn:
        rows = conn.execute("SELECT company_name, website_url, segment FROM companies").fetchall()
    assert len(rows) == 2
    assert {r["company_name"] for r in rows} == {"A税理士事務所", "B社労士事務所"}
    assert all(r["segment"] == "t2_pro_service" for r in rows)


def test_fetch_t2_skips_duplicates(db):
    fake_places = [
        {
            "place_id": "pid_a",
            "name": "A税理士事務所",
            "website": "https://a-tax.example.com",
            "formatted_address": "東京都",
            "types": ["accounting"],
        }
    ]
    builder = ListBuilder(db=db, gmaps_client=_make_mock_gmaps(fake_places))
    first = builder.fetch_t2(query="税理士", location=(35.68, 139.76), max_results=10)
    second = builder.fetch_t2(query="税理士", location=(35.68, 139.76), max_results=10)

    assert first == 1
    assert second == 0  # 重複スキップ


def test_fetch_t2_skips_without_website(db):
    fake_places = [
        {
            "place_id": "pid_a",
            "name": "HP無し事務所",
            "formatted_address": "東京都",
            "types": ["accounting"],
            # website 無し
        }
    ]
    builder = ListBuilder(db=db, gmaps_client=_make_mock_gmaps(fake_places))
    assert builder.fetch_t2(query="税理士", location=(35.68, 139.76), max_results=10) == 0


def test_t2_search_queries_covers_core_segments():
    joined = " | ".join(T2_SEARCH_QUERIES)
    for must in ["税理士", "社労士", "行政書士", "司法書士", "デザイン", "ウェブ制作"]:
        assert must in joined
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_list_builder.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 実装**

Create `sales-ops/src/tracks/c_outbound/list_builder.py`:
```python
"""Google Maps Places API からT2セグメント（士業・制作会社）のリストを取得する。"""
from __future__ import annotations

import logging
from typing import Iterable

from core.db import Database

logger = logging.getLogger(__name__)


T2_SEARCH_QUERIES = [
    "税理士事務所",
    "社労士事務所",
    "行政書士事務所",
    "司法書士事務所",
    "弁護士事務所",
    "会計事務所",
    "ウェブ制作会社",
    "デザイン事務所",
    "広告代理店",
    "コンサルティング会社",
]


class ListBuilder:
    def __init__(self, db: Database, gmaps_client):
        self.db = db
        self.gmaps = gmaps_client

    def fetch_t2(
        self,
        *,
        query: str,
        location: tuple[float, float],
        max_results: int = 20,
        radius_m: int = 5000,
    ) -> int:
        """`query` で Places Text Search を行い、DBに新規登録した件数を返す。"""
        results = self._search(query=query, location=location, radius_m=radius_m)

        inserted = 0
        for place in results[:max_results]:
            website = place.get("website")
            if not website:
                # 詳細問い合わせで website が取れるケースもあるので再試行
                detail = self.gmaps.place(place["place_id"], fields=["website"])
                website = detail.get("result", {}).get("website")
            if not website:
                continue
            if self._insert(
                name=place.get("name", ""),
                website=website,
                address=place.get("formatted_address", ""),
                industry=self._infer_industry(place.get("types", [])),
            ):
                inserted += 1
        logger.info("fetch_t2: query=%s inserted=%d/%d", query, inserted, len(results))
        return inserted

    def _search(self, *, query: str, location: tuple[float, float], radius_m: int) -> list[dict]:
        resp = self.gmaps.places_nearby(
            location=location, radius=radius_m, keyword=query, language="ja"
        )
        return resp.get("results", [])

    def _insert(self, *, name: str, website: str, address: str, industry: str) -> bool:
        try:
            with self.db.connect() as conn:
                conn.execute(
                    "INSERT INTO companies (source, segment, company_name, website_url, "
                    "location, industry) VALUES ('google_maps', 't2_pro_service', ?, ?, ?, ?)",
                    (name, website, address, industry),
                )
            return True
        except Exception as e:
            if "UNIQUE" in str(e):
                return False
            raise

    @staticmethod
    def _infer_industry(types: Iterable[str]) -> str:
        types_set = set(types)
        if "lawyer" in types_set:
            return "lawyer"
        if "accounting" in types_set:
            return "accounting"
        return ",".join(sorted(types_set))[:200]
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_list_builder.py -v`
Expected: 4 passed

- [ ] **Step 5: cronエントリー作成**

Create `sales-ops/scripts/run_list_builder.py`:
```python
"""cron: 毎日03:00 に実行。T2セグメントの企業リストを取得する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import googlemaps
from dotenv import load_dotenv

from core.config import Config
from core.db import Database
from tracks.c_outbound.list_builder import ListBuilder, T2_SEARCH_QUERIES


# 東京・大阪・名古屋の中心座標（半径5kmで検索）
TARGET_LOCATIONS = [
    ("東京", (35.6812, 139.7671)),
    ("大阪", (34.6937, 135.5023)),
    ("名古屋", (35.1815, 136.9066)),
]


def main() -> int:
    load_dotenv()
    cfg = Config.load()
    db = Database(cfg.db_path)
    gmaps = googlemaps.Client(key=cfg.google_maps_api_key)
    builder = ListBuilder(db=db, gmaps_client=gmaps)

    total = 0
    for region_name, loc in TARGET_LOCATIONS:
        for q in T2_SEARCH_QUERIES:
            n = builder.fetch_t2(query=f"{q} {region_name}", location=loc, max_results=5)
            total += n
    print(f"[OK] fetched {total} new T2 companies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: コミット**

```bash
git add sales-ops/src/tracks/c_outbound/list_builder.py sales-ops/tests/test_list_builder.py sales-ops/scripts/run_list_builder.py
git commit -m "feat(sales-ops): Google Maps T2企業リスト取得（税理士/社労士/制作会社等10業種）"
```

---

## Task 6: personalizer.py（Claude APIでDM下書き生成）

**Files:**
- Create: `sales-ops/src/tracks/c_outbound/personalizer.py`
- Create: `sales-ops/tests/test_personalizer.py`
- Create: `sales-ops/scripts/run_personalizer.py`

- [ ] **Step 1: テストを先に書く（Claude API はモック）**

Create `sales-ops/tests/test_personalizer.py`:
```python
import json
from unittest.mock import MagicMock

import pytest

from core.approval_queue import ApprovalQueue
from core.db import Database, init_schema
from tracks.c_outbound.personalizer import Personalizer


@pytest.fixture
def db(tmp_db_path):
    d = Database(tmp_db_path)
    init_schema(d)
    # 新規企業を1件登録
    with d.connect() as conn:
        conn.execute(
            "INSERT INTO companies (source, segment, company_name, website_url, "
            "industry, status) VALUES ('google_maps', 't2_pro_service', "
            "'A税理士事務所', 'https://a-tax.example.com', 'accounting', 'new')"
        )
    return d


def _mock_claude(response_json: dict):
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps(response_json, ensure_ascii=False))]
    client.messages.create.return_value = resp
    return client


def _mock_http_fetch(text: str = "当事務所は中小企業の経営支援に注力しています"):
    fetcher = MagicMock()
    fetcher.fetch_summary.return_value = text
    return fetcher


def test_personalize_inserts_pending_dm(db, env_stub):
    claude = _mock_claude({
        "subject": "A税理士事務所 様 — 顧問先の業務自動化ツールのご案内",
        "body": "山田と申します。貴事務所のHPで中小企業支援に注力されている旨を拝見し……",
        "personalization_hint": "中小企業支援",
    })
    fetcher = _mock_http_fetch()
    p = Personalizer(db=db, claude_client=claude, hp_fetcher=fetcher, model="claude-opus-4-7")

    processed = p.process_new_companies(batch_size=10)
    assert processed == 1

    queue = ApprovalQueue(db)
    items = queue.list_pending(track="c")
    assert len(items) == 1
    payload = json.loads(items[0]["payload_json"])
    assert "A税理士事務所" in payload["subject"]
    assert payload["to_company_id"] is not None


def test_personalize_updates_company_status(db, env_stub):
    claude = _mock_claude({
        "subject": "件名",
        "body": "本文",
        "personalization_hint": "ヒント",
    })
    p = Personalizer(db=db, claude_client=claude, hp_fetcher=_mock_http_fetch())
    p.process_new_companies(batch_size=10)

    with db.connect() as conn:
        row = conn.execute("SELECT status FROM companies").fetchone()
    assert row["status"] == "drafted"


def test_personalize_blocks_unfilled_placeholders(db, env_stub):
    # Claude が差込変数を残したまま返した場合はブロック
    claude = _mock_claude({
        "subject": "{{company_name}} 様 — オファー",  # 未展開
        "body": "本文",
        "personalization_hint": "",
    })
    p = Personalizer(db=db, claude_client=claude, hp_fetcher=_mock_http_fetch())
    processed = p.process_new_companies(batch_size=10)

    # ブロックされてキューには入らない
    queue = ApprovalQueue(db)
    assert queue.list_pending(track="c") == []
    # 企業ステータスは needs_retry
    with db.connect() as conn:
        row = conn.execute("SELECT status FROM companies").fetchone()
    assert row["status"] == "needs_retry"


def test_personalize_skips_when_no_new_companies(db, env_stub):
    with db.connect() as conn:
        conn.execute("UPDATE companies SET status = 'drafted'")
    p = Personalizer(db=db, claude_client=_mock_claude({}), hp_fetcher=_mock_http_fetch())
    assert p.process_new_companies(batch_size=10) == 0
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_personalizer.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 実装**

Create `sales-ops/src/tracks/c_outbound/personalizer.py`:
```python
"""企業HPを読み取り、Claude APIでパーソナライズDM下書きを生成する。"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from core.approval_queue import ApprovalQueue
from core.db import Database

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """あなたはBtoB向けのインサイドセールス専門コピーライターです。
以下の企業に対して、yn-tools（AI業務自動化ツール31種類、月2000円/ユーザー、tools.ynfactory.online）を提案するパーソナライズメールを1通作成してください。

企業情報:
- 会社名: {company_name}
- 業種: {industry}
- HP要約: {hp_summary}

制約:
1. 件名は30文字以内、相手の会社名を含める
2. 本文は400-600字、冒頭で相手HPから読み取った具体的要素を1つ触れる（パーソナライズ）
3. 自動化の具体的な業務例を業種に合わせて2-3個提示
4. 最後に14日間の無料トライアル案内と30分オンラインデモ提案
5. 送信者情報と配信停止手順を末尾に記載
6. 絶対に {{}} プレースホルダや [xxx] を残さない、全て実文字で埋める
7. 過度にフォーマルすぎない、「はじめまして、〜と申します」程度の自然な日本語

JSON 形式で返答してください。他の文字を出力してはいけません:
{{
  "subject": "件名",
  "body": "本文（改行は \\n）",
  "personalization_hint": "HPから読み取った要素の要約30字"
}}
"""


PLACEHOLDER_PATTERNS = [
    re.compile(r"\{\{[^}]+\}\}"),
    re.compile(r"\[[A-Z_]+\]"),
    re.compile(r"<[a-z_]+>"),
]


class Personalizer:
    def __init__(
        self,
        db: Database,
        claude_client,
        hp_fetcher,
        *,
        model: str = "claude-opus-4-7",
    ):
        self.db = db
        self.claude = claude_client
        self.hp_fetcher = hp_fetcher
        self.model = model
        self.queue = ApprovalQueue(db)

    def process_new_companies(self, *, batch_size: int = 50) -> int:
        companies = self._list_new_companies(limit=batch_size)
        processed = 0
        for c in companies:
            ok = self._process_one(c)
            self._update_status(c["id"], "drafted" if ok else "needs_retry")
            if ok:
                processed += 1
        return processed

    def _list_new_companies(self, *, limit: int) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM companies WHERE status = 'new' ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def _process_one(self, company: dict[str, Any]) -> bool:
        hp_summary = ""
        if company.get("website_url"):
            try:
                hp_summary = self.hp_fetcher.fetch_summary(company["website_url"])
            except Exception as e:
                logger.warning("hp_fetcher failed for %s: %s", company["website_url"], e)

        prompt = PROMPT_TEMPLATE.format(
            company_name=company["company_name"],
            industry=company.get("industry") or "不明",
            hp_summary=hp_summary or "HPが取得できませんでした",
        )
        resp = self.claude.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text if resp.content else "{}"
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("claude returned non-json for company %s", company["id"])
            return False

        subject = data.get("subject", "")
        body = data.get("body", "")

        if self._has_unfilled_placeholders(subject) or self._has_unfilled_placeholders(body):
            logger.warning(
                "unfilled placeholders in draft for company %s: subject=%r",
                company["id"], subject,
            )
            return False

        # HP要約があれば companies テーブルにも保存
        if hp_summary:
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE companies SET hp_summary = ?, personalization_hints = ? WHERE id = ?",
                    (hp_summary[:2000], data.get("personalization_hint", ""), company["id"]),
                )

        self.queue.enqueue(
            track="c",
            item_type="dm",
            payload={
                "to_company_id": company["id"],
                "to_website": company["website_url"],
                "subject": subject,
                "body": body,
                "personalization_hint": data.get("personalization_hint", ""),
            },
        )
        return True

    def _update_status(self, company_id: int, status: str) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE companies SET status = ? WHERE id = ?", (status, company_id)
            )

    @staticmethod
    def _has_unfilled_placeholders(text: str) -> bool:
        return any(p.search(text) for p in PLACEHOLDER_PATTERNS)
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_personalizer.py -v`
Expected: 4 passed

- [ ] **Step 5: cronエントリー作成（HTTP fetcherは最小実装）**

Create `sales-ops/scripts/run_personalizer.py`:
```python
"""cron: 毎日03:30 に実行。new 企業のDM下書きを生成して approval_queue に投入する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anthropic
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from core.config import Config
from core.db import Database
from tracks.c_outbound.personalizer import Personalizer


class SimpleHPFetcher:
    """シンプルなHP要約: <title> + <meta description> + <body> 先頭400字"""

    def fetch_summary(self, url: str) -> str:
        try:
            r = requests.get(
                url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0 SalesOps/1.0"},
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc = desc_tag.get("content", "") if desc_tag else ""
            body = soup.get_text(" ", strip=True)[:400] if soup.body else ""
            return f"{title} / {desc} / {body}".strip()
        except Exception:
            return ""


def main() -> int:
    load_dotenv()
    cfg = Config.load()
    db = Database(cfg.db_path)
    claude = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    personalizer = Personalizer(db=db, claude_client=claude, hp_fetcher=SimpleHPFetcher())
    processed = personalizer.process_new_companies(batch_size=50)
    print(f"[OK] drafted {processed} DMs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Then add `requests` and `beautifulsoup4` to `requirements.txt`:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
```

- [ ] **Step 6: コミット**

```bash
git add sales-ops/src/tracks/c_outbound/personalizer.py sales-ops/tests/test_personalizer.py sales-ops/scripts/run_personalizer.py sales-ops/requirements.txt
git commit -m "feat(sales-ops): Personalizer（Claude API でDM下書き生成+プレースホルダ検知）"
```

---

## Task 7: gmail_sender.py（Gmail API送信）

**Files:**
- Create: `sales-ops/src/core/senders/gmail_sender.py`
- Create: `sales-ops/tests/test_gmail_sender.py`
- Create: `sales-ops/scripts/gmail_oauth_setup.py`
- Create: `sales-ops/scripts/run_send_approved.py`

- [ ] **Step 1: テストを先に書く（Gmail API は Service モック）**

Create `sales-ops/tests/test_gmail_sender.py`:
```python
import base64
import json
from unittest.mock import MagicMock

import pytest

from core.approval_queue import ApprovalQueue
from core.db import Database, init_schema
from core.senders.gmail_sender import GmailSender, build_raw_email, DailyLimitReached


@pytest.fixture
def db(tmp_db_path):
    d = Database(tmp_db_path)
    init_schema(d)
    with d.connect() as conn:
        conn.execute(
            "INSERT INTO companies (source, segment, company_name, website_url, "
            "contact_email, status) VALUES ('google_maps', 't2_pro_service', "
            "'A税理士', 'https://a.example.com', 'contact@a.example.com', 'drafted')"
        )
    return d


def _enqueue_approved(db, body="本文です", subject="テスト件名", to_company_id=1):
    q = ApprovalQueue(db)
    item_id = q.enqueue(track="c", item_type="dm", payload={
        "to_company_id": to_company_id,
        "subject": subject,
        "body": body,
    })
    q.approve(item_id)
    return item_id


def test_build_raw_email_includes_required_headers():
    raw = build_raw_email(
        sender_name="YN Factory",
        sender_address="me@example.com",
        reply_to="me@example.com",
        to_address="you@example.com",
        subject="件名",
        body_text="本文",
        unsubscribe_url="https://example.com/unsub",
    )
    decoded = base64.urlsafe_b64decode(raw.encode()).decode("utf-8", errors="replace")
    assert "From: YN Factory <me@example.com>" in decoded
    assert "To: you@example.com" in decoded
    assert "Subject: =?utf-8?" in decoded  # MIMEエンコード
    assert "Reply-To: me@example.com" in decoded
    assert "List-Unsubscribe: <https://example.com/unsub>" in decoded


def test_sender_dry_run_does_not_call_api(db, env_stub):
    service = MagicMock()
    sender = GmailSender(
        db=db, gmail_service=service,
        sender_name="YN Factory", sender_address="me@example.com",
        reply_to="me@example.com", unsubscribe_url="https://example.com/unsub",
        dry_run=True, send_interval_sec=0, daily_limit=100,
    )

    item_id = _enqueue_approved(db)
    sender.send_all_approved(track="c")

    service.users().messages().send.assert_not_called()
    q = ApprovalQueue(db)
    assert q.get(item_id)["status"] == "sent"  # dry_runでもsent扱い（動作確認のため）


def test_sender_live_calls_api_and_marks_sent(db, env_stub):
    service = MagicMock()
    service.users().messages().send().execute.return_value = {"id": "gmail_msg_xyz"}

    sender = GmailSender(
        db=db, gmail_service=service,
        sender_name="YN Factory", sender_address="me@example.com",
        reply_to="me@example.com", unsubscribe_url="https://example.com/unsub",
        dry_run=False, send_interval_sec=0, daily_limit=100,
    )

    item_id = _enqueue_approved(db)
    sender.send_all_approved(track="c")

    q = ApprovalQueue(db)
    item = q.get(item_id)
    assert item["status"] == "sent"
    payload = json.loads(item["payload_json"])
    assert payload["gmail_message_id"] == "gmail_msg_xyz"


def test_sender_respects_daily_limit(db, env_stub):
    service = MagicMock()
    service.users().messages().send().execute.return_value = {"id": "msg"}
    sender = GmailSender(
        db=db, gmail_service=service,
        sender_name="YN", sender_address="me@example.com",
        reply_to="me@example.com", unsubscribe_url="https://example.com/unsub",
        dry_run=False, send_interval_sec=0, daily_limit=1,
    )

    _enqueue_approved(db)
    _enqueue_approved(db, to_company_id=1)  # 同じ company_id で2件目

    with pytest.raises(DailyLimitReached):
        sender.send_all_approved(track="c")


def test_sender_blocks_when_company_has_no_email(db, env_stub):
    # contact_email を NULL にしてしまう
    with db.connect() as conn:
        conn.execute("UPDATE companies SET contact_email = NULL WHERE id = 1")

    service = MagicMock()
    sender = GmailSender(
        db=db, gmail_service=service,
        sender_name="YN", sender_address="me@example.com",
        reply_to="me@example.com", unsubscribe_url="https://example.com/unsub",
        dry_run=False, send_interval_sec=0, daily_limit=100,
    )

    item_id = _enqueue_approved(db)
    sender.send_all_approved(track="c")

    q = ApprovalQueue(db)
    item = q.get(item_id)
    assert item["status"] == "failed"
    assert "contact_email" in (item["error_message"] or "")
```

- [ ] **Step 2: テストを走らせて失敗を確認**

Run: `cd sales-ops && pytest tests/test_gmail_sender.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 実装**

Create `sales-ops/src/core/senders/gmail_sender.py`:
```python
"""Gmail API 経由でDM送信。承認済みキューから順次送信、日次上限・送信間隔を制御。"""
from __future__ import annotations

import base64
import datetime as dt
import json
import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from core.approval_queue import ApprovalQueue
from core.db import Database

logger = logging.getLogger(__name__)


class DailyLimitReached(RuntimeError):
    pass


def build_raw_email(
    *,
    sender_name: str,
    sender_address: str,
    reply_to: str,
    to_address: str,
    subject: str,
    body_text: str,
    unsubscribe_url: str,
) -> str:
    """Gmail API 用の base64url エンコード済み raw メッセージを構築する。"""
    footer = (
        f"\n\n---\n{sender_name}\n{sender_address}\n"
        f"\n※配信停止をご希望の場合はこちら: {unsubscribe_url}\n"
        "※本メールは事業者様向けのご案内としてお送りしております。"
    )
    full_body = body_text.rstrip() + footer

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{sender_address}>"
    msg["To"] = to_address
    msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    msg.attach(MIMEText(full_body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return raw


class GmailSender:
    def __init__(
        self,
        db: Database,
        gmail_service,
        *,
        sender_name: str,
        sender_address: str,
        reply_to: str,
        unsubscribe_url: str,
        dry_run: bool,
        send_interval_sec: int,
        daily_limit: int,
    ):
        self.db = db
        self.service = gmail_service
        self.sender_name = sender_name
        self.sender_address = sender_address
        self.reply_to = reply_to
        self.unsubscribe_url = unsubscribe_url
        self.dry_run = dry_run
        self.send_interval_sec = send_interval_sec
        self.daily_limit = daily_limit
        self.queue = ApprovalQueue(db)

    def send_all_approved(self, *, track: str) -> int:
        sent_today = self._count_sent_today()
        sent_now = 0

        for item in self.queue.list_approved(track=track):
            if sent_today + sent_now >= self.daily_limit:
                raise DailyLimitReached(
                    f"daily limit {self.daily_limit} reached (today={sent_today}, now={sent_now})"
                )

            try:
                self._send_one(item)
                sent_now += 1
                if self.send_interval_sec > 0:
                    time.sleep(self.send_interval_sec)
            except _SendBlocked as e:
                self.queue.mark_failed(item["id"], str(e))
            except Exception as e:
                logger.exception("gmail send failed for item %s", item["id"])
                self.queue.mark_failed(item["id"], f"{type(e).__name__}: {e}")
        return sent_now

    def _send_one(self, item: dict[str, Any]) -> None:
        payload = json.loads(item["payload_json"])
        company_id = payload.get("to_company_id")
        if company_id is None:
            raise _SendBlocked("payload missing to_company_id")

        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT contact_email FROM companies WHERE id = ?", (company_id,)
            ).fetchone()
        if row is None or not row["contact_email"]:
            raise _SendBlocked("company has no contact_email")

        raw = build_raw_email(
            sender_name=self.sender_name,
            sender_address=self.sender_address,
            reply_to=self.reply_to,
            to_address=row["contact_email"],
            subject=payload["subject"],
            body_text=payload["body"],
            unsubscribe_url=self.unsubscribe_url,
        )

        if self.dry_run:
            logger.info("[DRY_RUN] would send item %s to %s", item["id"], row["contact_email"])
            self.queue.mark_sent(item["id"], gmail_message_id="dry_run")
            return

        resp = (
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        self.queue.mark_sent(item["id"], gmail_message_id=resp.get("id"))

    def _count_sent_today(self) -> int:
        today = dt.datetime.utcnow().date().isoformat()
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM approval_queue "
                "WHERE status = 'sent' AND DATE(sent_at) = ?",
                (today,),
            ).fetchone()
        return row["c"] if row else 0


class _SendBlocked(RuntimeError):
    pass
```

- [ ] **Step 4: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_gmail_sender.py -v`
Expected: 5 passed

- [ ] **Step 5: OAuth初回セットアップCLI**

Create `sales-ops/scripts/gmail_oauth_setup.py`:
```python
"""初回だけ実行: ブラウザで OAuth 承認して token.json を保存する。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from core.config import Config


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main() -> int:
    load_dotenv()
    cfg = Config.load()
    client_secret = Path(cfg.gmail_oauth_client_secret_json)
    if not client_secret.exists():
        print(f"[ERR] {client_secret} not found. Google Cloud Console からOAuthクライアント作成→JSONダウンロードしてください。")
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = Path(cfg.gmail_oauth_token_json)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"[OK] token saved to {token_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: 送信CLI（承認済み一斉送信）**

Create `sales-ops/scripts/run_send_approved.py`:
```python
"""承認済みの approval_queue を送信する（朝セッション承認後に起動）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from core.config import Config
from core.db import Database
from core.senders.gmail_sender import GmailSender

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main() -> int:
    load_dotenv()
    cfg = Config.load()
    creds = Credentials.from_authorized_user_file(cfg.gmail_oauth_token_json, SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    db = Database(cfg.db_path)
    sender = GmailSender(
        db=db,
        gmail_service=service,
        sender_name=cfg.gmail_sender_name,
        sender_address=cfg.gmail_sender_address,
        reply_to=cfg.gmail_reply_to,
        unsubscribe_url=cfg.gmail_unsubscribe_url,
        dry_run=cfg.dry_run,
        send_interval_sec=cfg.send_interval_sec,
        daily_limit=cfg.daily_send_limit,
    )
    sent = sender.send_all_approved(track="c")
    print(f"[OK] sent {sent} emails (dry_run={cfg.dry_run})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7: コミット**

```bash
git add sales-ops/src/core/senders/gmail_sender.py sales-ops/tests/test_gmail_sender.py sales-ops/scripts/gmail_oauth_setup.py sales-ops/scripts/run_send_approved.py
git commit -m "feat(sales-ops): GmailSender（OAuth送信・日次上限・特電法フッター・dry_run）"
```

---

## Task 8: /sales-briefing スキル（朝の承認UI）

**Files:**
- Create: `.claude/skills/sales-briefing/SKILL.md`
- Create: `.claude/skills/sales-briefing/references/approval-ui.md`

- [ ] **Step 1: スキル本体を作成**

Create `.claude/skills/sales-briefing/SKILL.md`:
```markdown
---
name: sales-briefing
description: 毎朝の営業オペレーション承認UI。軸C（法人アウトバウンド）の pending DM をオーナーに提示し、承認・却下を受け付けてVPSに送信指示を出す。Phase 1 では軸Cのみ対応、Phase 2で軸A・Bを統合する。
---

# Sales Briefing — 朝の営業承認ワークフロー

## 起動タイミング
- Windows Task Scheduler が平日07:30 に Claude Code を起動しこのスキルを呼び出す
- オーナーが手動で `/sales-briefing` と打っても実行できる

## ステップ

### 1. VPS から最新の approval_queue を取得

```bash
ssh yn-vps "cd /opt/sales-ops && python -c 'import sys; sys.path.insert(0, \"src\"); from core.db import Database; from core.approval_queue import ApprovalQueue; import os, json; from dotenv import load_dotenv; load_dotenv(); db = Database(os.environ[\"SALES_OPS_DB_PATH\"]); q = ApprovalQueue(db); print(json.dumps(q.list_pending(track=\"c\")))'"
```

（実運用では `ssh yn-vps "/opt/sales-ops/venv/bin/python /opt/sales-ops/scripts/list_pending.py --track c --json"` のような薄いCLIラッパーを使う。初期はSSHで直接Python叩く形でOK）

### 2. ペンディング件数をオーナーに提示

```
おはようございます！朝の営業承認です。

軸C（法人アウトバウンド）pending: 47件
  - 税理士事務所: 18件
  - 社労士事務所: 12件
  - 制作会社: 10件
  - その他: 7件

トップ10件を表示して一括承認しますか？
[1] トップ10を一括プレビュー→承認
[2] 業種を絞って選ぶ（税理士だけ、等）
[3] 個別に1件ずつレビュー
[4] 全部skip（今日は送らない）
```

AskUserQuestion でこの4択を提示する。

### 3. 承認UI

- トップN件について、件名+本文冒頭100字+企業名を並べて表示
- オーナーが「全承認」「個別却下」「文面修正」を選べる
- 文面修正時は、該当項目をその場で上書き編集して再度pending化

### 4. 承認アクションをVPSに通知

```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python -c 'from core.db import Database; from core.approval_queue import ApprovalQueue; import os; from dotenv import load_dotenv; load_dotenv(); db = Database(os.environ[\"SALES_OPS_DB_PATH\"]); q = ApprovalQueue(db); [q.approve(i) for i in [ID1, ID2, ...]]'"
```

### 5. 送信トリガー

```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/run_send_approved.py"
```

### 6. 結果サマリーをTelegramに通知

Telegram tool の reply で完了報告:
```
🌅 朝の営業承認 完了 (軸C)
  承認: 10件 / 却下: 3件 / 保留: 34件
  送信結果: 成功 10 / 失敗 0
  返信が来たら15分以内にこのチャットで通知します。
```

### 7. DASHBOARD_SALES.md 更新

今日の送信数を `.company/DASHBOARD_SALES.md` に追記（Phase 3でKPIダッシュボードとして本格化）。

## VPS 接続エイリアス

`~/.ssh/config` に以下を設定済み前提:
```
Host yn-vps
  HostName 163.44.101.31
  User root
  IdentityFile ~/.ssh/conoha_yn_factory
```

## Phase 2 以降の拡張

Phase 2 で軸A（フリーランス応募）・軸B（コンテンツ投稿）の承認も同じフローに統合する。その際 `track` パラメータを `c` から `a, b, c` すべてに拡張するだけで対応可能。

## 参考
- `references/approval-ui.md` — 承認UIのフロー詳細・エッジケース対応
```

- [ ] **Step 2: references/approval-ui.md 作成**

Create `.claude/skills/sales-briefing/references/approval-ui.md`:
```markdown
# Approval UI フロー詳細

## 個別レビュー時の表示フォーマット

```
=== [1/47] A税理士事務所 ===
宛先: contact@a-tax.example.com
件名: A税理士事務所 様 — 顧問先の業務自動化ツールのご案内
パーソナライズ: 中小企業支援に注力の旨をHP冒頭から抽出

本文冒頭:
  山田と申します。貴事務所のHPで中小企業の経営支援に注力されている……
  （続き 412字）

アクション:
  [a] 承認 / [r] 却下 / [e] 本文編集 / [s] スキップ（保留） / [q] 全体中断
```

## エッジケース

### 1. 未填入プレースホルダ検知
personalizer.py 側でブロックされているはずだが、念のため承認前に再検査:
- `{{}}`、`[XXX]`、`<placeholder>` が subject/body に残っていたら承認させない

### 2. 送信済みドメイン重複
同じドメインに過去30日送信済みの場合は警告表示:
```
⚠️ このドメイン (a-tax.example.com) には2026-03-15に送信済みです。再送しますか？
```

### 3. 返信中の企業
`conversations` テーブルで inbound 返信がある企業は新規DMから自動除外（personalizer側で制御）。万が一残っていたら承認UIで警告。

### 4. 夜間/休日の承認
- 休日: スキルを起動しない（Windows Task Scheduler側で平日のみ）
- どうしても日中動かしたい場合: `/sales-briefing --force` で強制起動

## オーナー不在時のフォールバック
- 3日連続で承認されなかった pending 項目は auto_reject_stale で自動却下
- Telegramで「3日承認なしです、承認しますか？」をリマインド
```

- [ ] **Step 3: コミット**

```bash
git add .claude/skills/sales-briefing/
git commit -m "feat(sales-ops): /sales-briefing スキル（朝の承認UIワークフロー）"
```

---

## Task 9: 統合テスト（dry-run でEnd-to-Endパイプライン検証）

**Files:**
- Create: `sales-ops/tests/test_e2e_dry_run.py`

- [ ] **Step 1: E2Eテストを書く**

Create `sales-ops/tests/test_e2e_dry_run.py`:
```python
"""list_builder → personalizer → approve → gmail_sender を dry_run で通す結合テスト。"""
import json
from unittest.mock import MagicMock

import pytest

from core.approval_queue import ApprovalQueue
from core.db import Database, init_schema
from core.senders.gmail_sender import GmailSender
from tracks.c_outbound.list_builder import ListBuilder
from tracks.c_outbound.personalizer import Personalizer


def _mock_gmaps_single(place_id="pid_e2e"):
    gmaps = MagicMock()
    gmaps.places_nearby.return_value = {
        "results": [{
            "place_id": place_id,
            "name": "E2E税理士事務所",
            "website": "https://e2e.example.com",
            "formatted_address": "東京都",
            "types": ["accounting"],
        }]
    }
    gmaps.place.side_effect = lambda place_id, fields=None: {
        "result": {"website": "https://e2e.example.com"}
    }
    return gmaps


def _mock_claude_valid_draft():
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps({
        "subject": "E2E税理士事務所 様 — AI業務自動化ツールのご案内",
        "body": "山田です。貴事務所のHPを拝見しました。\n主な活用例:\n・請求書自動生成\n無料トライアルあります。",
        "personalization_hint": "中小企業支援",
    }, ensure_ascii=False))]
    client.messages.create.return_value = resp
    return client


def _mock_hp_fetcher():
    f = MagicMock()
    f.fetch_summary.return_value = "中小企業の税務顧問を得意とする事務所です"
    return f


def test_end_to_end_dry_run(tmp_db_path, env_stub):
    """list_builder → personalizer → approve → gmail_sender（dry_run）まで一気通貫"""
    db = Database(tmp_db_path)
    init_schema(db)

    # 1. 企業リスト取得
    ListBuilder(db=db, gmaps_client=_mock_gmaps_single()).fetch_t2(
        query="税理士", location=(35.68, 139.76), max_results=10
    )

    # 2. contact_email を設定（本来はユーザが手動または別途補完）
    with db.connect() as conn:
        conn.execute(
            "UPDATE companies SET contact_email = 'e2e@e2e.example.com' WHERE id = 1"
        )

    # 3. 下書き生成 & pending 投入
    processed = Personalizer(
        db=db,
        claude_client=_mock_claude_valid_draft(),
        hp_fetcher=_mock_hp_fetcher(),
    ).process_new_companies(batch_size=10)
    assert processed == 1

    # 4. 承認
    q = ApprovalQueue(db)
    pending = q.list_pending(track="c")
    assert len(pending) == 1
    q.approve(pending[0]["id"])

    # 5. 送信（dry_run）
    sender = GmailSender(
        db=db,
        gmail_service=MagicMock(),
        sender_name="YN Factory",
        sender_address="me@example.com",
        reply_to="me@example.com",
        unsubscribe_url="https://example.com/unsub",
        dry_run=True,
        send_interval_sec=0,
        daily_limit=100,
    )
    sent = sender.send_all_approved(track="c")
    assert sent == 1

    # 6. 最終状態: queue は sent、company は drafted
    final_item = q.get(pending[0]["id"])
    assert final_item["status"] == "sent"
    payload = json.loads(final_item["payload_json"])
    assert payload["gmail_message_id"] == "dry_run"
```

- [ ] **Step 2: テストを走らせて成功を確認**

Run: `cd sales-ops && pytest tests/test_e2e_dry_run.py -v`
Expected: 1 passed

- [ ] **Step 3: 全テスト一括実行**

Run: `cd sales-ops && pytest -v`
Expected: 全テスト PASS（Task 2-7 + E2E の合計 23+ 件）

- [ ] **Step 4: コミット**

```bash
git add sales-ops/tests/test_e2e_dry_run.py
git commit -m "test(sales-ops): E2E dry-run（list→personalize→approve→send 一気通貫）"
```

---

## Task 10: VPS デプロイ手順ドキュメント

**Files:**
- Create: `sales-ops/DEPLOY.md`

- [ ] **Step 1: DEPLOY.md 作成**

Create `sales-ops/DEPLOY.md`:
```markdown
# Sales OS VPS デプロイ手順

## 前提
- ConoHa VPS (163.44.101.31) に root でSSH可能
- `~/.ssh/config` に `Host yn-vps` エイリアス設定済み
- ConoHa VPS上に Python 3.10+ インストール済み（`/opt/keiba-unified/` の例を参考）

## 1. コード転送
```bash
# ローカル
cd g:/マイドライブ/YNFactory-cc
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='tests' \
  --exclude='.pytest_cache' --exclude='data' \
  sales-ops/ yn-vps:/opt/sales-ops/
```

## 2. 依存セットアップ
```bash
ssh yn-vps "cd /opt/sales-ops && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
```

## 3. 環境変数設定
```bash
ssh yn-vps "cd /opt/sales-ops && cp .env.example .env"
# 以下をVPS上で手動編集
# - ANTHROPIC_API_KEY（既存 .env から流用可）
# - GOOGLE_MAPS_API_KEY（Google Cloud Console で Places API New を有効化→API Key発行）
# - GMAIL_OAUTH_CLIENT_SECRET_JSON（Google Cloud Console で OAuth Client ID作成→JSONダウンロード→scp転送）
# - GMAIL_SENDER_ADDRESS=yuichi4107@gmail.com
# - SALES_OPS_DB_PATH=/opt/sales-ops/data/sales_ops.db
# - SALES_OPS_DRY_RUN=true   # 本番切替は実運用開始時のみ
```

## 4. OAuth 初回承認
OAuth は localhost リダイレクトが必要なため、**初回だけローカル（PC）で実行** → 生成された `token.json` をVPSに scp する:

```bash
# ローカル
cd sales-ops
python scripts/gmail_oauth_setup.py
# → ブラウザで承認 → secrets/gmail_token.json 生成
scp secrets/gmail_token.json yn-vps:/opt/sales-ops/secrets/
scp secrets/gmail_client_secret.json yn-vps:/opt/sales-ops/secrets/
```

## 5. DB初期化
```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/init_db.py"
```

## 6. 動作確認（dry-run）
```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/run_list_builder.py"
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/run_personalizer.py"
# 承認はPC側で /sales-briefing スキル経由
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/run_send_approved.py"
```

## 7. crontab 登録
```bash
ssh yn-vps "crontab -l > /tmp/crontab.bak && cat >> /tmp/crontab.bak <<EOF
# Sales OS
0 2 * * * /opt/sales-ops/venv/bin/python /opt/sales-ops/scripts/run_list_builder.py >> /var/log/sales-ops.log 2>&1
30 2 * * * /opt/sales-ops/venv/bin/python /opt/sales-ops/scripts/run_personalizer.py >> /var/log/sales-ops.log 2>&1
EOF
crontab /tmp/crontab.bak"
```

※ `run_send_approved.py` はcron登録しない（朝セッションの承認後にPC→SSHで明示的に叩く）。

## 8. 本番切替チェックリスト
Phase 1 MVP の本番稼働前チェック:
- [ ] Gmail OAuth token 動作確認（VPSから実際に送信成功）
- [ ] `.env` の `SALES_OPS_DRY_RUN=false` に変更
- [ ] 初回は `SALES_OPS_DAILY_SEND_LIMIT=5` で様子見
- [ ] 特電法フッター（配信停止URL、事業者名）が表示されるか実物目視確認
- [ ] 3日連続で送信→返信状況を見て spam 判定されていないかチェック
- [ ] 問題なければ `SALES_OPS_DAILY_SEND_LIMIT=30` → `50` → `100` と段階的に引き上げ

## 9. 既知の注意点（JP-DAYTRADE教訓から）
- **DBは必ず `/opt/sales-ops/data/` 以下に置く**（Google Drive 配下禁止、同期干渉でDB破損）
- VPS上のログは `/var/log/sales-ops.log`、週1で `logrotate` 推奨
- Google Maps API は月$200 無料枠あり、超過監視を Billing アラートで設定
```

- [ ] **Step 2: コミット**

```bash
git add sales-ops/DEPLOY.md
git commit -m "docs(sales-ops): VPSデプロイ手順（OAuth初回セットアップ・cron登録・本番切替）"
```

---

## 全タスク完了後の確認

- [ ] **最終チェック: 全テストPASS**

```bash
cd sales-ops
pytest -v --tb=short
```
Expected: 23+ tests passed（Task 2: 3件、Task 3: 4件、Task 4: 8件、Task 5: 4件、Task 6: 4件、Task 7: 5件、Task 9: 1件 = 合計29件）

- [ ] **HANDOFF.md 更新**

`.company/secretary/HANDOFF.md` に以下を追加:
```markdown
### [NEW 2026-04-19] Sales OS Phase 1 — MVP実装完了
- **状態**: コード実装完了、VPS未デプロイ
- **次回最優先アクション**:
  1. Google Maps API Key発行（Google Cloud Console → Places API (New)）
  2. Gmail OAuth Client ID発行（Google Cloud Console）
  3. VPS `/opt/sales-ops/` へrsyncデプロイ
  4. OAuth初回承認をローカルで実施→token.jsonをVPSにscp
  5. dry_runで疎通確認→SALES_OPS_DAILY_SEND_LIMIT=5で本番開始
- **設計書**: `.company/engineering/docs/sales-ops-design.md`
- **プラン**: `.company/engineering/plans/2026-04-19-sales-ops-phase1-plan.md`
- **コード**: `sales-ops/`
```

---

## 完了条件（Phase 1 全体）

- [x] `sales-ops/` プロジェクトが作成され、ローカルで `pytest` 全PASS
- [x] `DEPLOY.md` に沿ってVPSデプロイできる状態
- [x] `/sales-briefing` スキルが Claude Code で利用可能
- [x] dry-run で list→personalize→approve→send のパイプラインが通る
- [ ] 本番API Key（Google Maps / Gmail OAuth）の取得 ← **オーナー作業**
- [ ] VPSデプロイ実施 ← **オーナー承認後**
- [ ] 本番最小額検証（5社だけ本番送信） ← **明示承認必須**

## Phase 2 への引き継ぎ

Phase 1 本番稼働後、Phase 2（軸A・B追加）のプランを別途 writing-plans で作成する。
