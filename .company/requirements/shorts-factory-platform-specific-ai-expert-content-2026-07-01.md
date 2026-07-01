---
date: "2026-07-01"
project: shorts-factory
status: implemented_platform_variants
owner_request: "SNSごとのバズる動画分析を踏まえ、SNSごとに内容を変える。ChatGPT限定からAIツール全般へ広げ、AI専門家としての認知を高める。"
implementation_boundary: "この設計書では実装しない。次工程でオーナー承認後に prompt / topics / generation flow を変更する。"
---

# shorts-factory SNS別コンテンツ設計書

## 1. ゴール

shorts-factory の動画内容を、現在の「ChatGPT活用術」中心から、AI専門家としての認知を高める「AIツール全般・AI導入・業務ワークフロー設計」へ広げる。

同時に、X / Instagram / TikTok / YouTube Shorts へ同一動画を横展開するのではなく、共通テーマからSNS別の動画台本・フック・CTAを作り分ける。

## 2. 背景

現状:

- `shorts-factory/prompts/script_prompt.md` は「AI・ChatGPT活用術」として台本を作る。
- `topics.json` はChatGPT関連テーマが中心。
- `platform_copy.py` は投稿文・CTAをSNS別に分けているが、動画本文そのものは共通。
- CTA先は無料AI導入診断からAI導入コンサル/顧問契約へつなげる設計になっている。

課題:

- ChatGPT小技だけでは「便利な使い方の人」に見えやすい。
- AI専門家として認知されるには、ツール名よりも「選定基準」「業務設計」「導入順序」「失敗回避」「効果検証」を語る必要がある。
- SNSごとに視聴者の温度感・期待値・伸びやすい動画構造が違うため、同一動画の横展開では伸びしろが限定される。

## 3. 設計方針

### 3.1 共通テーマからSNS別に分岐する

1つのsource topicを選び、4媒体それぞれのangleへ変換する。

例:

source topic:

> 会議後の議事録からタスク化までをAIで自動化する

SNS別変換:

- X: AI導入で失敗する会社は、ツール選びから始めている
- Instagram: 保存版。会議後10分でタスク化するAI手順
- TikTok: このAI連携、会議後の仕事を半分にします
- YouTube Shorts: ChatGPT / Gemini / NotebookLMで議事録をタスク化する方法

### 3.2 「AI専門家」に見える内容へ寄せる

専門家認知の中心は、最新ツール紹介ではなく判断軸にする。

優先する表現:

- どの業務からAI化すべきか
- どのツールを、どの条件で選ぶべきか
- AI導入で失敗する会社の共通点
- 人間チェックをどこに残すべきか
- 社内で定着させるには何を標準化すべきか
- 費用対効果をどう測るべきか

避ける表現:

- 「ChatGPTが便利」
- 「このプロンプトを入れるだけ」
- 「誰でもすぐ劇的改善」
- ツール名だけの羅列
- 根拠のない効果保証

## 4. SNS別バズ要因の整理

ここでの「バズる」は、単純な再生数だけでなく、AI導入コンサル/顧問契約につながる見込み客からの保存・共有・プロフィール遷移・相談意欲も含めて評価する。

| SNS | 主な視聴者仮説 | 伸びやすい構造 | 専門家認知の出し方 | 主KPI |
|---|---|---|---|---|
| X | 経営者、個人事業主、AI感度高めの実務家 | 逆張り、問題提起、短い判断軸 | 一言で刺さる見解、導入の落とし穴 | 返信、引用、プロフィール遷移 |
| Instagram | 保存して後で使いたいビジネス層 | 保存版、チェックリスト、3ステップ | 見やすい実務テンプレ、Before/After | 保存、プロフィール遷移 |
| TikTok | 広くAIに興味があるライト層 | 驚き、実演、比較、あるある | 難しいことを一瞬で見せる実演力 | 完走率、共有、フォロー |
| YouTube Shorts | 検索・関連動画から来る学習層 | 明確なHow-to、ツール比較、使い分け | 長期で残る解説、検索語を含むタイトル | 視聴維持、登録、関連視聴 |

## 5. SNS別コンテンツ仕様

### 5.1 X

役割:

- AI導入に関する「見解」を出す場所。
- 拡散よりも、AIに詳しい人・経営者・意思決定者に刺す。

動画仕様:

- 尺: 15〜35秒
- 冒頭: 逆張り/問題提起
- 構成: 誤解 → 判断軸 → まずやる1アクション
- 字幕: 短く強い断定。ただし効果保証はしない
- CTA: 「自社の場合はプロフィールの無料AI導入診断へ」

フック例:

- AI導入で失敗する会社は、だいたい最初にツールを選んでいます
- ChatGPTを増やしても、業務は自動化されません
- AI活用が進まない原因は、社員のITリテラシーではありません

