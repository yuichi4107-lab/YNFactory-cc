# yntools / sales-ops との連携設計

> **このファイルの位置づけ**: Calendly を中心とした予約システムと、
> 既存の sales-ops パイプライン・yntools との連携設計を記述するオプション資料。
> 初期運用では本ファイルの実装は不要。商談件数が月5件を超えた段階で検討する。

---

## 全体の連携図

```
[ウェビナー LP / DM メール]
         ↓ CTA クリック
[Calendly 予約ページ]
         ↓ 予約完了
    ┌────────────────────────────────┐
    │  Calendly Webhooks / Zapier    │
    └──────────┬─────────────────────┘
               │
    ┌──────────┼──────────────────────┐
    ↓          ↓                      ↓
[Gmail 通知]  [sales_ops.db 記録]   [Google Calendar]
(オーナー)   (Zoom 後フォロー管理)  (Zoom URL 付き)
```

---

## 連携 1: Calendly → sales_ops.db（予約記録の自動登録）

### 概要

Calendly で予約が入ったとき、予約者情報を sales_ops.db の `consultations` テーブルに自動記録する。

### 実装方法（オプション）

**方法 A: Calendly Webhooks（無料・プログラミング必要）**

Calendly はイベント発生時に Webhook を送信できる（無料プランでも利用可能）。

```
Calendly Webhook → VPS エンドポイント → sales_ops.db INSERT
```

1. Calendly 設定 → 「**Integrations**」→「**Webhooks**」
2. 「**+ New Webhook Subscription**」をクリック
3. Webhook URL: `https://[VPS IP または ドメイン]/api/calendly-webhook`
4. Events: `invitee.created`（予約作成時）、`invitee.canceled`（キャンセル時）を選択

VPS 側に受信エンドポイントを作成する（Flask / FastAPI 等）:
```python
# 例（疑似コード）
@app.post("/api/calendly-webhook")
def calendly_webhook(payload: dict):
    if payload["event"] == "invitee.created":
        # 予約情報を sales_ops.db に記録
        db.execute("""
            INSERT INTO consultations (
                customer_name, company, industry, employee_count,
                prefecture, role, email, phone,
                zoom_url, scheduled_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled')
        """, [...])
```

**方法 B: Zapier / Make（ノーコード・有料プランが必要になる場合あり）**

1. Zapier でアカウントを作成
2. Trigger: 「Calendly - Invitee Created」
3. Action: 「Google Sheets に行を追加」または「Gmail で通知を送信」
4. Zapier 経由で sales_ops.db への記録は難しいため、Google Sheets で管理する運用が現実的

---

## 連携 2: Calendly → Gmail 通知（現在の手動運用の補助）

### 現状（手動）

Calendly から info@ynfactory.online に予約通知が届く。
オーナーがメールを確認して対応する。

### 強化案（オプション）

Calendly の予約通知メールに、sales-ops パイプラインへの記録を促すリマインダーを含める:

```
新しい予約が入りました。

予約者: {{invitee_full_name}}
会社名: {{company_name}}（Q1 の回答）
業種: {{industry}}（Q2 の回答）

→ 商談後に sales_ops.db への記録をお忘れなく
```

---

## 連携 3: 商談後フォロー管理（Google Sheets 簡易 CRM）

### 概要

現状の sales_ops.db は DM 送信管理が中心で、商談後のフォロー管理機能は未実装。
月5件未満の段階は Google Sheets での手動管理で十分。

### Google Sheets の構成（商談管理シート）

| カラム | 内容 |
|--------|------|
| 商談日 | 予約日時 |
| 会社名 | Q1 の回答 |
| 業種 | Q2 の回答 |
| 従業員数 | Q3 の回答 |
| 都道府県 | Q4 の回答 |
| 担当者名 | 予約者氏名 |
| メール | 予約者メールアドレス |
| ヒアリングメモ | 当日のメモ |
| 推奨プラン | L1 / L2 / L3 |
| パターン | A（即決）/ B（検討）/ C（見送り） |
| フォローアップ送信日 | 送信した日付 |
| フォロー Zoom 予約日 | Pattern B の場合 |
| 最終ステータス | 契約 / 検討中 / 見送り |
| 備考 | |

---

## 連携 4: Calendly URL を DM / ウェビナー LP に組み込む

### DM テンプレートとの連携

既存の DM テンプレート（`.company/sales/templates/ai-advisor-dm/`）の
`{{webinar_url}}` プレースホルダーと同様に、個別相談 URL を CTA に組み込む。

**方法**:
1. DM テンプレート内に個別相談 URL を追加する箇所を設ける（例: PS 文）
2. run_personalizer.py で `{{consult_booking_url}}` として差し込む

```markdown
P.S. もし個別にお話を聞きたい場合は、以下の URL から
30分の無料相談をいつでもご予約いただけます。
https://calendly.com/yn-factory/30min-consult
```

### ウェビナー LP との連携

工程4（ウェビナー基盤）の LP 内 CTA ボタンに Calendly URL を使用する。

- CTA ボタンテキスト例: 「個別相談を予約する（無料・30分）」
- リンク先: `https://calendly.com/yn-factory/30min-consult`
- LP の `{{consult_booking_url}}` プレースホルダーに代入する

---

## 優先度と実装タイミング

| 連携 | 優先度 | 実装タイミング |
|------|--------|----------------|
| Calendly → Gmail 通知 | 必須（初期） | Calendly 設定時に同時に完了 |
| Calendly URL → LP / DM | 必須（初期） | Calendly URL 確定後すぐ |
| Google Sheets 商談管理 | 推奨（初期） | 月1件目の商談後に開始 |
| Calendly → sales_ops.db Webhook | オプション | 月5件超えたら検討 |
| Zapier 自動化 | オプション | 月10件超えたら検討 |

---

## 注意事項

- Calendly 無料プランでは Webhook が使えない場合がある（Standard プラン以上が必要）
- sales_ops.db の DM 管理とは独立して運用してよい（コンサル商談は別の DB テーブルで管理）
- 初期は手動管理で十分。自動化はオペレーションが安定してから検討する
