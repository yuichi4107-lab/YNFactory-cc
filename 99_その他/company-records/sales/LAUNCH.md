# Sales OS 軸C 本番稼働記録

> **ステータス**: 初回1通送信済み（自動本番送信は未解放）
> **最終更新**: 2026-06-23（Queue ID 282を実送信済み）

---

## 本番稼働開始記録

| 項目 | 値 |
|---|---|
| 稼働開始日 | 2026-06-23 |
| 初回送信件数 | 1件（Queue ID 282 / TDC） |
| 送信先業種 | 製造業（超精密研磨・鏡面仕上げ）|
| 初回送信承認者 | オーナー（中田 Yuichi） |

---

## 2026-06-22 現況確認メモ

- VPS接続名 `yn-vps` をこのMacのSSH設定に追加し、接続確認済み。
- VPSのSales OSは毎日 02:00 `run_list_builder.py` / 02:30 `run_personalizer.py` がcron実行されている。
- VPS `.env` は `SALES_OPS_DRY_RUN=true` / `SALES_OPS_DAILY_SEND_LIMIT=5` のため、候補生成・下書き生成は安全側で停止中。
- VPSの承認キューは `pending=0`。テスト会社 item_id `270` は `rejected` に変更済み。
- VPS `.env` の `WEBINAR_URL` は `https://ai-webinar-20260715.peatix.com/view`、`CONSULT_BOOKING_URL` は `https://calendly.com/y-nakada-yn-factory/30min-consult` へ更新済み。
- Calendly個別相談URLは `https://calendly.com/y-nakada-yn-factory/30min-consult` を作成し、場所はGoogle Meetへ変更済み。公開予約ページでGoogle Meet系の表示と予約可能時間を確認済み。
- Peatixはグループ `https://yn-factory.peatix.com` と公開イベント `https://ai-webinar-20260715.peatix.com/view` (event_id `5060263`) を作成し、ブラウザで表示確認済み。公開ページの日時は `2026/7/15 (水) 19:00 - 20:30 GMT+09:00`。本文・注意書き・配信参加方法のZoom表記はGoogle Meetへ修正済み。問い合わせ先は `y-nakada@yn-factory.com`。
- 2026-06-23に初回1通のみ実送信済み。VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持しており、自動本番送信は未解放。

**次に必要な作業**:
1. 初回送信後の返信・Peatix申込・Calendly予約を確認する。
2. 追加送信候補をAI側で選定し、宛先・本文を確認してからオーナー承認を取る。
3. 段階的に上限を上げる場合も、VPS `.env` は `SALES_OPS_DRY_RUN=true` を維持し、手動実行時だけ明示承認で1件ずつ外す。

## 2026-06-23 初回下書き確認メモ

