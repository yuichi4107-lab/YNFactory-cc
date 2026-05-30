# 意味保持版 分割CSV QC

- 作成日: 2026-05-13 07:09:44
- 修正前バックアップ: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/panels/comicle_output_meaning_preserved_split_pre_terms_fix_20260513_070944.csv`
- 復元元CSV: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/panels/comicle_output_exaggerated_pre_readability_20260512_234502.csv`
- 出力CSV: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/panels/comicle_output.csv`
- 明示コピー: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/panels/comicle_output_meaning_preserved_split.csv`
- 分割マップ: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/panels/comicle_output_meaning_preserved_split_map.csv`
- 旧ページ数: 121
- 新ページ数: 287
- 文字数 min/median/max: 0/53/78
- 100字超ページ: 0
- 固有名詞分断チェック: PASS

## 方針
- セリフ・ナレーションは元CSVから復元し、意味を短く言い換えない
- 長文は句点・読点単位で複数ページに分割する
- Nanobanana / ClaudeCode / ChatGPT などの固有名詞は途中で割らない
- 画像生成はいったん停止中。再開前にこのCSVを確認する
