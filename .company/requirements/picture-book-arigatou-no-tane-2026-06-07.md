# 要件定義書: KDP絵本『ありがとうの たね』

作成日: 2026-06-07  
ステータス: approved_2026-06-07  
担当フロー: requirements-definer -> executor -> quality-checker  
承認条件: オーナー承認済み。工程1から実制作へ進む

## 1. ゴール

Amazon KDP向けの新しい32ページ絵本『ありがとうの たね』を制作する。

KDP版は単体で満足できる汎用絵本として完成させ、巻末で別販売の個別版サービスへ自然に案内する。

## 2. 企画前提

- タイトル: ありがとうの たね
- サブタイトル: やさしい言葉が、心の中で育つ絵本
- 著者名: Yuichi
- 出版社: YN出版
- 運営: YNファクトリー
- 対象年齢: 3〜5歳
- 主な購入者: 親、祖父母、誕生日・入園・進級・季節のギフト購入者
- テーマ: 「ありがとう」を言う、受け取る、まねして広げる。やさしい言葉が子どもの心で育つ体験を描く
- 読後感: あたたかい、まねしたくなる、家族で言葉を交わしたくなる
- 既存絵本との差分:
  - 『おやすみ、きょうのきもち』は寝る前の感情整理
  - 『ちいさな いっぽの まほう』は初めての挑戦と勇気
  - 本作は日常の「ありがとう」と思いやりを扱う

## 3. スコープ

### やること

- 32ページ構成の企画、本文、ページ計画を作成する
- キャラクター定義、レイアウトメモ、ページ別画像プロンプトを作成する
- 2475 x 2475 px の本文ページ画像を32枚作成する
- 本文入りプレビューを32ページ分作成する
- Kindle固定レイアウトEPUBを作成する
- ペーパーバック本文PDFと表紙PDFを作成する
- KDP登録用メタデータ3点を作成する
- AI生成コンテンツ申告メモ、PIPELINE_REPORT、QUALITY_REPORT、progress.jsonを更新する
- P31を「保護者の方へ」、P32を「特別版のご案内 / 書籍紹介」として本編と分離する
- 個別版CTAは巻末と汎用LPに限定し、KDP商品説明には外部URLや注文フォーム導線を入れない

### やらないこと

- KDPへの実アップロード、公開申請、価格設定は行わない
- ユーザー固有名入りの個別版は今回作らない
- 既存絵本2冊の成果物は変更しない
- KDP商品説明欄に外部注文URLを入れない

## 4. 出力先

プロジェクトフォルダ:

```text
03_成果物/outputs/picture-books/arigatou-no-tane/
```

主要出力:

```text
project.md
research/theme_research.md
manuscript/story_text.md
manuscript/page_plan.md
manuscript/layout_notes.md
manuscript/page_image_prompts.md
manuscript/character_defs.json
images/pages/page_001.png ... page_032.png
images/pages/page_001.jpg ... page_032.jpg
layout/preview_pages/page_001.jpg ... page_032.jpg
layout/contact_preview_025_032.jpg
layout/fixed_layout_source/
KDP出版用/ありがとうの たね.epub
KDP出版用/paperback_interior_8.25x8.25_bleed.pdf
KDP出版用/paperback_cover_8.25x8.25_32p_premium_color.pdf
KDP出版用/paperback_size_spec.md
KDP出版用/書籍情報.md
KDP出版用/ジャンル・キーワード.md
KDP出版用/書籍紹介文_HTML.html
KDP出版用/AI生成コンテンツ申告メモ.md
PIPELINE_REPORT.md
QUALITY_REPORT.md
progress.json
```

## 5. KDP前提

2026-06-07時点でKDP公式ヘルプを確認済み。