- DMテンプレート3種を更新し、Peatix公開URLとCalendly個別相談URLを両方入れる形へ修正。
- Zoom表記はGoogle Meetへ統一済み。
- VPSのpersonalizerに `CONSULT_BOOKING_URL` 差し込みを追加。
- 文面品質修正として、`規模規模` の二重表記、Google Maps業種カテゴリの直出し、HP要約の文字化けを抑制。
- 初回確認用にGoogle Maps候補を16件追加し、下書き5件を作成。
- 品質確認済み下書き: Queue ID `276-280`。
- 5件すべてでPeatix URLあり、Calendly URLあり、Google Meet表記あり、Zoom表記なし、未置換プレースホルダーなし、文字化けなし。
- ただし5件すべて `contact_email` が空のため、現状では送信不可。
- 5件中3件は公益財団法人・中央会などの支援機関で、初回送信先としては優先度低め。
- 旧下書き Queue ID `271-275` は品質修正前のため `rejected_archive` へ退避。
- VPS `.env` は `SALES_OPS_DRY_RUN=true` を維持。実送信は未実行。
- 2026-06-23 06時台: 自己紹介文を「YNファクトリーの中田」と名乗ってから「AI活用アドバイザーとして」へつなぐ表現に更新。テンプレート3種、VPS側、既存pending下書き Queue ID `276-280` へ反映済み。承認済み0件、追加送信0件。オーナー確認OKのため、このテンプレートを正式版として扱う。
- 2026-06-23 07時台: 文面確認用 Queue ID `276-280` は送信対象から外して `rejected_archive` へ退避。候補16件を分類し、支援機関・大手・非ターゲット11件を除外、問い合わせフォームのみ4件を保留、公式会社概要に直接メール掲載があったTDC 1件を初回送信候補に採用。
- 2026-06-23 07時台: Google Maps英語カテゴリ `manufacturer` が製造業テンプレートv1へ入るように修正。TDCの汎用版下書き Queue ID `281` は退避し、製造業向けテンプレートで Queue ID `282` を作成。宛先 `tdc@mirror-polish.com`、Peatix/Calendly/Google Meet/自己紹介/未置換なしを確認済み。承認済み0件、追加送信0件。
- 2026-06-23 07時台: オーナー指示でメールアドレス表記を `y-nakada@yn-factory.com` に統一。VPS `.env` の `GMAIL_SENDER_ADDRESS` / `GMAIL_REPLY_TO` / `GMAIL_UNSUBSCRIBE_URL`、DMテンプレート3種、Queue ID `282` 本文を更新。旧 `info@ynfactory.online` / `info@yn-factory.com` / `yuichi4107@gmail.com` はQueue ID `282` 本文内に残存なし。承認済み0件、追加送信0件。
- 2026-06-23 07時台: Peatix公開イベント本文の問い合わせ先も `y-nakada@yn-factory.com` へ更新。公開ページ表示で新メール表示・旧 `info@yn-factory.com` 残存なしを確認済み。
- 2026-06-23 08時台: Queue ID `282` の本文を最終確認。公式サイト紹介文の切れた表現を自然な文に修正し、件名をウェビナー案内寄りへ調整。宛先 `tdc@mirror-polish.com`、ステータス `pending`、承認日時/送信日時なし。旧メール・Zoom表記・未置換プレースホルダーなし。VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-081253-jst-queue282-copyfix.db`。
- 2026-06-23 09時台: オーナーOK後、Queue ID `282` を1通上限で実送信試行。Gmail API未有効（Google Cloud project `YN Tools` / `gmail.googleapis.com` disabled）でブロックされ、送信0件。Queue ID `282` は安全のため `pending` に戻し、`sent_at` なし。VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-094811-jst-before-send-queue282.db`, `/opt/sales-ops/data/sales_ops_backup_20260623-095157-jst-reset-queue282-after-gmailapi-block.db`。次はGoogle Cloud Consoleで Gmail API 有効化後に再送。
- 2026-06-23 10時台: オーナー承認で Google Cloud project `YN Tools` の Gmail API を有効化し、Queue ID `282` を1通上限で再送。送信成功。宛先 `tdc@mirror-polish.com`、Gmail message id `19ef20982a6e1bc5`、`sent_at=2026-06-23T01:12:50.675619`（UTC）。VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま維持。VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-101245-jst-before-resend-queue282-after-api-enable.db`。
- 2026-06-23 10時台: 送信後監査として、Queue ID `282` の送信内容を `conversations` に記録（conversation_id `1`）。本文ペイロードに送信停止手続きあり。次回以降の見落とし防止として、DMテンプレート3種とVPS fallbackに `配信停止` 明記のフッターを反映。VPS DBバックアップ: `/opt/sales-ops/data/sales_ops_backup_20260623-101648-jst-before-conversation-log-queue282.db`。VPSテンプレート/コードバックアップsuffix: `20260623-101838-compliance-footer`。
- 2026-06-23 10時台: 本番cron確認。crontabは 02:00 `run_list_builder.py` / 02:30 `run_personalizer.py`。`/var/log/sales-ops.log` で 02:00 list_builder dry_run完了（新規リスト287件）と 02:30 personalizer dry_run完了（drafted 0件）を確認。自動送信cronはなし。

---

## 工程8 完了条件チェック

- [x] dryrunモードで5社分の下書きが approval_queue に生成されていること（Queue ID 270 確認）
- [x] オーナー確認前の5件の下書きを作成し、文面品質・ターゲット適合性をAI側で一次レビューしていること（Queue ID 276-280）
- [x] オーナーが初回送信用 Queue ID 282 の下書きを確認し、文面品質・ターゲット適合性をレビューしていること
- [x] 初回送信用の `contact_email` が取得されていること（TDC / Queue ID 282）
- [x] Queue ID 282をオーナーが確認していること
- [x] オーナーが承認した件数のDMが実際に Gmail 経由で送信されていること（初回1件送信済み。最低3件運用は次フェーズ）
- [x] 送信記録が `approval_queue.status = 'sent'` と `conversations` テーブルに残っていること（Queue ID 282は`sent`、conversation_id `1`）
- [x] 送信ログに特電法表記が含まれていることが確認できること（本文ペイロードに送信停止手続きあり。次回テンプレートは`配信停止`を明記済み）
- [x] 本番 cron（02:00/02:30）が正常に動作していること（VPSログで2026-06-23 02:00/02:30実行確認、dry_run維持）

---

## dryrun 完了済み事項（2026-05-04）

- gBizINFO 実 API: 長野県 20件 + Google Maps 5件 = 25件取得（dryrun PASS）
- personalizer: 5社分 DM 生成（業種別バリエーション v1/v2/v3 正常選択確認）
- プレースホルダー残: 0件（全件置換確認）
- approval_queue: ID=270（YNテスト株式会社宛）投入・positioning=ai_advisor 確認
- cron 設定: 02:00/02:30 確認済み
- 詳細: `.company/research/step8-dryrun-result.md`

---

## 本番稼働後のモニタリング計画

### 週次チェック（最初の4週間）
| 指標 | 目標 | 確認場所 |
|---|---|---|
| 送信数 | 5〜20通/週 | `/var/log/sales-ops.log` |
| 返信率 | 1〜3% | Gmail 受信トレイ |
| Bounce率 | < 5% | Gmail 送信ログ |
| ウェビナー申込 | 1件/月（初期） | Peatix 管理画面 |

### 改善トリガー
- 返信率 < 1% が2週間続く → 件名・本文を全面見直し
- Bounce率 > 10% → 取得ソース・メールアドレス品質を確認
- ウェビナー申込 0件/月 → DM内のCTA文言・URLを確認

---

## 次回レビュー予定

- **2週間後**: 初回10〜20件の送信結果レビュー（返信率・Bounce率確認）
- **1ヶ月後**: 商談化率・ウェビナー申込数レビュー
- **3ヶ月後（2026-08）**: KGI（初契約1件）の進捗レビュー

---

*テンプレート作成: 2026-05-04 工程8 executor*
*本番開始時に「準備完了」→「稼働中」に更新し、送信件数・日付を記録すること*
