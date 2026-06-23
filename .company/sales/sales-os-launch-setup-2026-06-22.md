# Sales OS Launch Setup 2026-06-22

## Status

- 作成日: 2026-06-22
- 対象: Sales OS 本番ローンチ前の Peatix / Calendly 実URL作成
- 状態: first_send_candidate_ready_owner_review_needed
- 本番送信: 未実行

## Requirements

### Goal

Sales OS の本番DMに入れる実リンクを用意し、存在しないURL入りのDM生成を防ぐ。

### Scope

- Peatixイベント公開URLを取得する
- Calendly 30分個別相談URLを取得する
- VPSの `WEBINAR_URL` / `CONSULT_BOOKING_URL` を実URLへ差し替える
- `SALES_OPS_DRY_RUN=false` への切り替えは、実URL確認後かつ送信直前の明示承認後に行う

### Do Not Do Yet

- Sales OSの本番送信
- `SALES_OPS_DRY_RUN=false` への切り替え

## Current VPS State

- `SALES_OPS_DRY_RUN=true`
- `SALES_OPS_DAILY_SEND_LIMIT=5`
- `WEBINAR_URL=https://ai-webinar-20260715.peatix.com/view`
- `CONSULT_BOOKING_URL=https://calendly.com/y-nakada-yn-factory/30min-consult`
- approval queue: pending 1件（Queue ID 282、送信未承認）
- 旧URLバックアップ: `/opt/sales-ops/.env.bak-20260622-222046-links`
- DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260622-222123_before_queue_cleanup.db`

## 2026-06-22 Browser Setup Result

- Peatixグループ作成済み: `https://yn-factory.peatix.com`
- Peatixイベント公開済み: `https://ai-webinar-20260715.peatix.com/view`
- Peatix event_id: `5060263`
- Peatix参加者フォーム作成・イベント適用済み: `AI活用ウェビナー事前アンケート`
- Peatix公開ページ表示確認済み: 日時 `2026/7/15 (水) 19:00 - 20:30 GMT+09:00`、Google Meet表記、無料チケット、申込ボタン表示、問い合わせ先 `y-nakada@yn-factory.com`
- Peatix配信設定の参加方法: Google Meet表記へ変更済み。参加URLは開催前日までにPeatix参加者向けメッセージで案内する運用。
- Calendly個別相談URL作成・表示確認済み: `https://calendly.com/y-nakada-yn-factory/30min-consult`
- Calendlyカレンダー競合チェック: `y-nakada@yn-factory.com` のGoogleカレンダー1件のみ。`yuichi4107@gmail.com` は追加しない方針。
- Calendlyの場所設定: `Google Meet` へ変更済み。公開予約ページでは `Web conferencing details provided upon confirmation.` と表示。
- Calendly公開予約ページ: 2026-07-01に `10:00〜17:30` の30分枠が表示されることを確認済み。
- URL到達確認: CalendlyはGET 200。Peatixは自動GETで502が返るが、Chrome上では公開ページを表示確認済み。

## 2026-06-22 VPS Update Result

- VPS `.env` の `WEBINAR_URL` を Peatix公開URLへ更新済み。
- VPS `.env` の `CONSULT_BOOKING_URL` を Calendly公開URLへ更新済み。
- `SALES_OPS_DRY_RUN=true` は維持。
- `SALES_OPS_DAILY_SEND_LIMIT=5` は維持。
- `approval_queue` のテスト会社 item_id `270` は `rejected` へ変更。
- 更新後の `approval_queue` pending件数は `0`。

## 2026-06-23 First Draft Review Result

- Sales OSのDMテンプレート3種を更新し、Zoom表記をGoogle Meetへ統一。
- DMテンプレート3種にPeatix申込URL `{{webinar_url}}` とCalendly個別相談URL `{{consult_booking_url}}` を両方入れる形へ更新。
- VPS `run_personalizer.py` / `personalizer.py` を更新し、`CONSULT_BOOKING_URL` を下書きへ差し込めるようにした。
- 文面品質修正として、従業員規模の二重表記（例: `30〜100名規模規模`）、Google Maps業種カテゴリの直出し、HP要約の文字化けを抑制する処理を追加。
- VPSコードバックアップ:
  - `/opt/sales-ops/src/tracks/c_outbound/personalizer.py.bak.20260623-024513-consult-url`
  - `/opt/sales-ops/scripts/run_personalizer.py.bak.20260623-024513-consult-url`
  - `/opt/sales-ops/src/tracks/c_outbound/personalizer.py.bak.20260623-025124-draft-quality`
