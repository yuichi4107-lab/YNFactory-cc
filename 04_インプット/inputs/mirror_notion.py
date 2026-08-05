#!/usr/bin/env python3
"""Notion「インプットDB」(原本) をローカルへミラーする。

【Notion原本ポリシー(2026-07-21改定)】
Notionが原本。本スクリプトは Notion → ローカル の一方向ミラーのみを行う。
ミラー先は notion_mirror/<ソース>/<日付>-<タイトル>-<pageid8>.md。
Notion側の編集は last_edited_time 差分で反映し、Notion側で削除(archive)された
ページはミラーからも削除する。ローカル側ミラーの手編集は次回実行で消える。

- state: intake/state/notion_mirror.json (page_id→{path, last_edited_time})
- 認証: .env.notion (sync_notion.py と共通)
- 初回はDB全ページのブロック取得のため時間がかかる。2回目以降は編集分のみ。

使い方:
  python mirror_notion.py            # 通常ミラー(差分)
  python mirror_notion.py --full     # 全ページ強制再取得
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

import sync_notion
from sync_notion import NotionClient, load_env_file
import os

BASE_DIR = Path(__file__).resolve().parent
MIRROR_DIR = BASE_DIR / "notion_mirror"
STATE_PATH = BASE_DIR / "intake" / "state" / "notion_mirror.json"
SYNC_STATE_PATH = BASE_DIR / "intake" / "state" / "notion_synced.json"
LOG_DIR = BASE_DIR / "logs"

_log_file = None


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()


def rich_to_text(rich_list) -> str:
    return "".join(r.get("plain_text", "") for r in (rich_list or []))


def block_to_md(client: NotionClient, block: dict, depth: int = 0) -> list:
    """Notionブロック1つをMarkdown行のリストに変換する。1段のネストまで対応。"""
    btype = block.get("type", "")
    data = block.get(btype, {}) or {}
    text = rich_to_text(data.get("rich_text"))
    indent = "  " * depth
    lines = []
    if btype == "heading_1":
        lines.append(f"# {text}")
    elif btype == "heading_2":
        lines.append(f"## {text}")
    elif btype == "heading_3":
        lines.append(f"### {text}")
    elif btype == "bulleted_list_item":
        lines.append(f"{indent}- {text}")
    elif btype == "numbered_list_item":
        lines.append(f"{indent}1. {text}")
    elif btype == "to_do":
        mark = "x" if data.get("checked") else " "
        lines.append(f"{indent}- [{mark}] {text}")
    elif btype == "quote":
        lines.append(f"> {text}")
    elif btype == "code":
        lang = data.get("language", "")
        lang = "" if lang == "plain text" else lang
        lines.append(f"```{lang}")
        lines.append(text)
        lines.append("```")
    elif btype == "divider":
        lines.append("---")
    elif btype == "callout":
        lines.append(f"> {text}")
    elif btype == "paragraph":
        lines.append(text)
    else:
        # 未対応ブロックはプレーンテキストにフォールバック(空なら型名だけ残す)
        lines.append(text if text else f"<!-- {btype} -->")
    # 子ブロック(1段のみ)
    if block.get("has_children") and depth < 2:
        for child in fetch_blocks(client, block["id"]):
            lines.extend(block_to_md(client, child, depth + 1))
    return lines


def fetch_blocks(client: NotionClient, block_id: str) -> list:
    blocks = []
    cursor = None
    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        resp = client.request("GET", path)
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks


def prop_value(props: dict, name: str):
    p = props.get(name)
    if not p:
        return None
    ptype = p.get("type")
    if ptype == "title":
        return rich_to_text(p.get("title"))
    if ptype == "rich_text":
        return rich_to_text(p.get("rich_text"))
    if ptype == "select":
        return (p.get("select") or {}).get("name")
    if ptype == "multi_select":
        return [o.get("name") for o in p.get("multi_select") or []]
    if ptype == "date":
        return (p.get("date") or {}).get("start")
    if ptype == "checkbox":
        return p.get("checkbox")
    return None


def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r'[\\/:*?"<>|#\s]+', "-", (text or "").strip()).strip("-")
    return text[:max_len] or "untitled"


def page_to_markdown(client: NotionClient, page: dict) -> str:
    props = page.get("properties", {})
    title = prop_value(props, "タイトル") or "(無題)"
    meta_lines = [
        "---",
        f"notion_page_id: {page['id']}",
        f"last_edited_time: {page.get('last_edited_time', '')}",
        f'title: "{title}"',
    ]
    for key, label in [("日付", "date"), ("ソース", "source"), ("関連プロジェクト", "related_project"),
                       ("優先度", "priority"), ("input_id", "input_id"), ("元ファイル", "source_file")]:
        v = prop_value(props, key)
        if v:
            meta_lines.append(f"{label}: {v}")
    tags = prop_value(props, "タグ")
    if tags:
        meta_lines.append("tags:")
        meta_lines.extend(f"  - {t}" for t in tags)
    todo = prop_value(props, "TODO候補")
    if todo is not None:
        meta_lines.append(f"todo_candidate: {str(bool(todo)).lower()}")
    meta_lines.append("---")
    meta_lines.append("")

    body_lines = []
    for block in fetch_blocks(client, page["id"]):
        body_lines.extend(block_to_md(client, block))
    return "\n".join(meta_lines + body_lines) + "\n"


def mirror_path(page: dict) -> Path:
    props = page.get("properties", {})
    source = prop_value(props, "ソース") or "other"
    date_str = prop_value(props, "日付") or ""
    title = prop_value(props, "タイトル") or "untitled"
    pid8 = page["id"].replace("-", "")[:8]
    prefix = f"{date_str[:10]}-" if date_str else ""
    return MIRROR_DIR / slugify(source, 30) / f"{prefix}{slugify(title)}-{pid8}.md"


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"pages": {}, "updated_at": None}


def save_state(state):
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    global _log_file
    parser = argparse.ArgumentParser(description="Notion インプットDB をローカルへミラーする")
    parser.add_argument("--full", action="store_true", help="全ページを強制再取得する")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _log_file = open(LOG_DIR / f"notion_mirror_{date.today().isoformat()}.log", "a", encoding="utf-8")

    load_env_file(BASE_DIR / ".env.notion")
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        log("ERROR: NOTION_TOKEN が未設定です。")
        return 1
    if not SYNC_STATE_PATH.exists():
        log("ERROR: notion_synced.json がありません(database_id不明)。先に sync_notion.py を実行してください。")
        return 1
    database_id = json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8")).get("database_id")
    if not database_id:
        log("ERROR: database_id が state にありません。")
        return 1

    client = NotionClient(token)
    state = load_state()

    # DBの全ページ一覧(プロパティのみ)を取得
    pages = []
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        resp = client.request("POST", f"/databases/{database_id}/query", payload)
        pages.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    log(f"mirror_notion start: {len(pages)} pages in Notion (full={args.full})")

    current_ids = set()
    written = skipped = failed = 0
    for page in pages:
        pid = page["id"]
        current_ids.add(pid)
        rec = state["pages"].get(pid)
        edited = page.get("last_edited_time", "")
        if rec and not args.full and rec.get("last_edited_time") == edited:
            skipped += 1
            continue
        try:
            out_path = mirror_path(page)
            content = page_to_markdown(client, page)
            # タイトル変更等でパスが変わった場合は旧ファイルを削除
            if rec and rec.get("path") and rec["path"] != str(out_path.relative_to(BASE_DIR)):
                old = BASE_DIR / rec["path"]
                if old.exists():
                    old.unlink()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            state["pages"][pid] = {
                "path": str(out_path.relative_to(BASE_DIR)),
                "last_edited_time": edited,
            }
            save_state(state)
            written += 1
            log(f"  [mirror] {out_path.relative_to(BASE_DIR)}")
        except Exception as e:
            failed += 1
            log(f"  [mirror] FAILED {pid}: {e}")

    # Notion側で削除(archive)されたページをミラーからも削除
    removed = 0
    for pid in list(state["pages"].keys()):
        if pid not in current_ids:
            rec = state["pages"].pop(pid)
            old = BASE_DIR / rec.get("path", "")
            if rec.get("path") and old.exists():
                old.unlink()
            removed += 1
            log(f"  [removed] {rec.get('path')} (Notion側で削除)")
    if removed:
        save_state(state)

    log(f"mirror_notion done: written={written}, skipped={skipped}, removed={removed}, failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
