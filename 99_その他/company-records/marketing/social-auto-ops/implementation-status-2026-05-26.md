---
title: AI集中版 SNS自動運用 実装ステータス
created: 2026-05-26
status: in_progress
---

# AI集中版 SNS自動運用 実装ステータス

## 完了

1. 要件定義を承認済みに更新
   - 5アカウント運用は保留
   - AI活用・AI導入商材に集中
   - X / Threads / Instagram / note / LP の導線を明確化
   - 初期投稿頻度を反映

2. 工程1 現状棚卸し
   - 成果物: `current-state-2026-05-26.md`
   - 自己採点: 92 / 100
   - 判定: 合格

3. 工程3 集客ファネル設計
   - 成果物: `funnel-plan-ai-implementation.md`
   - 自己採点: 91 / 100
   - 判定: 合格

4. 共通投稿キュー仕様
   - 成果物: `queue-schema.md`
   - 1企画から note / X / Threads / Instagram へ展開する形式を定義

5. dry-run用スクリプト
   - 成果物: `scripts/social_auto_ops.py`
   - `create` で投稿キューJSONを生成
   - `preview` で媒体別投稿文を確認
   - 2026-06-09追記: `dry-run` で X / Threads / Instagram の文字数・画像要件・承認状態を検証
   - 2026-06-09追記: dry-run結果を `.company/marketing/social-auto-ops/dry-runs/` にJSON保存
   - `python3 -m py_compile` 合格

6. サンプルキュー生成
   - 成果物: `.company/marketing/social-auto-ops/queue/2026-05-26-ai導入はツール選びより社内説明の1枚から始める.json`
   - X / Threads / Instagram / note CTA への展開を確認済み
   - 2026-06-09追記: LP URLとInstagram画像パスを設定し、X / Threads / Instagram すべて `ready_for_review` でdry-run通過

7. 個別投稿スクリプトのdry-run
   - `scripts/post_to_x.py --dry-run` でX投稿文を検証
   - `scripts/post_to_meta.py instagram ... --dry-run` でInstagramキャプション・画像必須条件を検証
   - `scripts/post_to_meta.py threads ... --dry-run` でThreads投稿文を検証
   - 2026-06-09追記: `scripts/post_to_meta.py` にFacebook Page / Instagramの本番投稿処理を実装。誤投稿防止のため本番投稿時は `--publish-approved` 必須。Instagram本番投稿はMeta仕様により公開HTTPS画像URL必須。Threads本番投稿は別フロー確定後に対応。

## 現時点の運用設計

```text
AIテーマのnote記事
  -> X: 1日2〜3本で問題提起・気づき
  -> Threads: 1日1〜2本で少し長めの補足
  -> Instagram: 週3〜5本で図解・カルーセル
  -> note: 週2本で深く説明
  -> LP: 相談・資料請求・申し込み
```

プロフィール欄:

- X: LP URL
- Threads: LP URL
- Instagram: LP URL
- note: LP URL

本文導線:

- X / Threads: note誘導を主、プロフィールLP誘導を補助
- Instagram: noteまたはプロフィールLPへ誘導
- note: LPへ誘導

## LP / CTA 作成状況

作成済み:

- LP原稿: `03_成果物/outputs/lp/ai-introduction-consult/lp-copy.md`
- 静的LP: `03_成果物/outputs/lp/ai-introduction-consult/index.html`
- LP CSS: `03_成果物/outputs/lp/ai-introduction-consult/styles.css`
- デスクトップ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/desktop-preview.png`
- スマホ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/mobile-preview.png`
- 親しみやすさ改善後のデスクトップ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/desktop-preview-friendly.png`
- 親しみやすさ改善後のスマホ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/mobile-preview-friendly.png`
- 画像強化後のデスクトップ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/desktop-preview-visual.png`
- 画像強化後のスマホ確認画像: `03_成果物/outputs/lp/ai-introduction-consult/mobile-preview-visual.png`
- LP用画像素材:
  - `03_成果物/outputs/lp/ai-introduction-consult/assets/hero-consultation.png`
  - `03_成果物/outputs/lp/ai-introduction-consult/assets/workflow-simplify.png`
  - `03_成果物/outputs/lp/ai-introduction-consult/assets/first-task-workshop.png`
- CTAライブラリ: `.company/marketing/social-auto-ops/cta/ai-introduction-cta-library.md`
- Googleフォーム: `.company/marketing/social-auto-ops/forms/free-ai-diagnosis-google-form-spec.md`

CTA:

- 主CTA: 無料AI導入診断を申し込む
- サブCTA: まずは相談できる業務を確認する
- 公開LP URL: https://sites.google.com/yn-factory.com/ai-lp
- 独自ドメイン候補: https://ai.yn-factory.com （2026-05-28 18:53 JST時点ではDNS未反映 / 未接続）
- Google Sites編集URL: https://sites.google.com/d/1jvOoTZBo9X-GckhUrMMGHmrg8X_BgV5j/p/1IpTs5IWm4Nmoic0BbwAZhCMxAMRnrcAw/edit
- 2026-05-28 追記: `y-nakada@yn-factory.com` 側のGoogle Sitesで簡易LPを作成し、公開設定を「公開」に変更済み
- 2026-05-28 19:10 JST追記: Google Sites版LPを再作成。見出しを「AI導入は、最初の1業務から。」へ変更し、前回HTML版を参考に本文量を増やし、相談シーン画像と業務整理イメージ画像を追加して公開済み
- 2026-05-28 19:11 JST追記: 画像配置を再調整。相談シーン画像をヘッダー背景に設定し、冒頭のインライン画像2点を削除して公開済み
- 2026-05-28 19:35 JST追記: ローカルLPに横幅いっぱいの区切り画像帯を3か所追加。デスクトップ1440pxでは各帯1440x430px、スマホ390pxでは各帯390x210pxで表示確認済み。Google Sites編集画面は直前のクライアントエラー後に操作状態が不安定なため、公開反映は未実施。
- 2026-05-28 19:58 JST追記: Google SitesではなくCloudflare Pagesへ静的LPとして公開。Project=`ynfactory-ai-lp`、公開URL=`https://ynfactory-ai-lp.pages.dev/`。Custom domain `ai.yn-factory.com` はCloudflare Pages側へ追加済みで、DNSのCNAME追加待ち。必要DNS: `ai` CNAME `ynfactory-ai-lp.pages.dev`。
- 2026-05-28 追記: LPの主CTA/ナビCTA/最終CTAをGoogleフォームへ接続済み
- 2026-05-28 追記: `y-nakada@yn-factory.com` でフォームをコピーし、Workspace所有版へ差し替え済み
- 回答用URL: https://docs.google.com/forms/d/e/1FAIpQLScFeFulq-ol1DzeUADBFdORNOFtZYlc4Ap-7j9OqJ8Hcb5W0Q/viewform
- 回答管理シート: https://docs.google.com/spreadsheets/d/17tNacuu6oWTTeaSXzaAC6lqzdLopgefgLAWCjvn0Pag/edit
- 新規回答メール通知: 有効
- 現在のオーナー: y-nakada@yn-factory.com
- 旧フォーム: `yuichi4107@gmail.com` 所有。Googleの同一ドメイン制限により直接譲渡不可だったため、Workspaceアカウントでコピーして移行。

表示確認:

- HTML parse OK
- CSS読み込みOK
- デスクトップスクリーンショット作成済み
- モバイルスクリーンショット作成済み
- 横はみ出し検出なし
- 2026-05-26 追加改善: 文字中心・AI感強めのデザインから、写真/イラストを使った親しみやすい構成へ変更
- ヒーロー画像、Before/After画像、診断ワークショップ画像を追加
- コピーを「AIの話をあなたの仕事の話に変える」方向へ強化

## 未確定事項

1. LP URL
   - ローカルLPは作成済み。
   - Google Sites公開URL: https://sites.google.com/yn-factory.com/ai-lp
   - 独自ドメイン候補 `https://ai.yn-factory.com` は、2026-05-28 18:53 JST時点では名前解決不可。
   - SNSプロフィール・note CTAには、独自ドメイン接続まではGoogle Sites公開URLを使用する。

2. LPの主CTA
   - 無料AI導入診断で確定。
   - フォーム送信先はGoogleフォームで確定。
   - フォームオーナーは `y-nakada@yn-factory.com` に移行済み。

