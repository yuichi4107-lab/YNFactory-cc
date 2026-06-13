# 自分史 文字版＋フル漫画版サービス 実装要件

作成日: 2026-06-09 (火)

## 1. ゴール

祖父母・シニア層を主役にした「自分史」を、完全な文字版電子書籍と完全な漫画版電子書籍の二本立てで制作できるサービス導線を作る。

既存の `theme-to-ebook` / `theme-to-ebook-to-manga` / `ebook-to-manga` を再利用しつつ、これまで曖昧だった「文字中心」を、漫画パートを含まない「完全文字版」として固定する。

## 2. スコープ

実装するもの:

- 自分史サービスの全体設計
- 受注後の注文フォルダ作成ルール
- ヒアリング項目、同意・プライバシー確認、制作ブリーフ
- 完全文字版と完全漫画版の制作ワークフロー
- 既存電子書籍・漫画化スキルへの接続ルール
- ローカルLP雛形とQR用URL設定
- 品質チェック基準
- 次回以降に呼び出せる専用スキル

今回やらないもの:

- 外部サイトへの公開
- 決済・予約フォームの本番接続
- 顧客の個人情報を含む実制作
- KDPへの申請、公開、販売開始
- 外部アカウント操作

## 3. 完了条件

- `.company/services/jibunshi-ebook-manga/` にサービス運用ドキュメント一式がある
- `.agents/skills/jibunshi-ebook-manga-service/SKILL.md` があり、次回から自分史案件で使える
- 受注ごとの注文フォルダを作るスクリプトがある
- `.company/outputs/lp/jibunshi-ebook-manga/` にLP雛形がある
- `theme-to-ebook` と `theme-to-ebook-to-manga` に「完全文字版」ルールが反映されている
- quality-checker視点で85点以上の品質確認が記録されている

## 4. 品質基準

| 項目 | 基準 |
|---|---|
| 商品設計 | 買い手、主役、納品物、制作工程が分離されている |
| 制作導線 | LPから受注後フォルダ作成、文字版、漫画版、納品まで迷わない |
| プライバシー | 実名、写真、家族情報、公開範囲の同意が必須になっている |
| スキル接続 | 既存スキルを再実装せず、入力・品質ゲート・出力先を接続している |
| 二本立て | 文字版に漫画パートを混ぜず、漫画版は独立したフル漫画として扱う |
| 外部操作安全 | 公開、送信、決済、KDP申請は明示承認前に実行しない |

## 5. 工程分割

### 工程1: サービス設計

成果物:

- `README.md`
- `SERVICE_BLUEPRINT.md`
- `production_workflow.md`
- `package_pricing.md`

合格基準:

- 祖父母本人、子・孫のギフト購入者、家族確認者の役割が分かれている
- 完全文字版と完全漫画版の違いが明確
- LP/QRから受注後制作へつながる

### 工程2: 受注運用テンプレート

成果物:

- `intake_questions.md`
- `production_brief_template.md`
- `privacy_and_consent.md`
- `quality_checklist.md`
- `order_schema.json`
- `tools/create_order_package.py`

合格基準:

- 注文単位で同じフォルダ構成を作れる
- 個人情報・家族情報・写真の扱いが明文化されている
- 既存スキルに渡す情報が揃う

### 工程3: 専用スキル実装

成果物:

- `.agents/skills/jibunshi-ebook-manga-service/SKILL.md`
- `.codex/skills/theme-to-ebook/SKILL.md` の完全文字版ルール追記
- `.codex/skills/theme-to-ebook-to-manga/SKILL.md` の二本立てルール追記

合格基準:

- 自分史案件で使うスキルの開始条件、停止条件、外部操作境界が明確
- 文字版に漫画を混ぜないルールが下流に伝わる

### 工程4: LP/QR導線

成果物:

- `.company/outputs/lp/jibunshi-ebook-manga/index.html`
- `.company/outputs/lp/jibunshi-ebook-manga/styles.css`
- `.company/outputs/lp/jibunshi-ebook-manga/lp-copy.md`
- `.company/outputs/lp/jibunshi-ebook-manga/QR_LP_URL.txt`
- `.company/outputs/lp/jibunshi-ebook-manga/qr_lp.png`

合格基準:

- LPが祖父母・親族向けの受注導線として読める
- 個人情報と写真の扱いがLP上で説明されている
- QRの参照先URLがファイルで管理されている

### 工程5: 品質チェック

成果物:

- `.company/services/jibunshi-ebook-manga/QUALITY_REPORT.md`

合格基準:

- 85点以上
- 未達なら修正して再チェック
