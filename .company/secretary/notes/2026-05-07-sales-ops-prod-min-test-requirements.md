---
created: "2026-05-07"
topic: "Sales OS 軸C 本番送信最小検証 要件定義書"
type: note
tags: [sales-ops, requirements, prod-launch, track-c]
---

# 要件定義書: Sales OS 軸C 本番送信最小検証

## ゴール

`From: info@yn-factory.com` による実送信が1通成立し、VPSログ・DB・受信トレイの三点を目視確認したうえで即ロールバックする。これにより LAUNCH.md 工程8 の残5項目のうち主要4項目を1セッションで閉じる。

---

## スコープ

### やること

- Google Workspace で IMAP/SMTP 有効化および「Send mail as」エイリアス設定（案A：535エラー再挑戦）
- approval_queue への自社テストレコード（YNファクトリー → yuichi4107@gmail.com）1件の手動挿入
- VPS .env を `DRY_RUN=false / DAILY_SEND_LIMIT=1` に一時変更
- /sales-briefing スキルでそのレコードを承認 → 実送信
- 受信側（yuichi4107@gmail.com）で From / 特電法フッター / 署名「中田雄一」/ Reply-To を目視確認
- VPS ログ確認・DB ステータス確認
- LAUNCH.md 工程8 チェック更新
- 即ロールバック（DRY_RUN=true / DAILY_SEND_LIMIT=5 に戻す）
- git commit（ログ・設定ファイルに変更があれば）

### やらないこと

- 既存 pending 50件への手動送信・変更
- 案B（Workspace OAuth 再挑戦）の実施（案Aが成功した場合）
- 案C（gmail.com From のまま運用）の本番化判断
- DAILY_LIMIT の段階引き上げ（5→30→50→100）
- Phase 2 プラン（軸A/B）の着手

---

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程1: Workspace IMAP/SMTP + Send mail as 設定 | エイリアス認証成功の確認（テスト送信OK） | Google Workspace admin.google.com へのアクセス |
| 工程2: approval_queue テストレコード挿入 | queue_id（新規払い出し）と DB レコード確認 | 工程1の完了（From が確定してから挿入） |
| 工程3: .env 一時変更 + 承認 + 実送信 | Gmail 受信成功（メール1通） | 工程2 の queue_id |
| 工程4: 目視確認 + LAUNCH.md 更新 + ロールバック + git commit | LAUNCH.md 更新・ロールバック完了・commit hash | 工程3 の実送信成功 |

---

## 工程1: Workspace IMAP/SMTP 有効化 + Send mail as エイリアス設定

### 完了条件

- [ ] admin.google.com → Gmail → IMAP アクセスを「有効」に変更済みであること
- [ ] yuichi4107@gmail.com の Gmail 設定 → 「メールの送信先を追加」で `info@yn-factory.com` を登録し、確認メールが届いていること
- [ ] 確認コードを入力してエイリアスが「送信者として利用可能」状態になっていること
- [ ] Gmail 作成画面で From ドロップダウンに `info@yn-factory.com` が表示されること（目視確認）
- [ ] 535 エラーが発生しないこと（認証成功）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | IMAP アクセスが admin.google.com 上で「有効」になっていること | 機能要件 | 20 |
| 2 | `info@yn-factory.com` が yuichi4107@gmail.com の送信元として追加完了していること | 機能要件 | 30 |
| 3 | 確認フローが 535 エラーなく完走していること | エラーハンドリング | 30 |
| 4 | Gmail 作成画面の From ドロップダウンでエイリアスが選択可能であること | 機能要件 | 20 |
| 合計 | | | 100 |

### リスク: 535 エラー再発時の代替手順

