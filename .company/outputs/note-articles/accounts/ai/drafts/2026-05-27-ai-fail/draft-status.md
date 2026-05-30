# Draft Status

date: 2026-05-27
account_id: you-ai-dx
target_note_url: https://note.com/you_ai_dx
status: blocked_before_note_draft
draft_url: null
posted_url: null

## 完了

- HANDOFF.md、最新TODO、accounts.json、global history、AI account history、AI persona を確認。
- 直近30日の重複を避け、既存の未完了テーマ「社内でAIエージェントを導入して失敗した3つ」を完成対象に選定。
- 反復の多かった旧稿を、約3000字の無料記事として全面修正。
- 画像プロンプト4点と画像配置表を保存。
- 品質チェック 93/100 PASS。

## ブロッカー

- ChatGPT Pro Web での gpt-image-2 / ChatGPT Images 生成を試すため Chrome note-ai プロファイルを起動したが、現在の実行環境では画面取得とComputer Useのウィンドウ検出ができなかった。
- OpenAI API、openai-image-gen スキル、APIキー、課金APIへのフォールバックは禁止のため、画像生成は実行していない。
- note操作前に必要な画面上のログインアカウント照合を実施できないため、note下書きは作成していない。

## 次に必要なこと

1. note-ai プロファイルのChromeを画面操作できる環境で開く。
2. ChatGPT Pro Web で `images/*.prompt.txt` からトップ画像1枚、本文中画像3枚を生成し、`images/` に保存する。
3. note画面でログイン中アカウントが `https://note.com/you_ai_dx` と一致することを確認する。
4. 一致した場合のみ、`note-post-ready.md` をnote下書きに投入し、見出し画像と本文中画像3枚を配置して下書き保存する。