向いているテーマ:

- AI導入の失敗パターン
- 経営者向け判断軸
- 社内展開の順番
- AIツール選定
- 業務自動化の設計

### 5.2 Instagram

役割:

- 保存される実務ノウハウの棚。
- 視聴者に「この人の投稿はあとで見返せる」と思わせる。

動画仕様:

- 尺: 25〜45秒
- 冒頭: 保存する理由を明確化
- 構成: チェックリスト → 手順 → 保存CTA
- 字幕: 1画面1ポイント。見返しやすさ優先
- CTA: 「保存して、AI導入前のチェックに使ってください」

フック例:

- 保存版。AI導入前に必ず見る3項目です
- 社内AIルールは、この順番で作ると迷いません
- AIツール選びで失敗しないチェックリスト

向いているテーマ:

- チェックリスト
- 導入手順
- テンプレート
- 比較表
- Before/After

### 5.3 TikTok

役割:

- 広い認知を取る入口。
- 難しいAI導入論を、実演や驚きで軽く見せる。

動画仕様:

- 尺: 20〜35秒
- 冒頭: 驚き/実演/あるある
- 構成: 悩み → 画面上の変化 → 結果 → CTA
- 字幕: テンポを早く、難語は使いすぎない
- CTA: 「プロフィールの無料診断で最初の1業務を整理できます」

フック例:

- これ、AIに任せると一瞬です
- 会議後に毎回これを手作業しているなら、かなり損です
- ChatGPTだけで頑張るより、この組み合わせの方が早いです

向いているテーマ:

- 実演
- ツール比較
- AI連携
- あるある失敗
- 1分で分かる使い分け

### 5.4 YouTube Shorts

役割:

- 検索・関連動画から長期的に見られる専門コンテンツ。
- 「AI導入の先生」として蓄積される場所。

動画仕様:

- 尺: 35〜55秒
- 冒頭: 検索意図に直結する問い
- 構成: 用途 → ツール候補 → 使い分け → 次アクション
- 字幕: 用語は正確に。タイトルと内容を一致させる
- CTA: 説明欄の無料AI導入診断URL

フック例:

- 議事録AIは、ChatGPTだけでなくNotebookLMも候補です
- 社内ナレッジ検索なら、この3つを使い分けてください
- AI導入の最初の1業務は、こう選びます

向いているテーマ:

- How-to
- ツール比較
- AI導入の基本
- 業務別おすすめ構成
- 検索される悩み

## 6. テーマカテゴリ

ChatGPT限定から、以下のカテゴリへ拡張する。

### 6.1 AIツール比較

- ChatGPT / Claude / Gemini の使い分け
- Perplexityで調査、ChatGPTで整理、Claudeで長文化
- NotebookLMで社内資料を読み込ませる
- Canva / Gamma / Figma系AIで資料化

### 6.2 業務ワークフロー

- 会議後の議事録 → タスク化 → 担当割り
- 営業商談の失注理由分析
- FAQ/問い合わせ返信の下書き化
- SNS投稿案の量産と品質チェック
- 採用面談メモの評価観点整理

### 6.3 AI自動化

- Zapier / Make / n8n による連携
- Google Drive / Gmail / Calendar / Sheets との連携
- 社内ナレッジ検索の自動化
- 定期レポート作成
- SNS投稿の生成と承認フロー

### 6.4 AI導入・定着

- 最初の1業務の選び方
- 社内ルールの作り方
- 情報漏洩リスクの避け方
- 人間チェックを残す場所
- 導入効果の測り方

### 6.5 AI専門家視点

- ツール選びより業務分解が先
- AI化しやすい仕事/しにくい仕事
- 導入が止まる会社の共通点
- 現場に定着するテンプレ設計
- AI顧問が見るべきKPI

## 7. データ設計案

### 7.1 topics.jsonの拡張

現在のtopic文字列中心から、以下のような構造を推奨する。

```json
{
  "topic": "会議後の議事録からタスク化までをAIで自動化する",
  "difficulty": "intermediate",
  "domain": "workflow_automation",
  "business_function": "meeting_ops",
  "primary_tools": ["ChatGPT", "NotebookLM", "Google Docs"],
  "expertise_angle": "tool_selection_and_workflow_design",
  "target_persona": "manager",
  "platform_angles": {
    "x": "AI導入で失敗する会社は、議事録ツール選びから始めている",
    "instagram": "保存版。会議後10分でタスク化するAI手順",
    "tiktok": "会議後の作業、AI連携でここまで減ります",
    "youtube": "ChatGPTとNotebookLMで議事録をタスク化する方法"
  },
  "avoid_angles": ["型化だけで終わる", "ChatGPTだけを万能扱いする"]
}
```

### 7.2 queue itemの拡張

1つのsource topicから複数媒体の動画を作るため、queueには以下を追加する。

