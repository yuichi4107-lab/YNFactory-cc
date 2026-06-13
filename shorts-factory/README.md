# shorts-factory — 日本語ショート動画 全自動生成・自動投稿システム

テーマ（ネタ帳）→ 台本AI生成 → VOICEVOX音声 → 背景画像 → FFmpeg合成（字幕焼き込み）
→ 機械品質検証 → Telegram承認 → X / YouTube Shorts / Instagram Reels / TikTok 自動投稿。

**ランニングコスト0円構成**（claude CLI＋VOICEVOX＋whisper.cpp＋PILカード画像）。
APIキーを入れるとAI画像等にアップグレード可能。

## 字幕正確性の4層防御（本システムの核）

1. **生成層**: 台本JSONをスキーマ検証（1行≤13文字・読み仮名必須・字幕と読み上げ文のLCS包含≥70%）。違反は自動再生成
2. **合成層**: 字幕1行=TTS1チャンクで個別合成し、**wav実測長から字幕タイミングを機械確定**（ずれは構造上発生しない）。VOICEVOXの読み（audio_query kana）と台本読み仮名を突合し、乖離したらかな直読みへ自動切替。頻出AI用語はユーザー辞書登録（ChatGPT=チャットジィーピィーティィー等、Whisper実測で明瞭発音を選定）
3. **検証層**: 完成動画を whisper.cpp **large-v3-turbo** で逆文字起こし → 台本と**音韻ベース**（pykakasi読み化・数字/長音/濁点/促音の表記ゆれ折り畳み）で行単位CER突合。行CER≤0.20・平均≤0.10 で合格。不合格行はかな直読み再合成→再レンダリング（≤5ループ、進捗なしは早期打ち切り→blocked）
4. **仕様層**: ffprobe（1080x1920/h264+aac/尺/サイズ）・blackdetect・ebur128（-14LUFS）・字幕端点・プレビューフレーム3枚（Telegramで人間も目視）

## 日常運用

- 毎朝 07:30 に1本自動生成 → Telegram にプレビュー動画＋ボタンが届く
- **✅承認して投稿** を押すと有効媒体へ自動投稿（結果URLが返ってくる）
- **❌却下** でスキップ、**⏸保留** で後回し
- ネタ帳残り7本以下になると補充アラートが届く → `topics.json` の backlog に追記
- **完全自動化**: `~/shorts-factory/config.yaml` に `queue: {auto_post: true}` と書くだけ（承認スキップ・事後通知）

## セットアップ（済んでいるもの）

> 新しいMacへ移設する場合: `python3.12 -m venv ~/shorts-factory/.venv && pip install -r requirements.txt`、
> `config.yaml.example`/`secrets.yaml.example` を `~/shorts-factory/` へコピーして編集、
> VOICEVOXエンジンとwhisperモデルを再取得（brew install whisper-cpp p7zip ffmpeg）。
> Playwrightは常駐Chrome(CDP)に接続するため `playwright install` は**不要**。

- venv: `~/shorts-factory/.venv`（python3.12 / openai, tweepy, playwright, pykakasi 等）
- VOICEVOX engine 0.25.2: `~/shorts-factory/voicevox/`（パイプラインがオンデマンド起動）
- whisper.cpp: `brew install whisper-cpp` + `~/shorts-factory/models/ggml-large-v3-turbo.bin`
- フォント: `assets/fonts/NotoSansJP-{Bold,Black}.otf`（OFL）
- 秘密情報: `~/shorts-factory/secrets.yaml`（Telegram=暫定で@mnb121_bot流用）。SNS認証は `.company/engineering/sns-credentials/.env` を自動参照

## launchd 登録（初回）

```bash
cd "<Drive>/YNFactory-cc/shorts-factory/scripts" && ./deploy.sh install
```

| ジョブ | 役割 |
|---|---|
| com.ynfactory.shorts-generate | 毎朝07:30 に1本生成（Driveから最新コードをrsyncしてから実行） |
| com.ynfactory.shorts-approval | 承認デーモン常駐（Telegramボタン処理・投稿実行） |
| com.ynfactory.shorts-chrome | YouTube/TikTok用 常駐Chrome（CDP 9223） |

## YouTube 初回ログイン（工程3の人間作業）

```bash
launchctl unload ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist
~/shorts-factory/app/scripts/login_youtube.sh   # Chromeが開く→Googleログイン→Studioが見えればOK
# Chromeを閉じて
launchctl load ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist
~/shorts-factory/.venv/bin/python ~/shorts-factory/app/scripts/check_youtube_session.py
```

セッション失効時は Telegram に手順つきアラートが届く（投稿は blocked で保全）。

## 手動操作

```bash
cd ~/shorts-factory/app   # または Drive の shorts-factory/
PY=~/shorts-factory/.venv/bin/python
$PY -m src.pipeline                          # ネタ帳から1本生成→キュー→Telegram
$PY -m src.pipeline --topic "..." --no-queue # テーマ指定・キュー登録なし（テスト）
$PY -m src.approval_bot                      # 承認デーモンを手動起動
```

## 設定変更

- 話者変更: `config.yaml` の `speaker_id`（一覧: `$PY -c "from src import tts_voicevox as t; print(t.speaker_names())"`）
- 投稿先の追加: `queue.platforms` に `youtube` / `instagram` / `tiktok` を追加
- AI画像化: `secrets.yaml` に `openai_api_key` か `gemini_api_key` → `images.provider: openai|gemini`
- 台本をOpenAIに: `openai_api_key` 設定 + `llm.provider: openai`

## 障害対応

| 症状 | 対応 |
|---|---|
| Telegramに何も届かない | `tail ~/Library/Logs/shorts-generate.log` / `shorts-approval.log` |
| 品質blocked が続く | `quality_report.json` の `accuracy.lines` を確認。固有名詞なら `src/jp_text.py` の TERM_READINGS に読みを追加 |
| YouTube失敗+スクショ | `~/shorts-factory/logs/yt_fail_*.png` を確認（UI変更ならセレクタ修正） |
| X投稿403 | API無料枠の動画上限。queueは blocked になるので翌日に承認し直す |
| VOICEVOX起動失敗 | `~/shorts-factory/logs/voicevox_engine.log` |

## クレジット・コンプライアンス

- 動画内下部とSNS説明文に `VOICEVOX:ずんだもん／音声・映像はAIで自動生成` を自動挿入（VOICEVOX利用規約のクレジット表記）
- フォントは Noto Sans JP（SIL OFL）
- BGMは初期オフ（権利クリアな音源を `assets/bgm/` に置いた場合のみ使用）