3. Meta Step6
   - Instagram / Threads投稿にはMeta権限とトークンが必要。
   - Page / Instagram向けの権限追加とGraph API Explorerでの短期トークン取得は完了。Threadsは別フローが必要。
   - 2026-06-09追記: dry-runはトークン不要で実行可能。実投稿は長期トークン化・`.env`反映・本番投稿処理実装後に、直前承認を取って実施する。
   - 2026-06-09追記: Developer ConsoleでPage系権限（`pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `pages_manage_metadata`, `business_management`）を追加済み。
   - 2026-06-09追記: Instagramユースケース「Instagramでメッセージとコンテンツを管理」を追加し、コンテンツ管理権限を追加済み。Graph API Explorerで`instagram_basic` / `instagram_content_publish` が選択可能になったことを確認済み。
   - 2026-06-09追記: Graph API ExplorerでPage + Instagram必須権限を選択し、オーナー承認後に`Generate Access Token`を実行済み。Threads権限はGraph API Explorer候補に出ないため別フロー扱い。
   - 2026-06-09追記: オーナー承認後にGraph API Explorerで短期User Access Tokenを生成し、`me/accounts`でPage Access Tokenを取得。保存先は `.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt`（権限 `600`）。付与権限は `business_management`, `instagram_basic`, `instagram_content_publish`, `pages_manage_metadata`, `pages_manage_posts`, `pages_read_engagement`, `pages_show_list` を確認済み。
   - 2026-06-09追記: 確認済みIDは FB Page `1015019845037766` / IG Business Account `17841477801881765`。Threads Tokenは未取得（別フロー必要）。
   - 2026-06-09追記: Step7用スクリプト `scripts/meta_step7_long_lived_token.py` を追加。短期User Tokenを長期化し、Page Access Tokenを再取得して保存ファイルを更新する。`APP_SECRET` は保存済み。初回実行時、短期User TokenがMeta側で `2026-06-08 17:00 PDT` に期限切れ済みだったため、オーナー承認後に短期User Tokenを再発行した。
   - 2026-06-09追記: Step7長期化完了。長期User Token期限は `2026-08-07T22:20:23Z`。長期User Tokenで `me/accounts`、Page Access Tokenで `1015019845037766?fields=instagram_business_account` の読み取り疎通OK。期待権限7件の欠落なし。保存先は `.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt`（権限 `600`）。
   - 2026-06-09追記: `.company/engineering/sns-credentials/.env` にMeta系キーを反映済み（`META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `META_IG_USER_ID` など）。同ディレクトリは `.gitignore` 除外済み。
   - 2026-06-09追記: オーナー承認後、Facebook Page `YN Factory 出版プロデュース` へテキストのみの実投稿テスト成功。投稿ID `1015019845037766_122103484112596516` / URL `https://www.facebook.com/122103484142596516/posts/122103484112596516`。結果ログは `.company/marketing/social-auto-ops/post-results/2026-06-09-facebook-test-post.json`。
   - 2026-06-09追記: オーナー承認後、Instagram `@nakada_yuichi` へ画像URL付きの実投稿テスト成功。Media ID `17865315447690414` / URL `https://www.instagram.com/p/DZXaimDE-nk/`。画像URLは `https://ai.yn-factory.com/assets/first-task-workshop.png`。結果ログは `.company/marketing/social-auto-ops/post-results/2026-06-09-instagram-test-post.json`。

4. Instagram画像運用
   - 初期は1枚図解投稿を優先。
   - 画像生成・ホスト方法はMeta投稿実装時に決める。

## 次にやること

1. `ai.yn-factory.com` のDNS / Google SitesカスタムURL接続を完了する。
2. X / Threads / Instagram / note のプロフィール導線へLP URLを反映する。
3. Threads Tokenの別フローを整理する。
4. 共通キューから承認済み投稿だけを本番投稿へ流す承認UI/承認フラグを実装する。
5. テスト投稿を残すか削除するかを決める（削除も直前承認必須）。
6. note下書き生成とキューを接続する。

## 総合品質チェック

| 項目 | 判定 |
|---|---|
| AI集中方針 | OK |
| 5アカウント保留 | OK |
| 投稿頻度 | OK |
| 短文SNS -> note -> LP 導線 | OK |
| プロフィールLP直接導線 | OK |
| 実投稿前dry-run | OK |
| 認証情報露出なし | OK |
| Meta外部ブロッカー明確化 | OK |
| LP / CTA 初版作成 | OK |
| デスクトップ / モバイル表示確認 | OK |
| 画像追加後の可読性 | OK |
| 画像追加後の横はみ出しなし | OK |

総合スコア: 95 / 100

合格。次工程はLP公開先・フォーム送信先の確定とMeta Step6再開。

2026-05-28 20:25 JST追記: Squarespace Domainsで `ai.yn-factory.com` のCNAMEを `ynfactory-ai-lp.pages.dev` に追加済み。外部DNSでは名前解決を確認済み。Cloudflare Pages側は独自ドメイン検証とSSL証明書発行待ちのため、反映完了までは一時URL `https://ynfactory-ai-lp.pages.dev/` を利用可能。

2026-05-28 20:33 JST追記: LPに離脱防止ポップアップを追加し、Cloudflare Pagesへ再デプロイ済み。PCは画面上部から離脱しようとした時、スマホは一定量スクロール後に表示。CTAはGoogleフォームへ接続。公開URL `https://ynfactory-ai-lp.pages.dev/` で表示確認済み。

2026-05-28 20:57 JST追記: 独自ドメイン `https://ai.yn-factory.com/` が有効化。DNSは `ynfactory-ai-lp.pages.dev` を返し、Cloudflare Pages側の `status` / `validation` / `verification` はすべて `active`。HTTPS 200 とLP本文表示を確認済み。

2026-05-28 22:10 JST追記: 1番目の作業「X / Threads / Instagram / note のプロフィール導線へLP URLを反映」に着手。Chrome確認結果、Xは `y-nakada@yn-factory.com` で新規作成フローに進んだため停止、Threads / Instagram / note はログイン画面。誤アカウント更新を避けるため未反映。プロフィールURL更新チェックリストを `.company/marketing/social-auto-ops/profile-update-checklist-2026-05-28.md` に作成済み。