```json
{
  "source_topic": "...",
  "content_strategy": {
    "domain": "workflow_automation",
    "expertise_angle": "tool_selection_and_workflow_design",
    "platform_variant_mode": "script_per_platform"
  },
  "script_variants": {
    "x": {"title": "...", "script_path": "..."},
    "instagram": {"title": "...", "script_path": "..."},
    "tiktok": {"title": "...", "script_path": "..."},
    "youtube": {"title": "...", "script_path": "..."}
  }
}
```

## 8. 生成フロー案

### Phase 1: 設計だけ反映

- 本設計書を確定
- テーマカテゴリとSNS別方針を承認
- 既存のChatGPTテーマをAIツール全般テーマへ棚卸し

### Phase 2: ネタ帳拡張

- `topics.json` に新カテゴリを追加
- ChatGPT固定テーマを減らし、AI導入/ツール比較/自動化テーマを増やす
- 重複回避のため、domain / business_function / expertise_angle を持たせる

### Phase 3: プロンプト拡張

- `script_prompt.md` を「AI・ChatGPT活用術」から「AIツール/AI導入/業務自動化」に変更
- platformごとのscript briefを生成できるようにする
- ただし最初は1媒体ずつではなく、4媒体の構成方針を保存するだけでもよい

### Phase 4: SNS別動画生成

選択肢:

1. 軽量実装: 動画は共通、冒頭フックと投稿文だけSNS別
2. 中間実装: 同じ映像構成で台本だけSNS別
3. 本命実装: 4媒体それぞれで台本・タイトル・字幕・投稿文を別生成

推奨:

- まず中間実装。
- 1日3本運用で4媒体すべて完全別動画にすると生成負荷と検証負荷が急に増える。
- まず14:00または19:00の中級枠だけ、SNS別台本を試す。

### Phase 5: 検証

媒体ごとに見るKPIを分ける。

- X: 返信、引用、プロフィールクリック
- Instagram: 保存、プロフィールアクセス、リーチ
- TikTok: 完走率、共有、フォロー
- YouTube: 視聴維持率、登録、検索流入、関連動画流入

## 9. 初期コンテンツ配分

1日3本の方針は維持しつつ、内容の役割を分ける。

| 時刻 | 難易度 | 役割 | 内容例 |
|---|---|---|---|
| 09:00 | beginner | 広く入り口を作る | AIツールの基本、よくある失敗 |
| 14:00 | intermediate | 実務に刺す | 業務別ワークフロー、ツール比較 |
| 19:00 | intermediate/expert | 専門家認知 | AI導入、社内定着、判断基準 |

## 10. 初期テーマ案

### AIツール比較

- ChatGPTとClaude、仕事でどう使い分けるべきか
- Geminiが向いている仕事、向いていない仕事
- Perplexityは検索ではなく調査メモ作成に使う
- NotebookLMで社内資料を検索しやすくする方法
- Canva AIとGammaを資料作成で使い分ける

### 業務ワークフロー

- 会議メモをAIでタスクに変える手順
- 営業の失注理由をAIで分析する方法
- 問い合わせ返信をAIで下書きする時の注意点
- 社内マニュアルをAIで更新しやすくする方法
- SNS投稿をAIで量産して品質を落とさない方法

### AI導入・定着

- AI導入の最初の1業務を選ぶ基準
- 社員にAIを使わせる前に決めるべきルール
- AIで情報漏洩を避ける基本設定
- AI活用が現場に定着しない理由
- AI顧問が最初に見るべき業務フロー

## 11. 実装時の変更対象

想定変更ファイル:

- `.company/marketing/shorts-factory/topics.json`
- `shorts-factory/prompts/script_prompt.md`
- `shorts-factory/src/script_gen.py`
- `shorts-factory/src/platform_copy.py`
- `shorts-factory/src/pipeline.py`
- 必要なら `shorts-factory/src/queue_lib.py`

実装時の注意:

- 既存の重複防止ロジックを壊さない
- 4媒体別生成にする場合、同じsource topic内のvariantは重複扱いにしない
- 過去動画との重複は引き続きtitle / cue signatureで検査する
- SNS別動画を作る場合、Telegram承認画面で「どの媒体向け動画か」が分かるようにする
- 生成失敗時に4媒体すべてを巻き込まないよう、variant単位で失敗/再生成できる設計にする

## 12. 品質基準

設計品質:

- SNSごとの視聴者と動画構造が明確
- ChatGPT限定からAIツール全般へ拡張されている
- AI導入コンサル/顧問契約につながる専門家認知がある
- 既存の1日3本運用と衝突しない
- 実装対象ファイルが明確

コンテンツ品質:

