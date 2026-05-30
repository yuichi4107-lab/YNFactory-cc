# Draft Status

- date: 2026-05-26
- account_id: you-ai-dx
- note_url: https://note.com/you_ai_dx
- title: AIに渡す仕事は、先に「決裁ライン」を決めるとうまくいく
- status: local_ready_note_draft_blocked_chrome_unavailable
- draft_url: null
- blocker: Chrome window unavailable; Computer Use returned cgWindowNotFound, so ChatGPT Web image generation and note account verification could not be performed safely.

## Notes

OpenAI API、openai-image-genスキル、APIキー、課金APIは使わない。ChatGPT Pro Web画面の gpt-image-2 / ChatGPT Images で画像生成を試行し、不可の場合はAPIにフォールバックしない。

## Blocker Detail

- 2026-05-26 08:xx JST: `open -na 'Google Chrome' --args --profile-directory='note-ai'` を試行。
- Computer Use の `get_app_state` が `cgWindowNotFound` を返した。
- note操作前のログイン中アカウント確認ができないため、note下書き作成は停止。
- ChatGPT Web画面での画像生成も安全に実行できないため、画像は未生成。`image-prompts.md` にプロンプトを保存済み。