- DBバックアップ:
  - `/opt/sales-ops/data/sales_ops_backup_20260623-024632_before_first_5_drafts.db`
  - `/opt/sales-ops/data/sales_ops_backup_20260622-175208_before_redraft_quality_fix.db`（UTC表記。JSTでは2026-06-23 02:52頃）
- Google Maps候補を16件追加し、初回確認用に5件の下書きを作成。
- 旧下書き Queue ID `271-275` は文面品質修正前のため `rejected_archive` へ退避。
- 修正版の下書き Queue ID `276-280` を `pending` として作成。
- 5件すべてで確認済み:
  - Peatix URLあり
  - Calendly URLあり
  - Google Meet表記あり
  - Zoom表記なし
  - 未置換プレースホルダーなし
  - 文字化けなし
  - `規模規模` の二重表記なし
- 注意点:
  - 5件すべて `contact_email` が未取得のため、このままでは送信できない。
  - 5件中3件は公益財団法人・中央会などの中小企業支援機関であり、初回送信先としては優先度低め。
  - 実送信前に、メールアドレス取得と送信対象の絞り込みが必要。
- VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持。実送信は未実行。

## 2026-06-23 Intro Copy Update

- DMテンプレート3種の自己紹介を、先に「YNファクトリーの中田」と名乗ってから「AI活用アドバイザーとして」へつなぐ表現に更新。
- オーナー確認結果: テンプレートはこの文面でOK。以後、この自己紹介を正式版として扱う。
- 新しい冒頭例:

```text
はじめてご連絡いたします。
YNファクトリーの中田と申します。

AI活用アドバイザーとして、
キャリアコンサルタントの国家資格を活かしながら、
人と組織の観点からAI導入を支援しています。
```

- VPSテンプレートとフォールバック文面へ反映済み。
- 既存pending下書き Queue ID `276-280` の本文も同じ自己紹介へ更新済み。
- DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260622-213557_before_intro_update.db`（UTC表記。JSTでは2026-06-23 06:35頃）
- 承認済み0件、追加送信0件。実送信は未実行。

## 2026-06-23 Target Filtering / Contact Acquisition

- オーナー指示「おすすめ通り」により、送信先の質を整える工程へ移行。
- 文面確認用だった Queue ID `276-280` は送信対象から外し、`rejected_archive` へ退避。
- 2026-06-23に追加したGoogle Maps候補16件を棚卸しし、以下に分類。
  - `excluded_not_first_send_target`: 11件（支援機関、公益法人、大手グループ、営業所、非ターゲット）
  - `contact_form_required`: 4件（中小企業本体に近いが公式サイト上は問い合わせフォームのみ）
  - `direct email`: 1件（TDC）
- 直接メールアドレス確認済み:
  - 会社: `㈱ティ･ディ･シー 本社（TDC）`
  - 公式サイト: `https://mirror-polish.com/`
  - 公式会社概要ページ掲載メール: `tdc@mirror-polish.com`
  - Queue ID: `282`
  - テンプレート: `v1`（製造業・人手不足対策）
- 問い合わせフォームのみ確認:
  - `冨田マテックス㈱`: `https://www.tomimateqs.co.jp/contact`
  - `新東北化学工業株式会社 本社`: `https://www.s-zeolite.com/wp/contact/`
  - `丸木医科器械㈱ 本社･仙台支店`: `https://maruki-ms.co.jp/contact`
  - `㈱ソーリンク`: `https://solink.co.jp/contact/`
