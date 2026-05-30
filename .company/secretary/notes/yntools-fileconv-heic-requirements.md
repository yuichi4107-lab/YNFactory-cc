# 要件定義書
# YNtools fileconv — HEIC形式対応追加

作成日: 2026-05-11

---

## ゴール

fileconv ツールの画像変換カードに HEIC 入出力を追加し、iPhone写真（.heic/.heif）をPNG/JPEG/WebPに変換できること、および任意画像からHEIC出力（実験的）を試せることが単一ページ変更で実現されている。

---

## スコープ

### やること
- `yn-tools/app/templates/tools/fileconv/index.html` のみ修正する
- `{% block head %}` 内に CDN `<script>` タグを2本追加する（base.html の拡張ポイントを使用）
  - heic2any（HEIC入力デコード）: unpkg CDN
  - libheif-js（HEIC出力エンコード、WASM版）: unpkg CDN
- `<input id="imgInput">` の `accept` 属性に `.heic,.heif,image/heic,image/heif` を追加する
- 出力 select `id="imgFormat"` に `<option value="image/heic">HEIC (実験的)</option>` を追加する
- `convertImage()` 関数を async/await 対応に書き換え、HEIC入力デコード分岐と HEIC出力エンコード分岐を追加する
- 変換中のローディング表示（`imgStatus` テキスト）を追加する
- HEIC デコード・エンコード失敗時のエラー表示を `imgStatus` に反映する
- 画像変換カードの説明文（`<p>PNG / JPEG / WebP 間で変換</p>`）に HEIC を追記する
- executor 判断で dashboard.html の説明文に "HEIC" を含めてよい（任意）
- VPS で `docker compose up -d --build` を実行し、本番デプロイまで実施する

### やらないこと
- imgbatch ツールへの HEIC 追加
- サーバーサイド変換への変更
- Stripe 料金・プラン変更
- guide.html / landing.html の文言変更
- CSV・テキスト変換カードへの手入れ
- base.html 本体の変更

---

## 完了条件チェックリスト

- [ ] `{% block head %}` 内に heic2any の CDN `<script>` タグが存在する
- [ ] `{% block head %}` 内に libheif-js の CDN `<script>` タグが存在する
- [ ] CDN URL にバージョン番号が明記されている（例: `@0.14.0`）、またはintegrity属性が付与されている
- [ ] `<input id="imgInput">` の `accept` 属性に `.heic,.heif,image/heic,image/heif` が含まれる
- [ ] `<select id="imgFormat">` に `<option value="image/heic">HEIC (実験的)</option>` が存在する
- [ ] `convertImage()` が async 関数として定義されている
- [ ] HEIC ファイル（`file.type` が `image/heic` または `image/heif`、もしくは拡張子 `.heic/.heif`）を入力した場合、heic2any を使ってデコードする分岐が存在する
- [ ] HEIC 出力（`format === 'image/heic'`）が選択された場合、libheif-js を使ってエンコードする分岐が存在する
- [ ] HEIC デコード失敗時に `imgStatus` にエラー文言が表示される処理が存在する
- [ ] HEIC エンコード失敗時に `imgStatus` にエラー文言が表示される処理が存在する
- [ ] 変換処理中に `imgStatus` にローディングを示すテキスト（例: "変換中..."）が表示される処理が存在する
- [ ] 既存の PNG / JPEG / WebP 変換ロジック（canvas.toBlob）が引き続き存在し、非 HEIC パスで呼ばれる
- [ ] VPS で `docker compose up -d --build` を実行済みである
- [ ] `https://tools.ynfactory.online/tools/fileconv/` を開くと画像変換カードが表示され、CDN スクリプト2本のロードがページソースに確認できる

---

## 品質チェック項目（quality-checker 向け）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | HEIC入力デコード分岐が実装されており、heic2any を呼び出している | 機能要件 | 15 |
| 2 | HEIC出力エンコード分岐が実装されており、libheif-js を呼び出している | 機能要件 | 10 |
| 3 | 既存のPNG/JPEG/WebP変換（canvas.toBlob パス）が破壊されていない | 機能要件 | 10 |
| 4 | ファイル未選択・ライブラリ未ロード時の alert または imgStatus 表示が存在する | エラーハンドリング | 8 |
| 5 | HEICデコード失敗時（try-catch 等）に imgStatus へエラーメッセージを出す処理がある | エラーハンドリング | 7 |
| 6 | HEICエンコード失敗時（try-catch 等）に imgStatus へエラーメッセージを出す処理がある | エラーハンドリング | 5 |
| 7 | 変換中ローディング表示（"変換中..." 等）が imgStatus に反映される | UX | 8 |
| 8 | 出力 select に "HEIC (実験的)" ラベルが付与されており、実験的である旨が明示されている | UX | 7 |
| 9 | async/await が convertImage 全体で一貫して使用されており、既存の同期処理と混在していない | コード品質 | 8 |
| 10 | 既存のコードスタイル（命名規則・インデント・コメント形式）と整合している | コード品質 | 7 |
| 11 | CDN URLにバージョン番号が固定されている（フローティングバージョン `@latest` 等ではない） | セキュリティ | 10 |
| 12 | VPS 再ビルド済みで、本番 URL のページソースに CDN 2本が含まれている | デプロイ確認 | 5 |
| 合計 | | | 100 |

---

## 備考

- libheif-js は WASM を含み数 MB のライブラリのため、ページロードへの影響を考慮してロード完了確認（`Module.onRuntimeInitialized` 等）が必要な場合がある。初期化前にエンコードを試みた場合は「ライブラリ初期化中です。しばらくお待ちください」等のメッセージを表示すること。
- heic2any は `Promise` ベースの API を持つため、async/await での呼び出しが自然。libheif-js は WASM 初期化が非同期なため同様に await 対応が必要。
- HEIC 入力の判定は `file.type`（`image/heic` / `image/heif`）で行うが、ブラウザによっては MIME タイプが空になる場合があるため、ファイル名の拡張子（`.heic` / `.heif`）も併用して判定すること。
- 工程分割: 単一工程（index.html 修正 + VPSデプロイ）で完結するため分割なし。
