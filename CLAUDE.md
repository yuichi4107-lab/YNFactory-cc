# YNFactory-cc

- 作業開始時は `/start` を実行する（GitHub最新を安全にDriveへ取り込み → `HANDOFF.md` → 当日TODO の順に読む）
- 日付・曜日は推測せずツールで確認し、"明日" 等は絶対日付に変換して保存する
- ルート直下は6バケット固定（`01_コード` `02_設定` `03_成果物` `04_インプット` `05_プロジェクト` `99_その他`）→ `02_設定/docs/folder-structure.md`
- リポジトリ本体は `C:\YNFactory-cc`（Mac は `~/YNFactory-cc`）。`03_成果物/outputs` `04_インプット` `05_プロジェクト` の大半はDriveへのリンク → `02_設定/docs/link-architecture.md`
- リンクを外すとき `rmdir /s /q` を使わない。リンク先（Drive上の成果物）まで消える
- ジャンクションは Python の `is_symlink()` では検出できない。リパースポイント属性で判定する → `02_設定/docs/link-architecture.md`
- Drive側（G:）で `git` を実行しない。gitエラーが出たら `git_drive_guard.py check` → `02_設定/docs/git-drive-safety.md`
- 公開・投稿・送信・購入・削除・本番反映は、実行直前に必ず承認を取る。作業に必要なファイルのダウンロードは承認不要 → `02_設定/docs/approval-rules.md`
- それ以外は自分で判断して進める。細かい手順の指示を待たない
- 作業は 要件定義 → 実行 → 品質チェック の順で進める → `02_設定/docs/quality-loop.md`
- ターミナル出力は200行以内。大量ログ・base64・node_modules を画面に出さない
- セッション終了時は `/handoff` を実行する。`HANDOFF.md` は現況のみ（400行/60KB以内）、履歴は `.company/secretary/handoff-log/` へ → `02_設定/docs/company-ops.md`
