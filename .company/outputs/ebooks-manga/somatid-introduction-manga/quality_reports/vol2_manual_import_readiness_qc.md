# Vol.2 手動画像取り込み準備 品質チェック

## 要件定義

- ゴール: Vol.2の手動生成PNGを受け取り、最終出力先 `vol2/pages/` へ配置できる状態にする
- スコープ: プロンプト存在確認、画像投入先確認、manifest検証、取り込み補助スクリプト作成
- 対象外: ChatGPT Plus上での画像生成そのもの、EPUB製本、KDPメタデータ作成
- 完了条件:
  - `cover.md` と `page_003.md`〜`page_088.md` が揃っている
  - `manual/import/` の不足PNGを検出できる
  - 画像投入後に `done/pages/` 取り込みと `vol2/pages/` 配置を一括実行できる

## 実行結果

- プロンプト: 87件確認済み（表紙1 + 本文86）
- Vol.2最終出力先: 存在確認済み、現時点の画像数は0
- `manual/import/`: 存在確認済み、現時点の画像数は0
- `manifest.json`: dry-run検証OK
- 追加ファイル: `manual/import_and_place_vol2.py`
- README: 一括取り込み手順を追記済み

## 品質チェック

スコア: **88/100 PASS**

- 期待ファイル検出: PASS
- 不足PNG検出: PASS（87枚不足を正しく検出）
- スクリプト構文チェック: PASS
- 医療安全プロンプト維持: PASS
- 残リスク: 実画像が未生成のため、画像内容・日本語テキスト・キャラ再現性の品質チェックは未実施

## 次工程

`manual/import/` に `cover.png` と `page_003.png`〜`page_088.png` を保存後、以下を実行する:

```bash
python3 .company/codex/done/somatid-introduction-manga_vol2_20260504_203002/manual/import_and_place_vol2.py
```