- 冒頭2秒で媒体ごとの視聴者に刺さる
- 1動画1テーマに絞る
- ツール紹介だけでなく判断基準を入れる
- 誇大表現・効果保証を避ける
- CTAが無料AI導入診断と自然につながる

## 13. 参考にしたプラットフォーム指針

- YouTube Help: 視聴維持率、冒頭維持、視聴離脱/再視聴ポイントの分析
  - https://support.google.com/youtube/answer/9314415
  - https://support.google.com/youtube/answer/12942217
- TikTok Business Help: 9:16、TikTok-first、最初6秒のフック、最初3秒の価値提示、複数クリエイティブの継続テスト
  - https://ads.tiktok.com/help/article/creative-best-practices
- X Business: 6〜15秒、キャプション、複数クリエイティブのテスト、動画広告仕様
  - https://business.x.com/en/help/campaign-setup/campaigns-101
  - https://business.x.com/en/help/campaign-setup/creative-ad-specifications
- Instagram for Creators: オリジナルコンテンツ、リコメンド適格性、短尺Reels、アカウント状態
  - https://creators.instagram.com/original-content-guidelines
  - https://creators.instagram.com/blog/instagram-recommendations-eligibility-tips-creators

## 14. 推奨する次アクション

次工程では、いきなり4媒体完全別動画にせず、以下から始める。

1. `topics.json` のテーマ構造をAIツール全般へ拡張する
2. `script_prompt.md` の表現を「AI・ChatGPT活用術」から「AIツール/AI導入/業務自動化」に変える
3. 14:00の中級枠だけ、SNS別台本variantを試験導入する
4. 1週間分の結果を見て、4媒体完全別動画へ広げるか判断する

## 15. 2026-07-01 実装着手メモ

オーナー確認後、初回実装は以下の範囲で進める。

- `topics.json` にAIツール比較・AI導入・業務自動化・AIガバナンス系の構造化テーマを追加する
- `script_prompt.md` をChatGPT限定からAIツール/AI導入/業務自動化へ広げる
- `script_gen.py` に `target_platform` とSNS別方針を渡せる土台を追加する
- `topic_store.py` でtopic entry全体を取り出せるようにし、domain / primary_tools / platform_angles を生成へ流す
- `queue_lib.py` に `content_strategy` / `platform_angles` を保存する
- `platform_copy.py` でSNS別angleを投稿文冒頭へ反映する

この初回実装では、4媒体分の動画を同時に4本レンダリングする処理は入れない。生成負荷・品質検証負荷・Telegram承認UIの複雑化が大きいため、まずは中間実装として「共通動画 + SNS別angle/投稿文 + 手動でtarget_platform指定可能」までに留める。

実装結果:

- `topics.json` に構造化topicを12本追加し、backlogは29本、うちintermediateは13本になった
- `topic_store.next_topic_entry()` を追加し、topic metadataを生成側へ渡せるようにした
- `script_prompt.md` をAIツール/AI導入/業務自動化向けに更新した
- `script_gen.py` に `target_platform` / `platform_guidance` / `topic_context` を追加した
- `queue_lib.py` が `target_platform` / `content_strategy` / `platform_angles` を保存するようにした
- `platform_copy.py` がSNS別angleを媒体別投稿文へ反映するようにした
- `pipeline.py` に `--target-platform` を追加し、SNS別台本寄せのテスト生成ができるようにした
- `README.md` に運用手順を追記した

検証:

- `python3 -m json.tool .company/marketing/shorts-factory/topics.json` PASS
- `python3 -m py_compile shorts-factory/src/topic_store.py shorts-factory/src/script_gen.py shorts-factory/src/pipeline.py shorts-factory/src/queue_lib.py shorts-factory/src/platform_copy.py shorts-factory/tests/test_posting_core.py` PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest shorts-factory/tests/test_posting_core.py` PASS（40 tests）

## 16. 2026-07-01 SNS別動画生成の追加実装

投稿後の確認で、投稿文だけでなく動画ファイル自体をSNS別に分ける必要が明確になったため、Phase 4を追加実装した。

実装内容:

- `content.platform_variant_videos: true` を標準にした
- 通常スケジュール実行時は、有効媒体ごとに `target_platform` を変えて別台本・別動画を生成する
- 1つのsource topicから `x` / `instagram` / `tiktok` / `youtube` の子キューを作る
- 各子キューは対象SNSだけを `enabled: true` にし、同じ動画が4媒体へ横展開されないようにした
- Telegramプレビューに `媒体別動画: <platform>` を表示する
- 従来の共通動画運用は `--single-video` または `content.platform_variant_videos: false` で残した

追加検証:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile shorts-factory/src/config.py shorts-factory/src/queue_lib.py shorts-factory/src/notify.py shorts-factory/src/pipeline.py shorts-factory/src/script_gen.py` PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest shorts-factory/tests/test_posting_core.py` PASS（42 tests）