- 冨田マテックスの `abc@tomimateqs.co.jp` は問い合わせフォームの入力例であり、送信用メールとして採用しない。
- Google Maps英語カテゴリ `manufacturer` などがテンプレート選択でv1に入るように `personalizer.py` を修正。
- TDC向けの汎用テンプレート下書き Queue ID `281` は `rejected_archive` へ退避し、製造業向けテンプレートで Queue ID `282` を作り直した。
- Queue ID `282` の確認結果:
  - 宛先メールあり
  - Peatix URLあり
  - Calendly URLあり
  - Google Meet表記あり
  - Zoom表記なし
  - 未置換プレースホルダーなし
  - 文字化けなし
  - 自己紹介は正式版
- VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持。承認済み0件、追加送信0件。
- DBバックアップ:
  - `/opt/sales-ops/data/sales_ops_backup_20260622-220231_before_target_filtering.db`（UTC表記。JSTでは2026-06-23 07:02頃）
  - `/opt/sales-ops/data/sales_ops_backup_20260622-220401_before_contact_target_update.db`（UTC表記。JSTでは2026-06-23 07:04頃）
  - `/opt/sales-ops/data/sales_ops_backup_20260622-220504_before_tdc_redraft_v1.db`（UTC表記。JSTでは2026-06-23 07:05頃）

## 2026-06-23 Sender Email Unification

- オーナー指示により、Sales OSのメールアドレス表記を `y-nakada@yn-factory.com` に統一。
- DMテンプレート3種の署名・送信者表記を `y-nakada@yn-factory.com` へ更新。
- VPS `.env` の以下を `y-nakada@yn-factory.com` へ更新。
  - `GMAIL_SENDER_ADDRESS`
  - `GMAIL_REPLY_TO`
  - `GMAIL_UNSUBSCRIBE_URL`
- 既存pending下書き Queue ID `282` の本文も更新。
- Queue ID `282` の確認結果:
  - 本文内 `y-nakada@yn-factory.com` あり
  - 旧 `info@ynfactory.online` なし
  - 旧 `info@yn-factory.com` なし
  - 旧 `yuichi4107@gmail.com` なし
  - Peatix / Calendly URLあり
  - 未置換プレースホルダーなし
- VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持。承認済み0件、追加送信0件。
- バックアップ:
  - `/opt/sales-ops/.env.bak.20260623-074253-email-unify`
  - `/opt/sales-ops/data/sales_ops_backup_20260622-224308_before_email_unify_y_nakada.db`（UTC表記。JSTでは2026-06-23 07:43頃）
- Peatix公開イベント本文の問い合わせ先も `y-nakada@yn-factory.com` へ更新し、公開ページ表示で旧 `info@yn-factory.com` が残っていないことを確認済み。

## 2026-06-23 Queue 282 Final Copy Check

- Queue ID `282` はステータス `pending` のまま。承認日時/送信日時なし。
- 宛先: `tdc@mirror-polish.com`
- 件名: `㈱ティ･ディ･シー 本社（TDC）様 / 人手不足対策として、AI活用の無料ウェビナーをご案内します`
- 公式サイト紹介文の途中切れ（`企業情報や超精密`）を、自然な表現へ修正。
- 確認結果:
  - 本文内 `y-nakada@yn-factory.com` あり
  - 旧 `info@ynfactory.online` なし
  - 旧 `info@yn-factory.com` なし
  - 旧 `yuichi4107@gmail.com` なし
  - Peatix / Calendly URLあり
  - Google Meet表記あり、Zoom表記なし
  - 未置換プレースホルダーなし
- VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-081253-jst-queue282-copyfix.db`

## 2026-06-23 Queue 282 First Send

- 2026-06-23 09時台: オーナーOK後、Queue ID `282` を1通上限で実送信試行。Gmail API未有効（Google Cloud project `YN Tools` / `gmail.googleapis.com` disabled）でブロックされ、送信0件。Queue ID `282` は安全のため `pending` に戻した。
- 2026-06-23 10時台: オーナー承認で Google Cloud project `YN Tools` の Gmail API を有効化し、Queue ID `282` を1通上限で再送。
- 送信結果: 成功
  - 宛先: `tdc@mirror-polish.com`
  - Gmail message id: `19ef20982a6e1bc5`
  - `sent_at`: `2026-06-23T01:12:50.675619`（UTC）
  - approval_queue status: `sent`
- VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持。自動本番送信は解放していない。
- VPS DBバックアップ:
  - `/opt/sales-ops/data/sales_ops_backup_20260623-094811-jst-before-send-queue282.db`
  - `/opt/sales-ops/data/sales_ops_backup_20260623-095157-jst-reset-queue282-after-gmailapi-block.db`
  - `/opt/sales-ops/data/sales_ops_backup_20260623-101245-jst-before-resend-queue282-after-api-enable.db`

## 2026-06-23 Queue 282 Post-send Audit

- Queue ID `282` は `approval_queue.status='sent'`、`error_message` なし。
- 送信内容を `conversations` に記録済み（conversation_id `1`、company_id `244`、gmail_message_id `19ef20982a6e1bc5`）。
- Queue ID `282` 本文ペイロードには送信停止手続きあり（`今後のご連絡が不要な場合は...速やかに送信停止いたします`）。
- 次回以降の見落とし防止として、DMテンプレート3種とVPS fallbackの停止表記を `配信停止` 明記へ更新。
- 本番cronは 02:00 `run_list_builder.py` / 02:30 `run_personalizer.py`。`/var/log/sales-ops.log` で 2026-06-23 02:00/02:30 の正常実行を確認（dry_run維持、自動送信cronなし）。
- VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-101648-jst-before-conversation-log-queue282.db`
- VPSテンプレート/コードバックアップsuffix: `20260623-101838-compliance-footer`

## Peatix Event Published

### Basic Info

- イベントタイトル: `【無料ウェビナー】人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選`
- サブタイトル: `キャリアコンサルタント国家資格保持者が「AI＝人を活かす」視点で解説する90分`
- 開催日時: `2026年7月15日（水）19:00〜20:30`
- 開催場所: `オンライン（Google Meet）`
- 参加費: `無料`
- 定員: `30名`
- カテゴリ: `ビジネス > セミナー・勉強会`
- タグ: `AI活用, 中小企業, 人手不足, 地方, DX`
- 申込締切: `2026年7月12日（日）`
- 問い合わせ先: `y-nakada@yn-factory.com`

### Event Body

```text
━━━━━━━━━━━━━━━━━━━━━━━━
【無料ウェビナー】
人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選
━━━━━━━━━━━━━━━━━━━━━━━━

こんな悩みはありませんか？

□ 求人を出しても応募が来ない・採用できない
□ AIが気になるが何から始めればいいかわからない
□ IT予算も専門人材もないのにDXなんて無理だと思っている
□ 少ない人数で業務が回らず社員が疲弊している
□ 「AIで人の仕事がなくなる」と社員が不安がっている

これらの悩みは、正しい視点でAIを活用すれば今すぐ改善できます。

■ ウェビナーで得られること

1. 求人票・採用文章の自動生成
2. 日報・報告書・議事録の自動化
3. 問い合わせ対応・FAQ自動化
4. 社員教育・マニュアル作成の効率化
5. 経営判断を支援するデータ分析・要約

■ キャリアコンサルタント国家資格保持者だからこそ語れる視点

一般的なAIコンサルは「業務効率化・コスト削減」を中心に語ります。
しかし採用・育成・評価の専門家として、私はAIが人材育成・組織強化に
どう貢献するかを経営者目線と社員目線の両方から語ることができます。

「AIで人が不要になる」という不安を払拭し、地方中小企業が
「AIと人が共存する強い組織」を作る方法をお伝えします。

■ 参加者限定 持ち帰り資料（無料）

・すぐ使えるAIプロンプト集PDF
・AI活用ロードマップワークシート
・当日限定: 無料個別相談30分の優先予約権

■ こんな方にお勧めです

・地方で事業を営む中小企業の経営者・経営幹部
・従業員30〜100名程度の製造業・サービス業・小売業・建設業など
・採用難・人材不足・業務効率化に課題を感じている方
・AIが気になるが何から始めれば良いかわからない方

■ 開催概要

・日時: 2026年7月15日（水）19:00〜20:30
・形式: Google Meet（オンライン）
・参加費: 無料
・定員: 30名

■ 講師紹介

中田 Yuichi（ナカタ ユウイチ）
AI活用アドバイザー / キャリアコンサルタント（国家資格）

キャリアコンサルタント国家資格を持つAI活用アドバイザー。
採用・育成・評価の人材領域の専門家として、地方中小企業が
「AIと人を共存させる」組織づくりを支援しています。

■ ご注意事項

・参加費は無料ですが、お申し込みはお早めにお願いします。
・Google Meet が使えるデバイスをご用意ください。
・高額商品の売り込みや無理な勧誘は一切ありません。
・ウェビナー後に「無料個別相談（30分）」のご案内をします。

お問い合わせ: y-nakada@yn-factory.com
```

