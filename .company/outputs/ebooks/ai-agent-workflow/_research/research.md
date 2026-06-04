# リサーチ結果: AIが勝手に仕事する会社の作り方

## メタ情報
- テーマ: 属人化したPC業務をAIエージェント化し、AIが仕事を進める状態を作る
- 生成日: 2026-06-02
- 想定読者: 中小企業経営者、管理職、AI導入担当、個人事業主
- 原典: `source/original_transcript.md`

## 原典から抽出した中核メッセージ
- 2024年型のAI研修は、文章生成・画像生成・動画生成・プロンプト作成に偏りがちで、2026年の実務水準とは差がある。
- 重要なのは「どのAIを使うか」ではなく、生成AIの得意不得意を理解し、業務フローを分解し、AIありの業務設計へ作り替えること。
- 属人化している業務は、担当者の暗黙知を手順・判断基準・入力・出力・例外処理に分解できれば、AI化の対象になる。
- 最初に取り組みやすいのは、ブラウザで行う反復作業、情報取得、転記、連絡文作成、チェック、レポート作成など。
- 人間の役割は不要になるのではなく、目的設定、品質判断、例外判断、責任ある承認に移っていく。

## Layer 1: AIエージェント化の技術前提
OpenAIは2026年3月の記事で、モデル単体の利用から、複雑なワークフローを扱うエージェントへの移行を説明している。エージェントにコンピュータ環境を与えることで、API取得、ファイル操作、レポート作成などの実務成果物を扱えるようになる。Responses APIとシェル、隔離されたコンテナ、ネットワーク制御、スキルなどは「AIが実行する」方向への基盤として位置づけられる。

OpenAIのAgents SDK更新では、エージェントがファイルを調べ、コマンドを実行し、コードを編集し、長いタスクをサンドボックス内で進めることが強調されている。これは、単なるチャットではなく、作業環境を持つAIへの流れを示す。

Claude Codeの公式ドキュメントも、コードベースを読み、ファイルを編集し、コマンドを実行し、開発ツールと連携するエージェント型のコーディングツールとして説明している。原典内の「AIにコードを書かせる」「ツールを作らせる」という主張は、現代のAIコーディング環境と整合する。

## Layer 2: 業務フローと企業導入
Google CloudのGemini Enterprise Agent Platformは、生成AIエージェントを本番環境で構築・デプロイするための安全な環境、Agent Development Kit、モデル選択、エージェント設計を提供している。これは、社内業務のAI化が個人のプロンプト技術だけではなく、運用基盤・データ接続・権限管理の問題になっていることを示す。

Microsoftの2026 Work Trend Indexは、AIを使う人の多くが高付加価値業務に時間を使えるようになったと回答しており、特に高度なAI利用者はマルチステップワークフローや複数エージェントの活用に踏み込んでいる。重要な人間スキルとして、AI出力の品質管理と批判的思考も挙げられている。

IBM Think 2026のレポートは、エージェント構築はライフサイクル全体の一部にすぎず、テスト、デプロイ、運用、監視、ガバナンスの比重が大きいと説明している。これは、導入時に「作って終わり」にしない重要性を裏づける。

## Layer 3: AIツール選定と得意不得意
原典では、生成AIにOCRを任せる例が挙げられている。Google Cloud Vision APIの公式ドキュメントでは、画像からのテキスト検出に `TEXT_DETECTION` と `DOCUMENT_TEXT_DETECTION` が用意され、後者は文書や密なテキスト向けに最適化されている。つまり、文字認識や帳票処理では、生成AIだけでなくOCRやDocument AIなどの専用技術を組み合わせる設計が現実的である。

OpenAIのComputer Useドキュメントは、AIがスクリーンショットを見てクリックや入力などの操作を返し、それを実行環境が処理し、再び画面を返すループを示している。同時に、人間の承認、安全境界、ドメイン制限、破壊的操作の扱いも重要とされる。これは、ブラウザ自動化を始める際の安全設計に直結する。

## Layer 4: 読者ニーズ
想定読者の悩みは、次の五つに集約できる。

- AIを使っているが、メール文や議事録要約で止まっている
- 社内に「あの人しかできない業務」があり、退職・休職・異動がリスクになっている
- AI研修を受けても、自社の業務にどう落とすかが分からない
- エンジニアがいないため、自動化やツール開発は無理だと思っている
- AI導入後の責任、品質、情報漏洩、権限管理が不安で踏み出せない

## Layer 5: 差別化ポイント
本書は、AIツールの紹介本ではなく、属人化した業務をAI化するための「仕事の分解・設計・実装・運用」の本にする。

差別化ポイントは以下。

- ChatGPT、Claude、Geminiなどの比較を目的にせず、業務特性に合わせた選定方法を扱う
- プロンプト集ではなく、業務フロー分解とAIあり業務設計を中心にする
- ブラウザ自動化とAIコーディングを、非エンジニア向けの最初の実践領域として扱う
- 人が不要になる話ではなく、人の役割が品質判断・設計・承認へ移る話として整理する
- 小さく始め、監視し、失敗を回収する運用設計まで入れる

## 参考ソース
- OpenAI, "From model to agent: Equipping the Responses API with a computer environment", 2026-03-11: https://openai.com/index/equip-responses-api-computer-environment/
- OpenAI, "The next evolution of the Agents SDK", 2026-04-15: https://openai.com/index/the-next-evolution-of-the-agents-sdk/
- OpenAI API Docs, "Computer use": https://platform.openai.com/docs/guides/tools-computer-use
- Claude Code Docs, "Overview": https://code.claude.com/docs/en/overview
- Google Cloud, "Gemini Enterprise Agent Platform": https://cloud.google.com/products/gemini-enterprise-agent-platform
- Microsoft WorkLab, "Agents, human agency, and the opportunity for organizations", 2026 Work Trend Index: https://www.microsoft.com/en-us/worklab/work-trend-index/agents-human-agency-and-the-opportunity-for-every-organization
- IBM, "Managing agentic AI’s speed, scale and sprawl: Insights from Think 2026": https://www.ibm.com/think/news/think-2026-ai-recap
- Google Cloud Vision API, "Detect and extract text from images": https://docs.cloud.google.com/vision/docs/ocr

