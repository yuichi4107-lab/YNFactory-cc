# 制作ワークフロー

## 全体

```text
LP/QR
  ↓
問い合わせ・相談
  ↓
注文フォルダ作成
  ↓
ヒアリング・素材整理・同意確認
  ↓
完全文字版制作
  ↓
本人/家族確認
  ↓
完全漫画版制作
  ↓
最終QA
  ↓
納品
```

## 注文フォルダ

受注ごとに以下を作る。

```text
03_成果物/outputs/jibunshi-orders/{order-id}/
├── project.md
├── input/
│   ├── intake_answers.md
│   ├── interview_questions.md
│   ├── source_materials.md
│   └── consent_checklist.md
├── production/
│   ├── brief.md
│   ├── pipeline_map.md
│   └── status.md
├── outputs/
│   ├── text-edition/
│   └── manga-edition/
├── qa/
│   ├── fact_check.md
│   ├── privacy_check.md
│   └── quality_report.md
└── delivery/
    └── README_納品対象.md
```

## Step 0: 受注前確認

確認すること:

- 主役本人は制作を知っているか
- 家族からのサプライズの場合、どこまで素材を使ってよいか
- 実名、写真、学校名、会社名、地名を使うか
- 公開KDPにするか、家族内限定納品にするか
- ペーパーバックが必要か

公開・販売を伴う場合は、本人または正当な代理者の明示承認が必要。

## Step 1: ヒアリングと素材整理

入力素材:

- ヒアリング回答
- インタビュー文字起こし
- 年表
- 写真
- 手紙、日記、職歴、受賞歴
- 家族からのメッセージ

処理:

- 時系列に整理
- 重要エピソードを抽出
- 伏せる情報を分ける
- 文字版に使う素材と漫画版に使う素材を分ける

## Step 2: 完全文字版制作

使用スキル:

- `theme-to-ebook`

必須条件:

- `edition_policy.text_edition = complete_text_only`
- 漫画ページ、漫画パート、章末漫画を入れない
- 画像は本人・家族提供写真、年表、家系図、図解に限定する
- AI画像を使う場合も漫画風のストーリーパネルにはしない

標準構成:

- はじめに
- 第1章: 生まれた時代と家族
- 第2章: 子ども時代・学生時代
- 第3章: 仕事、結婚、子育て、転機
- 第4章: 苦労、支え、人生で大切にしてきたこと
- 第5章: 家族へのメッセージ、これから残したい言葉
- おわりに

出力先:

```text
03_成果物/outputs/ebooks/{order-id}-text/
```

注文フォルダには `outputs/text-edition/source_path.txt` で実体パスを記録する。

## Step 3: 文字版確認

漫画化へ進む前に確認する。

- 本人名、家族名、地名、会社名の表記
- 伏せる情報
- 時系列の誤り
- 写真の使用可否
- 家族が読んで不必要に傷つく表現がないか
- 公開範囲

不確かな箇所は `qa/fact_check.md` に残し、漫画版へ流さない。

## Step 4: 完全漫画版制作

使用スキル:

- `theme-to-ebook-to-manga`
- 下流で `ebook-to-manga`

必須条件:

- 文字版の承認済みソースだけを使う
- 漫画版は全編漫画として構成する
- 実名・顔・制服・住所などは公開範囲に合わせて抽象化する
- 漫画版タイトルは原則 `マンガでわかる！{文字版タイトル}`

出力先:

```text
03_成果物/outputs/ebooks-manga/{order-id}-manga/
```

注文フォルダには `outputs/manga-edition/source_path.txt` で実体パスを記録する。

## Step 5: ペーパーバック対応

必要な場合のみ実施する。

- 文字版ペーパーバック
- 漫画版ペーパーバック
- 家族内納品用PDF
- KDP申請補助

KDP申請、販売開始、外部公開はオーナーの直前承認が必要。

## Step 6: 納品

`delivery/README_納品対象.md` に、渡してよいファイルだけを書く。

納品対象に含めるもの:

- 完全文字版EPUB/PDF
- 完全漫画版EPUB/PDF
- 表紙画像
- ペーパーバックPDF
- 使い方メモ

納品対象に含めないもの:

- 生のインタビュー文字起こし
- 非公開写真
- 未確認の家族情報
- 制作途中のプロンプト
- 内部QAメモ