- **原因候補**: Workspace プランが Business Starter 以下で SMTP リレー非対応 / 2段階認証設定でアプリパスワード未発行 / エイリアスが alias ではなく forwarding 設定にしかなっていない
- **対処A-1**: Google アカウント → セキュリティ → アプリパスワードを発行し、SMTP 認証に使用する
- **対処A-2**: admin.google.com → アプリ → Google Workspace → 設定 → SMTP リレーを明示的に許可する
- **代替案B（案Aが全滅の場合）**: Workspace OAuth（y-nakada@yn-factory.com で OAuth 同意画面を再実行）に切り替える。OAuth ブラウザエラーは別端末・シークレットウィンドウで再挑戦する
- **代替案C（B も不可の場合）**: From=yuichi4107@gmail.com のまま実送信検証だけ先に通す。From 修正は後続チケット化してブロックを外す。この場合 LAUNCH.md 工程8 の「送信者表示」チェックは保留扱いとする

---

## 工程2: approval_queue テストレコード挿入

### 完了条件

- [ ] VPS 上で SQL または運用スクリプト経由でレコードが挿入されること
  - `track='c'`, `item_type='dm'`, `status='pending'`
  - `company_name='YNファクトリー'`（自社）
  - `recipient_email='yuichi4107@gmail.com'`
  - 本文に「中田雄一」署名・`info@yn-factory.com` Reply-To・特電法フッターが含まれること
- [ ] INSERT 後に `queue_id`（ID値）が取得・記録されていること
- [ ] 既存 pending 50件のレコードが変更されていないこと（SELECT COUNT 確認）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | レコードの track / item_type / status / recipient_email が正しい値であること | 機能要件 | 25 |
| 2 | 本文に特電法フッターが含まれていること | 機能要件 | 25 |
| 3 | 本文に「中田雄一」署名と `info@yn-factory.com` Reply-To が含まれていること | 機能要件 | 25 |
| 4 | 既存 pending 50件が変更されていないこと（COUNT 確認） | データ完全性 | 25 |
| 合計 | | | 100 |

---

## 工程3: VPS .env 一時変更 + /sales-briefing 承認 + 実送信

### 完了条件

- [ ] VPS `/opt/sales-ops/.env` の `DRY_RUN=false` / `DAILY_SEND_LIMIT=1` への変更が反映されていること（`docker compose up -d --force-recreate` または `source .env` 相当）
- [ ] /sales-briefing スキルで工程2 で挿入した queue_id のレコードが「承認」操作されること
- [ ] `approval_queue.status` が `'approved'` → `'sent'` に遷移していること
- [ ] `/var/log/sales-ops.log` に `send success` 相当のログ行が出力されていること
- [ ] `conversations` テーブルに 1行追加されていること（direction='outbound'、company_id が自社テストレコードに対応）
- [ ] DAILY_SEND_LIMIT=1 の制約により2通目が送信されないこと

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | DRY_RUN=false が環境変数として読み込まれていること（ログで "DRY_RUN=False" 確認） | 機能要件 | 15 |
| 2 | approval_queue.status が 'sent' になっていること | 機能要件 | 20 |
| 3 | /var/log/sales-ops.log に送信成功ログが記録されていること | 機能要件 | 25 |
| 4 | conversations テーブルに 1行追加されていること | データ完全性 | 20 |
| 5 | DAILY_SEND_LIMIT=1 が守られ2通目が送出されていないこと | エラーハンドリング | 20 |
| 合計 | | | 100 |

---

## 工程4: 受信目視確認 + LAUNCH.md 更新 + ロールバック + git commit

### 完了条件

**受信目視確認（yuichi4107@gmail.com で確認）**
- [ ] From フィールドに `info@yn-factory.com`（または表示名 `中田雄一 <info@yn-factory.com>`）が表示されていること
- [ ] Reply-To ヘッダが `info@yn-factory.com` であること
- [ ] 本文末尾に特電法フッター（「広告」表記・会社名・連絡先）が含まれていること
- [ ] 署名に「中田雄一」が含まれていること

**LAUNCH.md 更新**
- [ ] `.company/sales/LAUNCH.md` の工程8 チェックリストのうち確認済み項目に `[x]` が入っていること

**ロールバック**
- [ ] VPS `.env` が `DRY_RUN=true` / `DAILY_SEND_LIMIT=5` に戻っていること
- [ ] `docker compose up -d --force-recreate`（または相当のコマンド）でロールバック後の設定が反映されていること
- [ ] ロールバック後に `/var/log/sales-ops.log` に DRY_RUN=True のログが出ること（次回 cron 稼働確認）

