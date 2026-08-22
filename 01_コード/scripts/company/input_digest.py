#!/usr/bin/env python3
"""04_インプット から、依頼文に関連しそうな資料の候補を機械的に抽出する。

責務は候補の抽出のみ。要約はしない（Claude Code が候補から最終選別して要約する）。
04_インプット は 681ファイル / 475MB あり、丸ごとAIへ渡すことはできないため、
ここで機械的に落としてから見せる。

使い方:
  py -3 input_digest.py --goal "社内アンケートを集計するツール" --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


INPUT_DIRNAME = "04_インプット"

# 依頼文によらず必ず候補に入れる。ワークスペースの判断前提が書かれている。
ALWAYS_RELATIVE = (
    ("inputs/context-map.md", "恒久コンテキスト"),
    ("inputs/CLAUDE.md", "恒久コンテキスト"),
)

EXCLUDED_DIRS = frozenset({
    "logs", "intake", "__pycache__", ".git", "node_modules", "uploader",
})
MARKDOWN_SUFFIX = ".md"

# 一般的すぎて検索語にならない語。要件定義の依頼文に頻出するもの。
STOPWORDS = frozenset({
    "する", "こと", "ため", "もの", "よう", "という", "について", "ください",
    "システム", "ツール", "アプリ", "作成", "開発", "実装", "対応", "管理",
    "機能", "情報", "内容", "場合", "以下", "上記", "自動", "処理", "利用",
})

TERM_PATTERN = re.compile(r"[一-龥]{2,}|[ァ-ヶー]{2,}|[A-Za-z][A-Za-z0-9_-]{1,}")
DATE_PATTERN = re.compile(r"(20\d{2}-\d{2}-\d{2})")
EXCERPT_LENGTH = 200
COMMON_TERM_RATIO = 0.5

DEFAULT_MAX_FILES = 8
DEFAULT_MAX_BYTES = 409_600


def detect_git_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return Path(result.stdout.strip()).resolve()
    except Exception:
        return Path.cwd().resolve()


def load_safety():
    """プランナーの検出器を借りる。無ければ検査なしで続行する。"""
    for candidate in (
        detect_git_root() / "01_コード" / "ai-collab-planner",
        Path("G:/マイドライブ/YNFactory-cc/01_コード/ai-collab-planner"),
    ):
        if (candidate / "ai_planner" / "safety.py").exists():
            sys.path.insert(0, str(candidate))
            try:
                from ai_planner.safety import scan_injection, scan_secrets
                return scan_secrets, scan_injection
            except Exception:
                continue
    return None, None


def extract_terms(goal: str) -> list[str]:
    terms: list[str] = []
    for token in TERM_PATTERN.findall(goal):
        if token in STOPWORDS or token in terms:
            continue
        terms.append(token)
    return terms


def collect_markdown(root: Path) -> list[Path]:
    """除外ルールを適用した .md の一覧。常時対象ファイルは含めない。"""
    always = {(root / relative).resolve() for relative, _ in ALWAYS_RELATIVE}
    found: list[Path] = []
    for path in sorted(root.rglob(f"*{MARKDOWN_SUFFIX}")):
        try:
            if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts[:-1]):
                continue
            if path.resolve() in always:
                continue
            if not path.is_file():
                continue
        except (OSError, ValueError):
            continue
        found.append(path)
    return found


def file_date(path: Path) -> str:
    match = DATE_PATTERN.search(path.name)
    return match.group(1) if match else ""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def rank(goal: str, files: list[Path]) -> list[dict]:
    """スコア順の候補を返す。スコア0のファイルは含めない。"""
    terms = extract_terms(goal)
    if not terms or not files:
        return []

    texts = {path: read_text(path) for path in files}

    # 全体の半分超に出る語は、選別の役に立たないので数えない。
    total = len(files)
    effective = [
        term for term in terms
        if sum(1 for text in texts.values() if term in text) <= total * COMMON_TERM_RATIO
    ]
    if not effective:
        effective = terms

    scored: list[dict] = []
    for path in files:
        text = texts[path]
        matched = [term for term in effective if term in text]
        if not matched:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        scored.append({
            "path": str(path),
            "bytes": size,
            "date": file_date(path),
            "matched": matched,
            "score": len(matched),
            "excerpt": text.strip().replace("\n", " ")[:EXCERPT_LENGTH],
        })

    # 安定ソートを2段。まず日付の新しい順、次にスコアの高い順。
    # 同スコアなら新しい資料が上に来る。
    scored.sort(key=lambda item: item["date"] or "0000-00-00", reverse=True)
    scored.sort(key=lambda item: -item["score"])
    return scored


def apply_safety(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """秘密情報・誘導文を含むファイルを候補から外す。値そのものは記録しない。"""
    scan_secrets, scan_injection = load_safety()
    if scan_secrets is None:
        return items, []

    kept: list[dict] = []
    blocked: list[dict] = []
    for item in items:
        text = read_text(Path(item["path"]))
        secrets = scan_secrets(text)
        if secrets:
            blocked.append({
                "path": item["path"], "kind": "secret",
                "findings": [finding.describe() for finding in secrets],
            })
            continue
        injections = scan_injection(text)
        if injections:
            blocked.append({
                "path": item["path"], "kind": "injection",
                "findings": [finding.describe() for finding in injections],
            })
            continue
        kept.append(item)
    return kept, blocked


def apply_limits(items: list[dict], max_files: int, max_bytes: int) -> list[dict]:
    limited: list[dict] = []
    total = 0
    for item in items:
        if len(limited) >= max_files:
            break
        if total + item["bytes"] > max_bytes and limited:
            continue
        limited.append(item)
        total += item["bytes"]
    return limited


def always_entries(root: Path) -> list[dict]:
    entries: list[dict] = []
    for relative, reason in ALWAYS_RELATIVE:
        path = root / relative
        if not path.is_file():
            continue
        try:
            entries.append({"path": str(path), "bytes": path.stat().st_size, "reason": reason})
        except OSError:
            continue
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="04_インプットから依頼文に関連する資料の候補を抽出する"
    )
    parser.add_argument("--goal", required=True, help="依頼文")
    parser.add_argument("--root", type=Path, help="04_インプット のパス")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)
    if getattr(args, "json", False) and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = args.root.resolve() if args.root else (detect_git_root() / INPUT_DIRNAME)
    if not root.is_dir():
        payload = {"error": f"見つかりません: {root}", "always": [], "candidates": []}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["error"])
        return 1

    files = collect_markdown(root)
    ranked = rank(args.goal, files)
    kept, blocked = apply_safety(ranked)
    candidates = apply_limits(kept, args.max_files, args.max_bytes)

    payload = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "root": str(root),
        "always": always_entries(root),
        "candidates": candidates,
        "scanned": len(files),
        "matched": len(ranked),
        "safety": {
            "secrets": sum(1 for item in blocked if item["kind"] == "secret"),
            "injection": sum(1 for item in blocked if item["kind"] == "injection"),
            "blocked": blocked,
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"走査 {payload['scanned']} 本 / 一致 {payload['matched']} 本 / 候補 {len(candidates)} 本")
        for entry in payload["always"]:
            print(f"  [常時] {entry['path']}")
        for item in candidates:
            print(f"  [{item['score']}] {item['path']}  一致: {'、'.join(item['matched'])}")
        if blocked:
            print(f"  除外（安全検査）: {len(blocked)} 本")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
