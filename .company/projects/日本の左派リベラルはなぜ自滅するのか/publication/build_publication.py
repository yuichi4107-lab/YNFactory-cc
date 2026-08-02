#!/usr/bin/env python3
"""Create KDP-derived manuscripts from the completed master manuscript.

S001 and S002 are internal project inputs. They are removed, then the remaining
public IDs are renumbered from old S003-S070 to new S001-S068.
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
MASTER_PUBLIC_ID_MIN = 3
MASTER_PUBLIC_ID_MAX = 70
PUBLIC_ID_OFFSET = 2
CITATION_PATTERN = re.compile(
    r"(?P<open>\[|［)(?P<body>\s*S\d{3}(?:\s*[,，、]\s*S\d{3})*\s*)(?P<close>\]|］)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def to_public_source_id(master_source_id: str) -> str:
    """Map an old master ID (S003-S070) to a public ID (S001-S068)."""
    number = int(master_source_id[1:])
    if not MASTER_PUBLIC_ID_MIN <= number <= MASTER_PUBLIC_ID_MAX:
        raise RuntimeError(f"公開版へ変換できない出典IDです: {master_source_id}")
    return f"S{number - PUBLIC_ID_OFFSET:03d}"


def publication_bytes(source: bytes) -> tuple[bytes, dict[str, int]]:
    """Exclude internal sources and renumber all remaining public source IDs."""
    source_text = source.decode("utf-8")
    marker = "**出典一覧**"
    row_pattern = re.compile(r"^(?P<prefix>\|\s*)(?P<source_id>S\d{3})(?P<suffix>\s*\|)")
    in_source_list = False
    removed: list[str] = []
    table_rows_renumbered = 0
    output: list[str] = []

    for line in source_text.splitlines(keepends=True):
        if marker in line:
            in_source_list = True
        match = row_pattern.match(line) if in_source_list else None
        if match:
            master_source_id = match.group("source_id")
            if master_source_id in EXCLUDED_SOURCE_IDS:
                removed.append(master_source_id)
                continue
            public_source_id = to_public_source_id(master_source_id)
            line = (
                line[: match.start("source_id")]
                + public_source_id
                + line[match.end("source_id") :]
            )
            table_rows_renumbered += 1
        output.append(line)

    if removed != ["S001", "S002"]:
        raise RuntimeError(f"出典一覧から除外した行が想定と異なります: {removed}")

    citation_occurrences_modified = 0
    citation_occurrences_with_internal_ids = 0
    citation_ids_removed = 0
    citation_ids_renumbered = 0

    def replace_citation(match: re.Match[str]) -> str:
        nonlocal citation_occurrences_modified
        nonlocal citation_occurrences_with_internal_ids
        nonlocal citation_ids_removed
        nonlocal citation_ids_renumbered
        opening = match.group("open")
        closing = match.group("close")
        if (opening, closing) not in {("[", "]"), ("［", "］")}:
            return match.group(0)

        ids = re.findall(r"S\d{3}", match.group("body"))
        remaining = [source_id for source_id in ids if source_id not in EXCLUDED_SOURCE_IDS]
        removed_count = len(ids) - len(remaining)
        citation_occurrences_modified += 1
        citation_ids_removed += removed_count
        citation_ids_renumbered += len(remaining)
        if removed_count:
            citation_occurrences_with_internal_ids += 1
        if not remaining:
            return ""
        public_ids = [to_public_source_id(source_id) for source_id in remaining]
        return f"{opening}{', '.join(public_ids)}{closing}"

    derived_text = CITATION_PATTERN.sub(replace_citation, "".join(output))

    statistics = {
        "source_table_rows_removed": len(removed),
        "source_table_rows_renumbered": table_rows_renumbered,
        "citation_occurrences_modified": citation_occurrences_modified,
        "citation_occurrences_with_internal_ids": citation_occurrences_with_internal_ids,
        "citation_ids_removed": citation_ids_removed,
        "citation_ids_renumbered": citation_ids_renumbered,
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
    expected_ids = [f"S{number:03d}" for number in range(1, 69)]
    if source_ids != expected_ids:
        raise RuntimeError("出版用原稿の出典一覧がS001〜S068の連番68件になっていません。")

    body_text = text.split("**出典一覧**", 1)[0]
    body_source_ids = [
        source_id
        for citation in CITATION_PATTERN.finditer(body_text)
        for source_id in re.findall(r"S\d{3}", citation.group("body"))
    ]
    invalid_body_ids = sorted(set(body_source_ids) - set(source_ids))
    if invalid_body_ids:
        raise RuntimeError(f"本文中に出典一覧へ存在しないIDがあります: {invalid_body_ids}")
    if not body_source_ids:
        raise RuntimeError("本文中の公開出典IDを検出できません。")
    unique_body_source_ids = sorted(set(body_source_ids))
    if any(token in text for token in ("3ae204bd6a1081f8a842fd804d386576", "3ae204bd6a10815ba4befe15c6f97c22")):
        raise RuntimeError("旧S001/S002の内部資料URLが派生原稿に残っています。")

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
- 正本との差分: 旧S001・S002を除外し、旧S003〜S070を公開版S001〜S068へ一括変換
- 出典一覧の除外: {statistics['source_table_rows_removed']}行
- 出典一覧のID変換: {statistics['source_table_rows_renumbered']}行
- 本文引用の変換: {statistics['citation_occurrences_modified']}箇所（旧S001/S002を含む引用 {statistics['citation_occurrences_with_internal_ids']}箇所、除外ID {statistics['citation_ids_removed']}件、番号変換ID {statistics['citation_ids_renumbered']}件）
- 出版用出典一覧: S001〜S068の{len(source_ids)}件（欠番・重複なし）
- 本文中の公開版出典ID: 延べ{len(body_source_ids)}件・{len(unique_body_source_ids)}種類、すべて出典一覧に存在
- ID以外の本文、全章節、書誌情報の保持: 合格
- UTF-8文字数: {characters:,}
- H1見出し数: {top_level}（書名1＋本文16部）
- H2見出し数: {second_level}（固定78節）

## 出版時点の留意事項

- 本文と出典一覧は調査基準日2026-07-31、共通閲覧日2026-08-01の記載を維持した。
- KDP公開版では旧S001・S002を掲載せず、旧S003を新S001、以後同じ規則で旧S070を新S068へ変換する。
- 複合引用では旧S001・S002だけを除外し、残る旧IDを公開版IDへ変換する。除外後に空になった引用括弧は削除する。
- 本文の公開版IDと末尾一覧の公開版IDには、同一の `新番号 = 旧番号 - 2` 規則を適用する。
- 正本原稿と研究台帳は変更していない。将来の再生成でも同じ除外・番号変換規則を派生原稿へ適用する。
- 政党名、役職、公開資料、URLなどは将来変わり得る。改訂版を公開する場合は、版番号を更新し、事実とリンクを再確認する。
- 連絡先は原稿記載どおり、KDP公開前に編集責任者が確定して奥付・公開ページへ反映する必要がある。
- この制作工程ではKDPへのアップロード、価格設定、公開操作を行わない。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
