# 品質チェックレポート（Step 5.5 削除 / ベストエフォート採用置換）

## サマリー
- **スコア**: 76 / 100
- **判定**: FAIL
- **完了条件充足**: 12 / 15 項目

---

## 完了条件チェック

| # | 条件 | 判定 | 備考 |
|---|---|---|---|
| 1 | `Step 5.5` / `Pillow 合成フォールバック` / `composited` / `_clean.png` / `fallback_pages` / `fallback_reasons` / `B路線` が 0 件 | OK | Grep 全キーワードで 0 件確認 |
| 2 | Step 6 の Pillow（PNG→JPEG）が保持されている | OK | L51, L1481, L1492, L1511 で保持確認 |
| 3 | ベストエフォート採用フロー（`needs_manual_review_pages[]` / `needs_manual_review_reasons{}`）が Step 5 本体に追加 | OK | L650, L731-734, L869-876 で記載確認 |
| 4 | progress.json サンプル・フィールド説明・E2E 記述でスキーマ一致 | NG | L910 に `"needs_manual_review": true, "review_reason"` というページ単位フラグ記法が残存し、L898-907 のリスト/辞書形式と矛盾 |
| 5 | `composited.png` 参照が Step 7 に残っていない | OK | Step 7 は `page_{NNN}.png` のみ参照 |
| 6 | codex-handoff モードのフロー（`step5_regen_iter_<n>/` 再ハンドオフ等）とベストエフォート採用が矛盾しない | OK | L660 で「max_iter 超過時: ベストエフォート採用（モード分岐なし）」と明記 |
| 7 | Step 4 `コマ別テキストJSON` が「OCR 判定だけが参照する」に変更され、confirmation bias 回避の意図が残っている | OK | L469 で「OCR 判定だけが参照する」、L470 で confirmation bias 記述確認。ただし L468 に旧 API 名「Gemini」が残存（軽微） |
| 8 | Step 5 冒頭から「100% 正確テキスト保証」「A+B ハイブリッド」が削除されている | OK | 削除確認済み。L646-650 でベストエフォート採用の限界を適切に記述 |
| 9 | コスト試算から `clean regen フォールバック` / `Pillow 合成処理` 行が削除され、合計 `~$33.84/冊` に更新されている | OK | L1938 で `~$33.84/冊` 確認。ただし Step 5 セクション内試算（L931: `$24.15〜$24.75/冊`）と乖離あり（別途バッファ込み試算として説明あり） |
| 10 | `panel_regions.json` の扱い：Pillow 合成専用データファイルであれば削除指示が必要 | NG | `panel_regions.json` の `_meta.description` に「Pillow合成時のテキスト配置座標として使用する」と明記されたままで削除されていない。skill.md 内の参照（L486, L512-525）も整理が不完全 |
| 11 | E2E テストの合格基準テーブル・確認手順がベストエフォート採用ベースで一貫している | OK | E2E セクション 4（L2082-2103）でベストエフォート採用確認手順・合格基準テーブル（L2202）が整備されている |
| 12 | frontmatter / 絶対ルールで「Pillow 合成」の言及が Step 6 PNG→JPEG 以外に残っていない | OK | frontmatter L3 / 絶対ルール L41-47 に Pillow 合成の不適切な言及なし |
| 13 | 「Step 5.5 を参照」等の相互参照リンク切れが残っていない | OK | Grep で 0 件確認 |
| 14 | ベストエフォート採用の説明が複数箇所で矛盾していない | NG | L910 のページ単位フラグ記法（`"needs_manual_review": true, "review_reason"`）が L898-907 のリスト/辞書形式と矛盾 |
| 15 | 見出し番号に飛びがない（Step 5 → Step 6 が自然） | OK | Step 5 → Step 5-QC → Step 6 の順で連番正常 |

---

## 品質スコア詳細