**git commit**
- [ ] LAUNCH.md 更新・ログメモ等の変更が git commit されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | From / Reply-To / 特電法フッター / 署名「中田雄一」が全件目視確認済みであること | 機能要件 | 35 |
| 2 | LAUNCH.md 工程8 チェックリストが更新されていること | リクエストとの一致度 | 20 |
| 3 | VPS .env が DRY_RUN=true / DAILY_SEND_LIMIT=5 にロールバックされ、設定が反映されていること | エラーハンドリング | 30 |
| 4 | git commit が作成されていること | 完了条件の充足率 | 15 |
| 合計 | | | 100 |

---

## LAUNCH.md 工程8 残5項目との対応関係

| LAUNCH.md チェック項目 | 対応工程 | 備考 |
|---|---|---|
| オーナーが5件の下書きを確認し、文面品質・ターゲット適合性をレビュー | **本検証では対象外**（スコープ外）| 自社1件のみ挿入のため。既存50件レビューは別タスク |
| オーナーが承認した件数のDMが実際に Gmail 経由で送信されていること（最低3件） | 工程3 | 今回は1件。3件要件は後続フェーズ |
| 送信記録が approval_queue.status='sent' と conversations テーブルに残っていること | 工程3 | |
| 送信ログに特電法表記が含まれていることが確認できること | 工程4（受信目視） | |
| 本番 cron（02:00/02:30）が正常に動作していること（VPS ログ確認） | 工程4（ロールバック後の次回 cron 確認） | 翌朝 cron ログで確認。即日クローズは困難。要翌日確認 |

---

## リスク・前提まとめ

| リスク | 対処 |
|---|---|
| 工程1: 535 エラー再発 | 上記「代替手順A-1/A-2/B/C」の順で対処 |
| 工程2: 既存 pending 50件への誤 UPDATE | WHERE 句に `id = <新規ID>` を明示。作業前に COUNT(*) を記録 |
| 工程3: DAILY_SEND_LIMIT=1 設定漏れで複数送信 | .env 変更直後に `echo $DAILY_SEND_LIMIT` で確認してから承認 |
| 工程4: ロールバック忘れ | 工程4 完了条件の最優先チェック項目として扱う。実送信完了直後にロールバックを実行する |
| 工程4: cron が当日中に起動して DRY_RUN=false のまま 50件送信 | ロールバックを工程3 完了から15分以内に行う（02:00/02:30 cron と重ならない時間帯で作業する） |

### 作業推奨時間帯

- VPS cron が `02:00` / `02:30` に稼働するため、誤送信リスクを避けるため **03:00〜01:00 JST（深夜2時台を除く）** に作業する。
- 昼間（09:00〜23:00）が最も安全。

---

## 想定所要時間

| 工程 | 見込み時間 | 備考 |
|---|---|---|
| 工程1 | 30〜60分 | Workspace 設定は UI 操作、535再発時は +30分 |
| 工程2 | 10〜15分 | SQL 直挿入 or スクリプト実行 |
| 工程3 | 15〜20分 | .env 変更 → 承認 → ログ確認 |
| 工程4 | 15〜20分 | Gmail 受信確認 → LAUNCH.md → ロールバック → commit |
| **合計** | **70〜115分** | 535 エラー再発なし想定 |

---

## 備考

- 案A 成功後も、**From の表示名**（`info@yn-factory.com` vs `中田雄一 <info@yn-factory.com>`）は gmail_sender.py の `from_name` 設定次第。工程4 の目視で表示名が「中田雄一」になっているか確認する。なっていなければ gmail_sender.py の修正チケットを別途起票する。
- 本検証は「最小検証」のため、1通成功で工程8 を「実送信確認済み」と見なす。DAILY_LIMIT の段階引き上げ（5→30→50→100）は別タスクとして LAUNCH.md に追記する。
- LAUNCH.md 更新時、工程8 の「本番 cron 確認」項目は翌朝のログ確認後にクローズする（当日中にロールバック済みのため即クローズ不可）。
