#!/usr/bin/env python3
"""Create a standardized order package for the jibunshi service."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = ROOT / ".company" / "services" / "jibunshi-ebook-manga"
OUTPUT_ROOT = ROOT / ".company" / "outputs" / "jibunshi-orders"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "order"


def write(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_order_id(args: argparse.Namespace) -> str:
    if args.order_id:
        return slugify(args.order_id)
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y%m%d")
    return f"{today}-{slugify(args.subject_name)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a jibunshi order package.")
    parser.add_argument("--order-id", default="")
    parser.add_argument("--buyer-name", default="未設定")
    parser.add_argument("--subject-name", required=True)
    parser.add_argument("--relationship", default="未設定")
    parser.add_argument(
        "--package",
        choices=["text", "manga", "bundle", "bundle_paperback"],
        default="bundle",
    )
    parser.add_argument(
        "--publication-scope",
        choices=["family_private", "limited_share", "kdp_public_candidate"],
        default="family_private",
    )
    parser.add_argument("--final-approver", default="未設定")
    parser.add_argument("--notes", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    order_id = build_order_id(args)
    order_root = OUTPUT_ROOT / order_id
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")

    directories = [
        "input/materials",
        "production",
        "outputs/text-edition",
        "outputs/manga-edition",
        "qa",
        "delivery",
    ]
    for directory in directories:
        (order_root / directory).mkdir(parents=True, exist_ok=True)

    project = f"""# 自分史制作プロジェクト: {args.subject_name}

作成日時: {now}

## 基本情報

- 注文ID: {order_id}
- 注文者: {args.buyer_name}
- 主役: {args.subject_name}
- 関係: {args.relationship}
- プラン: {args.package}
- 公開範囲: {args.publication_scope}
- 最終確認者: {args.final_approver}

## 制作方針

- 完全文字版: 漫画ページを含めない
- 完全漫画版: 承認済み文字版をもとに独立したフル漫画として作る
- 外部公開/KDP申請: 直前にオーナー承認を取る

## メモ

{args.notes or "未記入"}
"""

    intake = f"""# ヒアリング回答

注文ID: {order_id}
主役: {args.subject_name}

## 注文者

- 名前: {args.buyer_name}
- 主役との関係: {args.relationship}

## 回答

`{SERVICE_ROOT / "intake_questions.md"}` の項目に沿って追記する。
"""

    consent = f"""# 同意チェック

注文ID: {order_id}

## 制作前

- [ ] 主役本人が制作を知っている、または注文者に正当な代理権限がある
- [ ] 素材利用の許可がある
- [ ] 写真利用方針が決まっている
- [ ] 実名利用方針が決まっている
- [ ] 伏せる情報が記録されている

## 公開前

- [ ] 文字版の最終承認
- [ ] 漫画版の最終承認
- [ ] 外部公開の明示承認
- [ ] KDP申請の明示承認
"""

    brief = f"""# 制作ブリーフ

テンプレート:

`{SERVICE_ROOT / "production_brief_template.md"}`

## 今回の制作

- 注文ID: {order_id}
- 主役: {args.subject_name}
- プラン: {args.package}
- 公開範囲: {args.publication_scope}

## 既存スキル接続

- 完全文字版出力先: `03_成果物/outputs/ebooks/{order_id}-text/`
- 完全漫画版出力先: `03_成果物/outputs/ebooks-manga/{order_id}-manga/`
"""

    pipeline = f"""# パイプラインマップ

## 1. 入力整理

- input/intake_answers.md
- input/source_materials.md
- input/consent_checklist.md

## 2. 完全文字版

- 使用スキル: `theme-to-ebook`
- 出力先: `03_成果物/outputs/ebooks/{order_id}-text/`
- 文字版ポリシー: `complete_text_only`

## 3. 確認

- qa/fact_check.md
- qa/privacy_check.md

## 4. 完全漫画版

- 使用スキル: `theme-to-ebook-to-manga`
- 入力: 承認済み文字版
- 出力先: `03_成果物/outputs/ebooks-manga/{order_id}-manga/`

## 5. 納品

- delivery/README_納品対象.md に納品物だけを列挙する
"""

    delivery = f"""# 納品対象

注文ID: {order_id}

ここには、顧客へ渡してよい承認済みファイルだけを書く。

## 納品候補

- [ ] 完全文字版PDF
- [ ] 完全文字版EPUB
- [ ] 完全漫画版PDF
- [ ] 完全漫画版EPUB
- [ ] 表紙画像
- [ ] ペーパーバック用PDF

## 納品しないもの

- 生の文字起こし
- 未使用写真
- 伏せる情報一覧
- 内部QAメモ
- 制作プロンプト
"""

    write(order_root / "project.md", project, args.force)
    write(order_root / "input" / "intake_answers.md", intake, args.force)
    write(order_root / "input" / "interview_questions.md", (SERVICE_ROOT / "intake_questions.md").read_text(encoding="utf-8"), args.force)
    write(order_root / "input" / "source_materials.md", "# 素材一覧\n\n- \n", args.force)
    write(order_root / "input" / "consent_checklist.md", consent, args.force)
    write(order_root / "production" / "brief.md", brief, args.force)
    write(order_root / "production" / "pipeline_map.md", pipeline, args.force)
    write(order_root / "production" / "status.md", "# 進捗\n\n- [ ] 入力整理\n- [ ] 完全文字版\n- [ ] 確認\n- [ ] 完全漫画版\n- [ ] 納品\n", args.force)
    write(order_root / "qa" / "fact_check.md", "# 事実確認\n\n- [ ] 時系列\n- [ ] 名前\n- [ ] 地名\n- [ ] 家族関係\n", args.force)
    write(order_root / "qa" / "privacy_check.md", (SERVICE_ROOT / "privacy_and_consent.md").read_text(encoding="utf-8"), args.force)
    write(order_root / "qa" / "quality_report.md", "# 品質レポート\n\n未実施\n", args.force)
    write(order_root / "delivery" / "README_納品対象.md", delivery, args.force)

    print(order_root)


if __name__ == "__main__":
    main()