### Peatix Questionnaire

| 質問 | 種別 | 必須 |
|---|---|---|
| 会社名 | テキスト（一行） | 必須 |
| 業種 | 選択肢（製造業 / 建設業 / 小売業 / 飲食業 / 物流業 / 医療福祉 / サービス業 / その他） | 必須 |
| 従業員数 | 選択肢（10〜30名 / 31〜50名 / 51〜100名 / 101名以上） | 必須 |
| 都道府県 | テキスト（一行） | 必須 |
| 事前に聞きたいこと・現在の課題 | テキスト（複数行） | 任意 |

## Calendly Event Draft

- イベント名: `無料個別相談 30分（AI活用アドバイザー）`
- 時間: `30 minutes`
- 公開URL: `https://calendly.com/y-nakada-yn-factory/30min-consult`
- 利用可能時間: 平日 `10:00〜18:00`
- バッファ: 前後5分
- 受付範囲: 翌日から14日先まで
- 最低予約通知: 24時間前
- 最大予約数: 1日3件
- 場所: Google Meet（予約完了後に会議情報が自動提供される設定）

### Calendly Description

```text
AI活用・業務効率化・採用/人材育成の課題について、30分で現状を整理する無料個別相談です。

こんな方におすすめ:
・人手不足や採用難に悩んでいる
・AIを業務に入れたいが何から始めるか迷っている
・現場に合うAI活用の進め方を相談したい

相談後、必要に応じて次の一手をご提案します。高額商品の売り込みや無理な勧誘はありません。
```

### Calendly Questions

1. 会社名（必須）
2. 相談したい内容・現在の課題（必須）
3. 業種・従業員数（任意）

## Post Login Checklist

- [x] Peatixにログイン
- [x] Peatixイベント作成画面に入力
- [x] Peatix参加者フォームを作成・適用
- [x] 公開直前でオーナー確認（Peatix公開OK）
- [x] Peatix公開URLを取得
- [x] Calendlyにログイン
- [x] Event Typeを作成
- [x] 保存・公開直前でオーナー確認
- [x] Calendly公開URLを取得
- [x] VPS `.env` に実URLを反映
- [x] ブラウザで両URLが表示できることを確認
- [ ] 自動HTTP確認で両URLが200系であることを確認（Calendlyは200、Peatixは自動GETで502のため未達）
- [x] テスト会社pendingを除外
- [x] Calendlyの場所をZoomからGoogle Meetへ変更
- [x] Calendly公開ページで時間候補表示を確認
- [x] DMテンプレートにPeatix URLとCalendly URLを反映
- [x] 初回確認用の下書き5件を作成・品質確認
- [x] 初回送信用のメールアドレス取得（TDC 1件）
- [x] 送信対象から支援機関・非ターゲットを除外
- [x] 初回送信候補1件を作成（Queue ID 282）
- [x] Queue ID 282の本文をオーナーが確認
- [x] 送信直前にオーナー承認を取り、手動実行時のみ `SALES_OPS_DRY_RUN=false` / `SALES_OPS_DAILY_SEND_LIMIT=1` で送信
- [x] Queue ID 282の送信記録を `conversations` に残し、停止表記を確認
- [x] 本番cron（02:00/02:30）の正常実行をVPSログで確認
