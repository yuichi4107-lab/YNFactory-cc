# 工程8: 本番送信前チェックリスト

- **作成日**: 2026-05-04
- **作成者**: executor
- **目的**: 本番DM送信開始前にオーナーが確認・実施すべき事項を網羅する

---

## A. オーナー確認事項（手動）

### A-1. gBizINFO API 設定
- [x] gBizINFO APIトークン本番化完了（`/opt/sales-ops/.env` に `GBIZINFO_API_TOKEN` 設定済み、HTTP 200 確認済み）
- [x] 実APIで長野県の企業取得テスト成功（dryrun: 20件採用 確認済み 2026-05-04）

### A-2. Gmail 送信設定
- [ ] DMの送信元メールアドレス（`yuichi4107@gmail.com`）の確認
  - `.env` の `GMAIL_SENDER_ADDRESS=yuichi4107@gmail.com` が正しいこと
  - 送信者名 `GMAIL_SENDER_NAME=YNファクトリー 代表 中田雄一` を最終確認
- [ ] Gmail OAuth トークン有効性確認（既存運用継続）
  - VPS上で `python scripts/gmail_oauth_setup.py` を実行して有効期限確認
  - 期限切れの場合は再認証手順を実施

### A-3. 特電法表記の最終確認
以下の表記が全DMテンプレートに含まれていること:

| 必須項目 | 確認 | 設定値 |
|---|---|---|
| 送信者名 | [ ] | YNファクトリー 代表 中田雄一 |
| 住所 | [ ] | `.company/sales/templates/ai-advisor-dm/` 内に記載 |
| 連絡先 | [ ] | `GMAIL_REPLY_TO=info@yn-factory.com` |
| 配信停止URL | [ ] | `GMAIL_UNSUBSCRIBE_URL=mailto:info@yn-factory.com?subject=Unsubscribe` |

> **注意**: 現在の `.env` の `GMAIL_REPLY_TO` と `GMAIL_UNSUBSCRIBE_URL` は `yn-factory.com` ドメインになっています。`ynfactory.online` に統一するか確認してください。

### A-4. 安全装置の動作確認
- [x] 1日送信上限: `SALES_OPS_DAILY_SEND_LIMIT=5`（`.env` 設定済み）
  - 初期は5通/日で運用。手応えを確認後に増加を検討
- [x] 送信間隔: `SALES_OPS_SEND_INTERVAL_SEC=60`（1分間隔、設定済み）
- [ ] 送信時間帯設定（営業時間内: 9:00-18:00 JST）
  - `run_send_approved.py` に時間帯チェックロジックが実装されているか確認
  - cron は毎日 02:30 で承認キュー処理（送信は別スクリプト `run_send_approved.py` が担当）

### A-5. ウェビナーURL確認
- [ ] `WEBINAR_URL=https://ynfactory.online/webinar` のURLが実際にアクセス可能であること
  - 現在はプレースホルダーURL。工程4b（Peatix/Zoom設定）完了後に本番URLに更新すること

---

## B. cron 設定確認（自動チェック済み）

| スケジュール | スクリプト | 設定 |
|---|---|---|
| 毎日 02:00 JST | `run_list_builder.py` | ✅ crontab 設定済み |
| 毎日 02:30 JST | `run_personalizer.py` | ✅ crontab 設定済み |
| 手動（承認後） | `run_send_approved.py` | ⚠ 送信は手動承認制 |

**重要**: 送信は `approval_queue` に投入されたDMをオーナーが承認した後、`run_send_approved.py` で実行する手動承認フロー。cron による自動送信は設定されていない（安全設計）。

毎朝の sales-briefing スキルで `approval_queue` の pending DM を確認・承認する。

---

## C. 監視・アラート

### C-1. ログ監視
- [x] ログファイル: `/var/log/sales-ops.log`（cron による出力先として設定済み）
- [ ] ログローテーション設定（logrotate）の確認
  - `/etc/logrotate.d/sales-ops` が存在するか確認
  - 存在しない場合は以下を設定:
    ```
    /var/log/sales-ops.log {
        weekly
        rotate 4
        compress
        missingok
        notifempty
    }
    ```

### C-2. Telegram エラー通知（未実装・オプション）
- [ ] 送信失敗時の Telegram 通知を追加（任意）
  - 参考: `/opt/keiba-unified/keiba-ai-system/scripts/` の Telegram 通知実装
  - `run_send_approved.py` に try/except で Telegram webhook を呼ぶ形で追加可能

---

## D. 初回送信前の最終チェック

### D-1. DM内容目視確認
- [ ] dryrun で5件分のDMを目視確認
  ```bash
  # VPS上で実行
  cd /opt/sales-ops
  SALES_OPS_DRY_RUN=true python scripts/run_personalizer.py
  ```
- [ ] 件名・本文・特電法表記・ウェビナーURLを確認してオーナーOK

### D-2. 段階的送信計画
1. [ ] まず1件だけ `info@ynfactory.online` 宛に手動送信（自分宛テスト）
   ```bash
   cd /opt/sales-ops && SALES_OPS_DRY_RUN=false python scripts/run_send_approved.py --id <queue_id>
   ```
2. [ ] メール受信・レイアウト・リンク動作を確認
3. [ ] 問題なければ残り4件送信
4. [ ] 翌日以降は cron + 手動承認で日次送信

### D-3. スパム判定回避確認
- [ ] 送信元ドメイン（gmail.com）のSPF設定（Gmail は標準設定で OK）
- [ ] DKIMは Gmail が自動設定（問題なし）
- [ ] 初期は5件/日以下で運用（スパム判定リスク最小化）

---

## E. 本番 gBizINFO 設定確認（自動チェック済み）

| 設定項目 | 状態 | 備考 |
|---|---|---|
| GBIZINFO_API_TOKEN | ✅ 設定済み (32文字) | 実API HTTP 200 確認済み |
| GBIZINFO_START_PAGE | 5（推奨） | page 1-4 は公的機関が多い |
| GBIZINFO_PAGES_PER_PREFECTURE | 3（デフォルト） | 1都道府県 30件取得 |
| gBizINFO 非首都圏フィルタ | ✅ 動作確認済み | dryrun で skipped_metro=0 確認 |

---

## チェックリスト完了後の手順

1. `approval_queue` の pending DM（ID=270, YNテスト株式会社宛）を目視確認
2. 内容OKなら削除してリセット（テストデータのため）:
   ```sql
   DELETE FROM companies WHERE id IN (232,233,234,235,236);
   DELETE FROM approval_queue WHERE id=270;
   ```
3. 本番 cron が翌朝 02:00 に list_builder を自動実行 → 02:30 に personalizer → DM生成
4. 翌朝 `sales-briefing` スキルで approval_queue を確認・承認
5. 承認後 `run_send_approved.py` で送信

---

*最終更新: 2026-05-04 工程8 executor*