- 判型: 8.25 x 8.25 inch
- ページ数: 32ページ
- 印刷: フルカラー / プレミアムカラー / ペーパーバック
- 本文画像: 2475 x 2475 px
- 裁ち落としあり本文PDF: 8.375 x 8.5 inch
- 背幅: 32 pages x 0.002347 inch = 0.075104 inch
- 表紙全体幅: 0.125 + 8.25 + 0.075104 + 8.25 + 0.125 = 16.825104 inch
- 表紙全体高さ: 0.125 + 8.25 + 0.125 = 8.5 inch
- 32ページでは背表紙文字を入れない
- 表紙にはKDPバーコード用の白地エリアを確保する
- AI生成テキスト・画像を使う場合はKDP登録時にAI生成コンテンツとして申告する

参照:

- KDP Create a Paperback Cover: https://kdp.amazon.com/en_US/help/topic/G201953020
- KDP Set Trim Size, Bleed, and Margins: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/
- KDP Cover Calculator: https://kdp.amazon.com/cover-templates?language=en_US

## 6. 工程分割

### 工程1: 企画・本文・ページ設計

中間成果物:

- project.md
- research/theme_research.md
- manuscript/story_text.md
- manuscript/page_plan.md
- manuscript/character_defs.json
- manuscript/layout_notes.md
- manuscript/page_image_prompts.md

品質基準:

- 3〜5歳向けに読み聞かせしやすい短文である
- 主人公の性別・名前を固定しない
- 1ページ1感情・1行動の絵本リズムになっている
- 「ありがとう」を押しつけず、まねしたくなる体験として描いている
- 既存絵本とテーマ、場面、CTAが被りすぎない
- P31/P32が本編と明確に分離されている

合格基準: 85点以上

### 工程2: 画像・ページレイアウト

中間成果物:

- images/pages/page_001.png ... page_032.png
- images/pages/page_001.jpg ... page_032.jpg
- layout/preview_pages/page_001.jpg ... page_032.jpg
- layout/contact_preview_025_032.jpg

品質基準:

- 32ページすべてが 2475 x 2475 px
- 画像内に崩れた文字を入れない
- 本文が安全余白内に収まる
- P31/P32を目視確認する
- 主人公と家族・周囲の人物の見た目が大きく破綻しない

合格基準: 85点以上

### 工程3: EPUB・PDF・表紙制作

中間成果物:

- Kindle固定レイアウトEPUB
- ペーパーバック本文PDF
- ペーパーバック表紙PDF
- paperback_size_spec.md

品質基準:

- EPUBのXHTMLページ数が32
- OPFに pre-paginated / portrait / spread none を設定
- spine全ページに page-spread-center を設定
- zipfile.testzip() が None
- PDF本文が32ページ
- PDF寸法がKDP前提と一致する
- 表紙に背表紙文字を入れない

合格基準: 85点以上

### 工程4: KDPメタデータ・最終QC

中間成果物:

- KDP出版用/書籍情報.md
- KDP出版用/ジャンル・キーワード.md
- KDP出版用/書籍紹介文_HTML.html
- KDP出版用/AI生成コンテンツ申告メモ.md
- PIPELINE_REPORT.md
- QUALITY_REPORT.md
- progress.json

品質基準:

- メタデータにタイトル、著者、出版社、説明文、キーワードが揃っている
- KDP商品説明に外部注文URLや個人情報入力導線を入れない
- AI生成コンテンツ申告メモを明記する
- required files の存在確認を行う
- 最終スコア85点以上

合格基準: 85点以上

## 7. 完了条件

- 必須ファイルがすべて存在する
- 32ページ本文、P31、P32の構成が明確である
- EPUB zip検査が通る
- PDFページ数と寸法を確認済みである
- KDPメタデータ3点が作成済みである
- QUALITY_REPORT.md の総合スコアが85点以上である
- PIPELINE_REPORT.md にKDPアップロード候補ファイルと残る手動確認を明記している

## 8. 承認

2026-06-07、オーナーより「承認」。

工程1から実行し、各工程で品質チェック85点以上を満たしてから次工程へ進む。
