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

- 09:00 / 14:00 / 19:00 に1本ずつ自動生成 → Telegram にプレビュー動画＋ボタンが届く
- 難易度バランスは 09:00=初級、14:00=中級、19:00=中級
- **✅承認して投稿** を押すと有効媒体へ自動投稿（結果URLが返ってくる）
- **❌却下** でスキップ、**⏸保留** で後回し
- ネタ帳残り7本以下になると補充アラートが届く → `topics.json` の backlog に追記
- **完全自動化**: `~/shorts-factory/config.yaml` に `queue: {auto_post: true}` と書くだけ（承認スキップ・事後通知）

2026-06-16時点の実運用は、`~/shorts-factory/config.yaml` に
`queue.platforms: [x, youtube, instagram, tiktok]` を設定済み、`auto_post: false` の承認制。
YouTube / TikTok は専用Chromeプロファイルへのログイン確認後に実投稿可能になる。

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
| com.ynfactory.shorts-generate | 09:00 / 14:00 / 19:00 に生成（Driveから最新コードをrsyncしてから実行） |
| com.ynfactory.shorts-approval | 承認デーモン常駐（Telegramボタン処理・投稿実行） |
| com.ynfactory.shorts-chrome | YouTube/TikTok用 常駐Chrome（CDP 9223） |

## YouTube / TikTok 初回ログイン（人間作業）

```bash
launchctl unload ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist
~/shorts-factory/app/scripts/login_youtube.sh   # Chromeが開く→Googleログイン→Studioが見えればOK
~/shorts-factory/app/scripts/login_tiktok.sh    # 必要なら同じ専用ChromeでTikTokログイン
# Chromeを閉じて
launchctl load ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist
~/shorts-factory/.venv/bin/python ~/shorts-factory/app/scripts/check_platforms.py
```

セッション失効時は Telegram に手順つきアラートが届く（投稿は blocked で保全）。

## 手動操作

```bash
cd ~/shorts-factory/app   # または Drive の shorts-factory/
PY=~/shorts-factory/.venv/bin/python
$PY -m src.pipeline                          # ネタ帳から1本生成→キュー→Telegram
$PY -m src.pipeline --difficulty intermediate # 中級ネタを明示生成
$PY -m src.pipeline --topic "..." --no-queue # テーマ指定・キュー登録なし（テスト）
$PY -m src.approval_bot                      # 承認デーモンを手動起動
```

### 失敗媒体だけ自動再投稿・手動再試行

複数媒体投稿で一部だけ失敗した場合、標準では失敗媒体だけ最大2回まで自動再投稿する。
成功済み媒体は `posted` のまま保持され、自動再投稿・手動再試行のどちらでも二重投稿されない。

自動再投稿後も残った場合、キュー全体は `partial_failed` または `failed` になり、Telegramの投稿結果に手動再試行コマンドが出る。

```bash
cd "<Drive>/YNFactory-cc"
python3 shorts-factory/scripts/retry_failed_posts.py --all        # dry-run
python3 shorts-factory/scripts/retry_failed_posts.py <queue_id> --execute
```

自動再投稿の回数や待機秒数は `queue.retry_max_attempts` / `queue.retry_delay_sec` で変更できる。

### SNS別CTA・説明文

投稿時は `src/platform_copy.py` が媒体別の本文を作る。

- X: 短文内に「最初の1業務」軸のCTAを入れ、プロフィール導線へ誘導
- Instagram: 保存訴求とプロフィールの無料AI導入診断へ誘導
- TikTok: 短い説明とプロフィールの無料診断へ誘導
- YouTube Shorts: 説明欄に `utm_source=youtube` 付きLP URLを直接記載

新規キューには `platform_copy` として媒体別本文を保存する。旧キューに `platform_copy` が無い場合も、投稿時に同じルールで自動生成される。

## 設定変更

- 話者変更: `config.yaml` の `speaker_id`（一覧: `$PY -c "from src import tts_voicevox as t; print(t.speaker_names())"`）
- 投稿先の追加: `queue.platforms` に `youtube` / `instagram` / `tiktok` を追加
- 失敗時の自動再投稿: `queue.retry_failed_posts` / `queue.retry_max_attempts` / `queue.retry_delay_sec`
- CTA先LP: `cta.lp_url` / `cta.campaign`
- 投稿頻度・難易度: `content.scheduled_slots` を変更（標準は 9時=初級、14時/19時=中級）
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
| `rsync失敗` が続く | `SHORTS_REPO_ROOT` または `YNFACTORY_ROOT` を確認。`scripts/run_generate.sh` は候補パスを解決し、失敗理由をログに残す |
| 一部媒体だけ投稿失敗 | 標準で失敗媒体だけ最大2回自動再投稿。それでも残る場合は `python3 shorts-factory/scripts/retry_failed_posts.py --all` で対象確認 → `--execute` |

## クレジット・コンプライアンス

- 動画内下部とSNS説明文に `VOICEVOX:ずんだもん／音声・映像はAIで自動生成` を自動挿入（VOICEVOX利用規約のクレジット表記）
- フォントは Noto Sans JP（SIL OFL）
- BGMは初期オフ（権利クリアな音源を `assets/bgm/` に置いた場合のみ使用）
