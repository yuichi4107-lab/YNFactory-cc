# YNFactory-cc

- 作業開始時はまず `sync_drive_git.py pull-sync` でGitHub最新をDriveへ取り込み、その後 `.company/secretary/HANDOFF.md` → `.company/secretary/todos/` の順に読む
- 日付・曜日は推測せずツールで確認し、"明日" 等は絶対日付に変換して保存する
- ルート直下は6バケット固定（`01_コード` `02_設定` `03_成果物` `04_インプット` `05_プロジェクト` `99_その他`）→ `02_設定/docs/folder-structure.md`
- 通常作業はDrive側、`git commit` / `push` はローカルGit側 → `02_設定/docs/multi-pc-rules.md`
- Drive側で `git` を実行しない。gitエラーが出たら `git_drive_guard.py check` → `02_設定/docs/git-drive-safety.md`
- 公開・投稿・送信・購入・削除・本番反映は、実行直前に必ず承認を取る。作業に必要なファイルのダウンロードは承認不要 → `02_設定/docs/approval-rules.md`
- それ以外は自分で判断して進める。細かい手順の指示を待たない
- 作業は 要件定義 → 実行 → 品質チェック の順で進める → `02_設定/docs/quality-loop.md`
- ターミナル出力は200行以内。大量ログ・base64・node_modules を画面に出さない
- セッション終了時は `/handoff` を実行する。`HANDOFF.md` は現況のみ（400行/60KB以内）、履歴は `.company/secretary/handoff-log/` へ → `02_設定/docs/company-ops.md`
