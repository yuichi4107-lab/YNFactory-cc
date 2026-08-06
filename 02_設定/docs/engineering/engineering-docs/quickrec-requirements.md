---
title: YN-tools QuickRec ツール 要件定義書
status: 承認済み（2026-04-15）
next_action: 工程1（バックエンド基盤）から実装開始
related: yn-tools/apps/ 配下に新規追加予定
---

# 要件定義書: YN-tools 「QuickRec」— ワンタッチ録音＋要約＋Q&Aツール

## ゴール
オーナーがPCで**ホットキー一発**で録音を開始/停止し、自動で文字起こし・要約・Q&A対話までできるツールをYN-toolsに追加する。会議・アイデアメモ・取材・壁打ち等を摩擦ゼロで記録→活用できるようにする。

## 既存資産の確認（重要）
- `yn-tools/app/tools/voiceminutes/` — Whisper文字起こし+議事録生成（OpenAI whisper-1使用）
  - `service.py` の `transcribe_audio()` 関数を **QuickRecでも流用**
- `yn-tools/app/tools/minutes/` — テキスト入力→議事録生成（流用はしない、機能重複のため）
- 認証: `require_tool_access("quickrec")` を既存の仕組みに追加登録が必要

## スコープ（4工程）

### 工程1: バックエンド基盤（yn-tools側）
- `yn-tools/app/tools/quickrec/` 新設
- モジュール:
  - `models.py`: `QuickRecSession`（録音メタ+文字起こし+要約）、`QuickRecQA`（Q&A履歴）
  - `router.py`:
    - `POST /tools/quickrec/api/upload` — 音声アップロード＋処理キックオフ
    - `GET /tools/quickrec/{session_id}` — 結果ページ（HTML）
    - `POST /tools/quickrec/api/{session_id}/ask` — Q&Aエンドポイント
    - `GET /tools/quickrec/` — ダッシュボード（履歴一覧）
  - `service.py`:
    - `transcribe_audio()` — voiceminutes/service.py のものを流用
    - `generate_summary()` — 要約・キーポイント・アクションアイテム抽出（Claude API）
    - `answer_question()` — 文字起こしをコンテキストに質問応答（Claude API）
  - テンプレート: `templates/tools/quickrec/` 配下に `index.html` / `result.html` / `dashboard.html`
- DB migration: alembicで追加
- 認証: 既存`require_tool_access("quickrec")`で統一

### 工程2: デスクトップ常駐アプリ（Windows）
- 配置: `yn-tools/apps/quickrec-desktop/`
- 技術スタック:
  - `pystray` — タスクトレイアイコン
  - `pynput` — グローバルホットキー（Ctrl+Alt+R）
  - `sounddevice` + `soundfile` — 録音（マイク + システム音）
  - `requests` — API呼び出し
  - `keyring` — API トークン安全保存
- 機能:
  - ホットキー押下で録音開始（トレイアイコンが赤●に変化）
  - 再度押下で停止 → 自動アップロード
  - アップ完了後、結果URLをブラウザで自動オープン
  - エラー時はWindows通知
- 配布: `pyinstaller`で単一exe化（スタートアップ登録スクリプトも用意）

### 工程3: Q&Aフロントエンド
- 結果ページに対話UI追加
  - 文字起こし＋要約を上部表示
  - 下部にチャット入力欄（fetch でask APIを叩く）
  - セッションは文字起こし全文+過去QAをコンテキストに Claude API呼び出し
- モバイルブラウザでも使える（Bootstrap流用）

### 工程4: 統合テスト＆ドキュメント
- ローカルで録音→アップ→結果確認→Q&A の一連フロー動作
- VPSへデプロイ（既存 ai-trade-systemと同じコンテナ手順）
- デスクトップアプリをローカルPCにインストール
- README/操作ガイド `yn-tools/apps/quickrec-desktop/README.md` 作成

## 完了条件

### 工程1 (Backend)
- [ ] alembic migration適用でテーブル生成成功
- [ ] POST /upload で音声受け取り→Whisper処理→DB保存→URL返却
- [ ] GET /{id}で結果ページ表示
- [ ] POST /ask で Claude APIから回答取得
- [ ] curlで一連の動作確認

### 工程2 (Desktop)
- [ ] Ctrl+Alt+R でトグル録音が動作
- [ ] トレイアイコンの状態遷移（待機/録音中/アップ中）
- [ ] 録音停止から結果ブラウザオープンまで自動
- [ ] エラー時の通知表示
- [ ] pyinstallerで .exe 生成成功

### 工程3 (Q&A UI)
- [ ] 結果ページで文字起こし・要約・キーポイント・アクションアイテムが表示される
- [ ] チャット欄から質問→回答がストリーミング表示
- [ ] 過去のQ&A履歴が保持される

### 工程4 (Integration)
- [ ] ローカルPCからVPSへの実アップロード成功
- [ ] 30秒・3分・10分の録音で全て正常動作
- [ ] モバイルブラウザで結果ページ＋Q&Aが動作

## 品質基準
- コードスタイル: 既存yn-toolsの規約（async SQLAlchemy、依存性注入）に揃える
- セキュリティ: 音声ファイルはユーザー毎に隔離、tokenはkeyring保存、HTTPS必須
- UX: 録音開始から停止まで3クリック以内、結果閲覧まで10秒以内

## スコープ外（MVP後の課題）
- 録画（画面キャプチャ）機能 — 後日追加
- Mac/Linux版 — 後日追加
- ベクトルDBでの長期記憶Q&A — 当面はコンテキスト注入で対応
- 複数話者識別（diarization）
- 自動タグ付け・カレンダー連携

## 品質チェックのループ上限
- 各工程ごとに最大5回まで修正ループ
- 5回超過時は成果物と不合格項目をオーナーに相談

## 想定工数
- 工程1: 3〜5時間
- 工程2: 4〜6時間（録音デバイス扱い＆pyinstaller試行錯誤込み）
- 工程3: 2〜3時間
- 工程4: 2〜3時間
- **合計: 11〜17時間**

## 次回再開時の最初のアクション
1. `yn-tools/app/tools/voiceminutes/` のコード詳細を読み込み、流用部分を確認
2. `yn-tools/app/tools/quickrec/` ディレクトリ作成
3. `models.py` 実装（QuickRecSession, QuickRecQA）
4. alembic migration 生成・適用
5. router.py の upload エンドポイントから実装開始