| # | チェック項目 | 配点 | 得点 | 根拠 |
|---|---|---|---|---|
| 1 | Step 5.5 参照の完全消滅（`Step 5.5` / `composited` / `_clean.png` / `fallback_pages` / `fallback_reasons` / `B路線`） | 20 | 20 | Grep 全キーワードで 0 件。完全削除を確認 |
| 2 | Step 6 の Pillow（PNG→JPEG）保持 | 10 | 10 | L51, L1481, L1492, L1511 で Pillow を使った PNG→JPEG 変換が正しく保持されている |
| 3 | ベストエフォート採用フローの一貫性（疑似コード・処理の流れ・progress.json・E2E） | 15 | 11 | 擬似コード（L728-735）・処理の流れ（L869-876）・E2E（L2082-2101）は一貫しているが、L910 に「`"needs_manual_review": true, "review_reason": "{reason}"`をページ単位で追記する」という記法が残存し、L898-907 のリスト/辞書形式と矛盾している。-4点 |
| 4 | progress.json スキーマの整合性 | 10 | 6 | サンプル JSON（L898-902）・フィールド説明（L906-907）・E2E（L2126-2127）は `needs_manual_review_pages[]` / `needs_manual_review_reasons{}` で統一されているが、L910 で `"needs_manual_review": true, "review_reason": "{reason}"` という別形式の追記指示が残存し、実装者が混乱する矛盾となっている。-4点 |
| 5 | EPUB 製本（Step 7）の接続 | 10 | 10 | Step 7 は `page_{NNN}.png` のみ参照（L1572）。`composited.png` 参照なし。ベストエフォートページも `glob("page_*.png")` で自動収集される説明（L1693-1701）が正確 |
| 6 | codex-handoff モードの整合 | 10 | 10 | L660 で「max_iter 超過時: ベストエフォート採用（モード分岐なし）」と明記。iter ごとの再ハンドオフ（`step5_regen_iter_N/`）もベストエフォート採用と矛盾しない |
| 7 | Step 4 `コマ別テキストJSON` 説明 | 10 | 8 | L469 で「OCR 判定だけが参照する」を確認、L470 で confirmation bias 回避の意図も保持。ただし L468 に旧 API 名「Gemini」が残存している（本改修範囲外だが仕様書として不正確）。-2点 |
| 8 | Step 5 冒頭の売り文句変更 | 5 | 5 | 「100% 正確テキスト保証」「A+B ハイブリッド」の削除確認。L647 でベストエフォート採用による限界（max_iter 超過時）を適切に明記 |
| 9 | コスト試算の妥当性 | 5 | 4 | `clean regen フォールバック` / `Pillow 合成処理` 行の削除確認（L1932-1938）。ただし Step 5 セクション内試算（L931: `$24.15〜$24.75/冊`）とコスト見積もりセクション（L1938: `~$33.84/冊`）の乖離について、L933-946 でバッファ込み上限値である旨を説明しており実質矛盾なし。-1点（乖離の読み解きに説明が必要な点） |
| 10 | `panel_regions.json` の扱い | 5 | 1 | `panel_regions.json` の `_meta.description` に「Pillow合成時のテキスト配置座標として使用する」と残存。Pillow 合成専用データファイルであるにもかかわらず削除されておらず、skill.md の L486・L512-525 に参照（`composite_page5.py` 言及含む）も整理されていない。L1007 では「将来の手動レビューツール用に保持」と説明しているが、ファイル自体の`_meta`は旧用途説明のままで不整合。-4点 |
| 11 | E2E テストの整合 | — | — | チェック3・4・5 に含まれるため個別配点なし |
| 12 | frontmatter / 冒頭の整合 | — | — | チェック1に含まれるため個別配点なし |
| 13 | 相互参照リンク切れ | — | (加点なし) | Grep 0 件確認。減点事由なし |
| 14 | 冗長記述・矛盾 | — | (チェック3/4に反映) | L910 の矛盾はチェック3・4で減点済み |
| 15 | 見出し番号 | — | (加点なし) | Step 5 → Step 5-QC → Step 6 で自然。問題なし |
| **合計** | | **100** | **76** | |

---

## 改善指示

### 優先度1: progress.json スキーマの矛盾（チェック4 得点: 6/10）

**問題**: L910 に以下の記述が残存している。

```
- max_iter 超過時は `progress.json` の当該ページに `"needs_manual_review": true, "review_reason": "{reason}"` を追記する
```

この記法はページ単位でフラグを追記するもので、L898-907 で定義された `needs_manual_review_pages[]` リストと `needs_manual_review_reasons{}` 辞書という管理方式と矛盾する。実装者が「どちらの形式で実装すればよいか」判断できない。

**改善方法**: L910 の行を削除し、代わりに以下のように書き換える。

```markdown
- max_iter 超過時は `progress.json` の `needs_manual_review_pages` に当該ページ番号を追加し、
  `needs_manual_review_reasons` に理由キーを記録する（上記フィールド仕様参照）
- ログに `[needs_review] page {NNN}: best-effort accepted (reason={reason}, missing=[キャラ名])` を出力する
```

---

### 優先度2: `panel_regions.json` の未整理（チェック10 得点: 1/5）

**問題**: `panel_regions.json` ファイルの `_meta.description` に「Pillow合成時のテキスト配置座標として使用する」と記述されたままである。このファイルは Pillow 合成フォールバック（Step 5.5）専用データファイルであり、Step 5.5 の削除と同時に用途が消滅した。

加えて skill.md L522-525 に `composite_page5.py`（旧 Pillow 合成プロトタイプ）への言及が残存しており、「Step 5.5 削除後も panel_regions.json は残る」という誤解を与える。

**改善方法**: 以下の2つの対応を行う。

**方法A（推奨）**: `panel_regions.json` を削除し、skill.md の参照を整理する。
- L486: `コマ番号。`panel_regions.json` のキーと対応する` → `コマ番号。テンプレートのコマ番号に対応する整数` に変更
- L512-525 の注記ブロック全体を削除（`composite_page5.py` 参照が Pillow 合成専用のため）
- L1007: `（コマ領域の切り出し機能は現在未使用。将来の手動レビューツール用に保持。）` → 削除

**方法B（保持する場合）**: `panel_regions.json` の `_meta.description` を更新する。
```json
"description": "コミクル2.0 テンプレ1〜7 コマ領域定義。将来の手動レビューツール実装時に参照予定（現在は未使用）。",
```
また skill.md L522-525 の `composite_page5.py` 言及を panel_id の説明から切り離し、現在の用途（未使用・将来保持）を明記する。

---

### 優先度3: L955 「フォールバック合成の期待テキスト源」という表現の残存（チェック3 に関連）

**問題**: L955 に以下の記述がある。

```
本ループの OCR 比較とフォールバック合成の期待テキスト源になる
```

「フォールバック合成」は Step 5.5（Pillow 合成フォールバック）の用語であり、削除後は不適切。

**改善方法**: 以下に変更する。

```
本ループの Blind-OCR 比較の期待テキスト源になる
```

---

### 参考: 軽微な問題（減点なし、任意対応）

**L468 の旧 API 名残存**:

```
**設計の注意（重要）**: この列は画像生成（Gemini）には渡さない。
```

現スキルは gpt-image-2（OpenAI）を使用しており、「Gemini」は旧実装の名称。「画像生成」または「gpt-image-2」に変更することを推奨するが、今回の採点範囲（Step 5.5 削除・ベストエフォート採用置換）の直接的な問題ではないため採点には影響させていない。
