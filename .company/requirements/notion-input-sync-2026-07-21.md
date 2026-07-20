---
date: 2026-07-21
type: requirements
project: インプットデータNotion自動蓄積
status: approved
---

# 要件定義: インプットデータの Notion 自動蓄積

## 背景

- `.company/inputs/` に raw→intake→organized→indexes のインプット取り込みパイプラインが稼働中(Limitless / Zoom / Google Meet / Drive INPUT_BOX の4系統)
- 2026-07-15 の音声メモで「蓄積したインプットデータを Notion に移して整理・管理したい」との指示
- 2026-07-21 にオーナー確認済み: Notion 公式 API + トークン方式 / organized 全部 / 単一DB+ビュー / 1日1回実行

## ゴール

`organized/**/*.md` が自動的に Notion の単一データベース「インプットDB」へページとして蓄積され、Notion 側でソース別・日付別・タグ別に整理閲覧できる状態。

## スコープ

- 対象: `organized/{lifelogs,zoom,google-meet,external}/*.md`(README・_template 除外)。初回バックフィル約101件+今後の新規分
- スコープ外: conversations/ 原文の同期、Notion→ローカルの逆方向同期、indexes/ の個別ページ化

## 完了条件

1. 初回バックフィルで organized/ 全件が Notion DB に登録される
2. 再実行しても重複ページが増えない(冪等)
3. ファイル内容の変更が次回実行で反映される(旧ページ archive → 再作成)
4. Windows Task Scheduler「YNFactory Notion Sync」で毎日 07:30 に無人実行される
5. トークン(.env.notion)が git にコミットされない

## 品質基準(quality-checker 採点観点)

- 冪等性(state による重複防止・sha256 差分検知)
- 機密非コミット(.gitignore / sync 対象パス限定)
- ログ出力(logs/notion_sync_YYYY-MM-DD.log)
- 途中終了耐性(1件ごとに state 逐次保存)
- レート制限順守(0.35秒間隔・429 リトライ)

## 構成

| ファイル | 役割 |
|---|---|
| `.company/inputs/sync_notion.py` | 同期本体 |
| `.company/inputs/notion_sync.bat` | 実行ラッパー |
| `.company/inputs/setup_notion_sync_windows.bat` | タスク登録(DAILY 07:30) |
| `.company/inputs/remove_notion_sync_windows.bat` | タスク解除 |
| `.company/inputs/.env.notion` | NOTION_TOKEN / NOTION_PARENT_PAGE_ID(git 非対象) |
| `.company/inputs/intake/state/notion_synced.json` | 同期 state(DB ID・ページ ID・sha256) |

## Notion DB プロパティ

タイトル(title) / 日付(date) / ソース(select: lifelog・zoom・google-meet・external) / タグ(multi_select) / 関連プロジェクト(select) / 優先度(select) / TODO候補(checkbox) / input_id(rich_text) / 元ファイル(rich_text) / 取込日時(date)

## オーナー作業(前提)

1. https://www.notion.so/my-integrations で内部インテグレーション作成 → トークン取得
2. Notion に親ページ(例: YNFactory インプット)を作成し、インテグレーションを接続
3. `.company/inputs/.env.notion` にトークンと親ページ ID を記入
