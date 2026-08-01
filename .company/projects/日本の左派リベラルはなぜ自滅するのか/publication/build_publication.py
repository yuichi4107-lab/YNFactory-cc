#!/usr/bin/env python3
"""Freeze the completed manuscript as the publication source.

The publication copy is byte-for-byte identical to the completed manuscript.
No editorial transformation is performed here.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_DIR / "manuscript" / "日本の左派リベラルはなぜ自滅するのか.md"
DESTINATION = PROJECT_DIR / "publication" / "出版用原稿.md"
REPORT = PROJECT_DIR / "publication" / "時点再確認レポート.md"
EPUB_SOURCE = PROJECT_DIR / "epub" / "manuscript.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"正本原稿が見つかりません: {SOURCE}")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, DESTINATION)
    EPUB_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, EPUB_SOURCE)

    source_hash = sha256(SOURCE)
    destination_hash = sha256(DESTINATION)
    if source_hash != destination_hash:
        raise RuntimeError("出版用原稿が正本と一致しません。")

    text = DESTINATION.read_text(encoding="utf-8")
    epub_hash = sha256(EPUB_SOURCE)
    if source_hash != epub_hash:
        raise RuntimeError("EPUB用原稿が正本と一致しません。")

    characters = len(text)
    top_level = sum(1 for line in text.splitlines() if line.startswith("# "))
    second_level = sum(1 for line in text.splitlines() if line.startswith("## "))
    report = f"""# 出版時点再確認レポート

- 確認日: 2026-08-01
- 調査基準日: 2026-07-31
- 版: 第1版
- 正本: `manuscript/日本の左派リベラルはなぜ自滅するのか.md`
- 出版用原稿: `publication/出版用原稿.md`
- EPUB用原稿: `epub/manuscript.md`

## 同一性確認

- SHA-256: `{source_hash}`
- 出版用原稿と正本のバイト同一: 合格
- EPUB用原稿と正本のバイト同一: 合格
- UTF-8文字数: {characters:,}
- H1見出し数: {top_level}（書名1＋本文16部）
- H2見出し数: {second_level}（固定78節）

## 出版時点の留意事項

- 本文と出典一覧は調査基準日2026-07-31、共通閲覧日2026-08-01の記載を維持した。
- 本レポート作成時点で、正本本文、固定章節タイトル、出典ID、出典一覧への編集は行っていない。
- 政党名、役職、公開資料、URLなどは将来変わり得る。改訂版を公開する場合は、版番号を更新し、事実とリンクを再確認する。
- 連絡先は原稿記載どおり、KDP公開前に編集責任者が確定して奥付・公開ページへ反映する必要がある。
- この制作工程ではKDPへのアップロード、価格設定、公開操作を行わない。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
