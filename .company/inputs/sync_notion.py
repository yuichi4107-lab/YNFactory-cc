#!/usr/bin/env python3
"""organized/ 配下の整理済みインプットを Notion の単一データベースへ同期する。

- 対象: organized/{lifelogs,zoom,google-meet,external}/*.md (README等は除外)
- 冪等性: intake/state/notion_synced.json に相対パス→{page_id, sha256} を記録
- 内容変更時: 旧ページを archive して新規ページを作成する
- 認証: .env.notion の NOTION_TOKEN / NOTION_PARENT_PAGE_ID (環境変数優先)

使い方:
  python sync_notion.py            # 通常同期
  python sync_notion.py --dry-run  # API を呼ばず対象を表示
  python sync_notion.py --limit 5  # 先頭5件だけ処理(お試し)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, date
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
ORGANIZED_DIR = BASE_DIR / "organized"
STATE_PATH = BASE_DIR / "intake" / "state" / "notion_synced.json"
ENV_PATH = BASE_DIR / ".env.notion"
LOG_DIR = BASE_DIR / "logs"

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
DATABASE_TITLE = "インプットDB"
REQUEST_INTERVAL = 0.35  # Notion 公式レート制限 約3req/s
MAX_RETRIES = 4

# organized/ サブフォルダ → ソース select 値
SOURCE_DIRS = {
    "lifelogs": "lifelog",
    "zoom": "zoom",
    "google-meet": "google-meet",
    "external": "external",
}

EXCLUDE_NAMES = {"README.md", "_template.md"}

_log_file = None


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()


def load_env_file(path: Path) -> None:
    """KEY=VALUE 形式の簡易 .env 読み込み。既存の環境変数を優先する。"""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ---------------------------------------------------------------------------
# frontmatter / markdown 解析
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str):
    """YAML サブセット(key: value / key: の下の - リスト)を dict に変換して本文と分離する。"""
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            current_list_key = None
            for line in block.splitlines():
                if not line.strip():
                    continue
                if re.match(r"^\s+-\s+", line) and current_list_key:
                    meta.setdefault(current_list_key, [])
                    if isinstance(meta[current_list_key], list):
                        meta[current_list_key].append(line.strip()[2:].strip().strip('"').strip("'"))
                    continue
                m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
                if m:
                    key, value = m.group(1), m.group(2).strip()
                    if value == "":
                        current_list_key = key
                        meta[key] = []
                    else:
                        current_list_key = None
                        meta[key] = value.strip('"').strip("'")
    return meta, body


def chunk_rich_text(text: str, limit: int = 2000):
    """rich_text の 2000 文字制限に合わせて分割する。"""
    if not text:
        return [{"type": "text", "text": {"content": ""}}]
    return [
        {"type": "text", "text": {"content": text[i:i + limit]}}
        for i in range(0, len(text), limit)
    ]


def markdown_to_blocks(body: str):
    """Markdown 本文を Notion ブロックの簡易表現へ変換する。"""
    blocks = []
    lines = body.splitlines()
    i = 0
    in_code = False
    code_lines = []
    code_lang = ""
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                code_text = "\n".join(code_lines)
                blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": chunk_rich_text(code_text),
                        "language": code_lang if code_lang else "plain text",
                    },
                })
                in_code = False
                code_lines = []
            else:
                in_code = True
                lang = stripped[3:].strip().lower()
                # Notion が受け付けない言語名は plain text に落とす
                code_lang = lang if lang in {"python", "javascript", "json", "bash", "shell", "sql", "yaml", "html", "css", "markdown"} else "plain text"
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = min(len(m.group(1)), 3)
            blocks.append({
                "type": f"heading_{level}",
                f"heading_{level}": {"rich_text": chunk_rich_text(m.group(2))},
            })
            i += 1
            continue
        m = re.match(r"^-\s+\[( |x|X)\]\s+(.*)$", stripped)
        if m:
            blocks.append({
                "type": "to_do",
                "to_do": {
                    "rich_text": chunk_rich_text(m.group(2)),
                    "checked": m.group(1).lower() == "x",
                },
            })
            i += 1
            continue
        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": chunk_rich_text(m.group(1))},
            })
            i += 1
            continue
        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": chunk_rich_text(m.group(1))},
            })
            i += 1
            continue
        if stripped.startswith(">"):
            blocks.append({
                "type": "quote",
                "quote": {"rich_text": chunk_rich_text(stripped.lstrip("> "))},
            })
            i += 1
            continue
        blocks.append({
            "type": "paragraph",
            "paragraph": {"rich_text": chunk_rich_text(stripped)},
        })
        i += 1
    if in_code and code_lines:
        blocks.append({
            "type": "code",
            "code": {"rich_text": chunk_rich_text("\n".join(code_lines)), "language": "plain text"},
        })
    return blocks


# ---------------------------------------------------------------------------
# Notion API クライアント
# ---------------------------------------------------------------------------

class NotionClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        })

    def request(self, method: str, path: str, payload=None):
        url = f"{NOTION_API}{path}"
        for attempt in range(MAX_RETRIES + 1):
            time.sleep(REQUEST_INTERVAL)
            resp = self.session.request(method, url, json=payload, timeout=60)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", "2"))
                log(f"  rate limited, retry after {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code >= 500 and attempt < MAX_RETRIES:
                time.sleep(2 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise RuntimeError(f"Notion API error {resp.status_code} {method} {path}: {resp.text[:500]}")
            return resp.json()
        raise RuntimeError(f"Notion API retry exceeded: {method} {path}")

    def create_database(self, parent_page_id: str):
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": DATABASE_TITLE}}],
            "properties": {
                "タイトル": {"title": {}},
                "日付": {"date": {}},
                "ソース": {"select": {"options": [
                    {"name": "lifelog", "color": "blue"},
                    {"name": "zoom", "color": "purple"},
                    {"name": "google-meet", "color": "green"},
                    {"name": "external", "color": "orange"},
                ]}},
                "タグ": {"multi_select": {}},
                "関連プロジェクト": {"select": {}},
                "優先度": {"select": {}},
                "TODO候補": {"checkbox": {}},
                "input_id": {"rich_text": {}},
                "元ファイル": {"rich_text": {}},
                "取込日時": {"date": {}},
            },
        }
        return self.request("POST", "/databases", payload)

    def create_page(self, database_id: str, properties: dict, blocks: list):
        payload = {
            "parent": {"type": "database_id", "database_id": database_id},
            "properties": properties,
            "children": blocks[:100],
        }
        page = self.request("POST", "/pages", payload)
        page_id = page["id"]
        rest = blocks[100:]
        while rest:
            self.request("PATCH", f"/blocks/{page_id}/children", {"children": rest[:100]})
            rest = rest[100:]
        return page_id

    def archive_page(self, page_id: str):
        self.request("PATCH", f"/pages/{page_id}", {"archived": True})


# ---------------------------------------------------------------------------
# 同期ロジック
# ---------------------------------------------------------------------------

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"database_id": None, "files": {}, "updated_at": None}


def save_state(state):
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_targets():
    """organized/ 配下の同期対象 md を (相対パス, ソース名) で列挙する。"""
    targets = []
    for dirname, source in SOURCE_DIRS.items():
        folder = ORGANIZED_DIR / dirname
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name in EXCLUDE_NAMES or path.name.startswith("_"):
                continue
            targets.append((path, source))
    return targets


def sanitize_select(value: str) -> str:
    """select 値のカンマ禁止対応と長さ制限。"""
    return value.replace(",", "、")[:100]


def parse_date_str(value):
    if not value:
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", str(value))
    return m.group(1) if m else None


def build_properties(meta: dict, body: str, path: Path, source: str, rel_path: str):
    title = str(meta.get("title") or "").strip()
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else path.stem
    if len(title) > 2000:
        log(f"  warn: title truncated to 2000 chars: {rel_path}")
    props = {
        "タイトル": {"title": chunk_rich_text(title[:2000])},
        "ソース": {"select": {"name": source}},
        "元ファイル": {"rich_text": chunk_rich_text(rel_path)},
        "取込日時": {"date": {"start": datetime.now().isoformat(timespec="seconds")}},
    }
    date_str = parse_date_str(meta.get("date"))
    if date_str:
        props["日付"] = {"date": {"start": date_str}}
    tags = meta.get("tags")
    if isinstance(tags, list) and tags:
        if len(tags) > 20:
            log(f"  warn: tags truncated to 20 (was {len(tags)}): {rel_path}")
        props["タグ"] = {"multi_select": [{"name": sanitize_select(t)} for t in tags[:20] if t]}
    related = str(meta.get("related_project") or "").strip()
    if related and related != "-":
        props["関連プロジェクト"] = {"select": {"name": sanitize_select(related)}}
    priority = str(meta.get("priority") or "").strip()
    if priority:
        props["優先度"] = {"select": {"name": sanitize_select(priority)}}
    todo = str(meta.get("todo_candidate") or "").strip().lower()
    props["TODO候補"] = {"checkbox": todo == "true"}
    input_id = str(meta.get("input_id") or "").strip()
    if input_id:
        props["input_id"] = {"rich_text": chunk_rich_text(input_id)}
    return props


def main() -> int:
    global _log_file
    parser = argparse.ArgumentParser(description="organized/ を Notion へ同期する")
    parser.add_argument("--dry-run", action="store_true", help="API を呼ばず対象と差分だけ表示する")
    parser.add_argument("--limit", type=int, default=0, help="処理する最大件数(0=無制限)")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"notion_sync_{date.today().isoformat()}.log"
    _log_file = open(log_path, "a", encoding="utf-8")

    load_env_file(ENV_PATH)
    token = os.getenv("NOTION_TOKEN", "").strip()
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()

    state = load_state()
    targets = collect_targets()
    log(f"sync_notion start: {len(targets)} target files (dry_run={args.dry_run}, limit={args.limit or 'none'})")

    # 差分判定
    plan = []  # (path, source, rel_path, sha256, action)
    for path, source in targets:
        content = path.read_text(encoding="utf-8", errors="replace")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        rel_path = path.relative_to(ORGANIZED_DIR).as_posix()
        rec = state["files"].get(rel_path)
        if rec is None:
            plan.append((path, source, rel_path, sha, "create"))
        elif rec.get("sha256") != sha:
            plan.append((path, source, rel_path, sha, "update"))

    skipped = len(targets) - len(plan)
    if args.limit > 0:
        plan = plan[:args.limit]

    if args.dry_run:
        for _, source, rel_path, _, action in plan:
            log(f"  [{action}] ({source}) {rel_path}")
        log(f"dry-run done: create/update={len(plan)}, skipped={skipped}")
        return 0

    if not token or not parent_page_id:
        log("ERROR: NOTION_TOKEN / NOTION_PARENT_PAGE_ID が未設定です。.env.notion を確認してください。")
        return 1

    client = NotionClient(token)

    # データベース確保(初回のみ作成)
    if not state.get("database_id"):
        log(f"creating Notion database '{DATABASE_TITLE}' under parent page...")
        db = client.create_database(parent_page_id)
        state["database_id"] = db["id"]
        save_state(state)
        log(f"database created: {db['id']}")
    database_id = state["database_id"]

    created = updated = failed = 0
    for path, source, rel_path, sha, action in plan:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(content)
            props = build_properties(meta, body, path, source, rel_path)
            blocks = markdown_to_blocks(body)
            if action == "update":
                old_id = state["files"][rel_path].get("page_id")
                if old_id:
                    try:
                        client.archive_page(old_id)
                    except RuntimeError as e:
                        log(f"  warn: archive failed for {rel_path}: {e}")
            page_id = client.create_page(database_id, props, blocks)
            state["files"][rel_path] = {
                "page_id": page_id,
                "sha256": sha,
                "synced_at": datetime.now().isoformat(timespec="seconds"),
            }
            save_state(state)  # 途中終了に備えて逐次保存
            if action == "create":
                created += 1
            else:
                updated += 1
            log(f"  [{action}] ok ({source}) {rel_path}")
        except Exception as e:
            failed += 1
            log(f"  [{action}] FAILED {rel_path}: {e}")

    log(f"sync_notion done: created={created}, updated={updated}, skipped={skipped}, failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
