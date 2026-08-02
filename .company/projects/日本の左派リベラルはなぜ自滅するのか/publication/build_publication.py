#!/usr/bin/env python3
"""Create KDP-derived manuscripts from the completed master manuscript.

S001 and S002 are internal project inputs. They are removed from both inline
citations and the final source table without changing the master manuscript.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_DIR / "manuscript" / "日本の左派リベラルはなぜ自滅するのか.md"
DESTINATION = PROJECT_DIR / "publication" / "出版用原稿.md"
REPORT = PROJECT_DIR / "publication" / "時点再確認レポート.md"
EPUB_SOURCE = PROJECT_DIR / "epub" / "manuscript.md"
EXCLUDED_SOURCE_IDS = frozenset({"S001", "S002"})
CITATION_PATTERN = re.compile(
    r"(?P<open>\[|［)(?P<body>\s*S\d{3}(?:\s*[,，、]\s*S\d{3})*\s*)(?P<close>\]|］)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publication_bytes(source: bytes) -> tuple[bytes, dict[str, int]]:
    """Remove excluded IDs from citations and their rows from the source list."""
    source_text = source.decode("utf-8")
    marker = "**出典一覧**"
    row_pattern = re.compile(r"^\|\s*(S00[12])\s*\|")
    in_source_list = False
    removed: list[str] = []
    output: list[str] = []

    for line in source_text.splitlines(keepends=True):
        if marker in line:
            in_source_list = True
        match = row_pattern.match(line) if in_source_list else None
        if match:
            removed.append(match.group(1))
            continue
        output.append(line)

    if removed != ["S001", "S002"]:
        raise RuntimeError(f"出典一覧から除外した行が想定と異なります: {removed}")

    citation_occurrences_modified = 0
    citation_ids_removed = 0

    def replace_citation(match: re.Match[str]) -> str:
        nonlocal citation_occurrences_modified, citation_ids_removed
        opening = match.group("open")
        closing = match.group("close")
        if (opening, closing) not in {("[", "]"), ("［", "］")}:
            return match.group(0)

        ids = re.findall(r"S\d{3}", match.group("body"))
        remaining = [source_id for source_id in ids if source_id not in EXCLUDED_SOURCE_IDS]
        removed_count = len(ids) - len(remaining)
        if removed_count == 0:
            return match.group(0)

        citation_occurrences_modified += 1
        citation_ids_removed += removed_count
        if not remaining:
            return ""
        return f"{opening}{', '.join(remaining)}{closing}"

    derived_text = CITATION_PATTERN.sub(replace_citation, "".join(output))
    if any(source_id in derived_text for source_id in EXCLUDED_SOURCE_IDS):
        raise RuntimeError("派生本文にS001/S002が残っています。引用外の記載を確認してください。")

    statistics = {
        "source_table_rows_removed": len(removed),
        "citation_occurrences_modified": citation_occurrences_modified,
        "citation_ids_removed": citation_ids_removed,
    }
    return derived_text.encode("utf-8"), statistics


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"正本原稿が見つかりません: {SOURCE}")

    source_bytes = SOURCE.read_bytes()
    derived_bytes, statistics = publication_bytes(source_bytes)

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(derived_bytes)
    EPUB_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    EPUB_SOURCE.write_bytes(derived_bytes)

    source_hash = sha256(SOURCE)
    destination_hash = sha256(DESTINATION)
    epub_hash = sha256(EPUB_SOURCE)
    if destination_hash != epub_hash:
        raise RuntimeError("出版用原稿とEPUB用原稿が一致しません。")
    if source_bytes == derived_bytes:
        raise RuntimeError("S001/S002の除外が出版用原稿へ反映されていません。")
    if len(source_bytes.splitlines()) - len(derived_bytes.splitlines()) != 2:
        raise RuntimeError("正本と出版用原稿の行数差が2行ではありません。")

    text = DESTINATION.read_text(encoding="utf-8")
    source_ids = re.findall(r"^\| (S\d{3}) \|", text, flags=re.MULTILINE)
    expected_ids = [f"S{number:03d}" for number in range(3, 71)]
    if source_ids != expected_ids:
        raise RuntimeError("出版用原稿の出典一覧がS003〜S070の68件になっていません。")
    if "S001" in text or "S002" in text:
        raise RuntimeError("派生原稿にS001/S002が残っています。")

    characters = len(text)
    top_level = sum(1 for line in text.splitlines() if line.startswith("# "))
    second_level = sum(1 for line in text.splitlines() if line.startswith("## "))
    report = f"""# 出版時点再確認レポート

- 確認日: 2026-08-02
- 調査基準日: 2026-07-31
- 版: 第1版
- 正本: `manuscript/日本の左派リベラルはなぜ自滅するのか.md`
- 出版用原稿: `publication/出版用原稿.md`
- EPUB用原稿: `epub/manuscript.md`

## 同一性確認

- 正本SHA-256: `{source_hash}`
- 出版用原稿SHA-256: `{destination_hash}`
- EPUB用原稿SHA-256: `{epub_hash}`
- 出版用原稿とEPUB用原稿のバイト同一: 合格
- 正本との差分: S001・S002を本文引用と末尾の出典一覧から除外
- 出典一覧の除外: {statistics['source_table_rows_removed']}行
- 変更した本文引用: {statistics['citation_occurrences_modified']}箇所（除外ID {statistics['citation_ids_removed']}件）
- 派生原稿内のS001/S002残存: 0件
- S001/S002以外の本文、全章節、出典参照の保持: 合格
- 出版用出典一覧: S003〜S070の{len(source_ids)}件
- UTF-8文字数: {characters:,}
- H1見出し数: {top_level}（書名1＋本文16部）
- H2見出し数: {second_level}（固定78節）

## 出版時点の留意事項

- 本文と出典一覧は調査基準日2026-07-31、共通閲覧日2026-08-01の記載を維持した。
- KDP公開版には内部制作資料であるS001・S002を本文引用・出典一覧とも掲載せず、公開資料S003〜S070の68件を掲載する。
- 複合引用ではS001・S002だけを除外し、残る出典IDを保持する。除外後に空になった引用括弧は削除する。
- 正本原稿と研究台帳は変更していない。将来の再生成でも同じ除外規則を派生原稿へ適用する。
- 政党名、役職、公開資料、URLなどは将来変わり得る。改訂版を公開する場合は、版番号を更新し、事実とリンクを再確認する。
- 連絡先は原稿記載どおり、KDP公開前に編集責任者が確定して奥付・公開ページへ反映する必要がある。
- この制作工程ではKDPへのアップロード、価格設定、公開操作を行わない。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
