# Calendly Event Type 設定詳細

> **概要**: 「無料個別相談 30分（AI活用アドバイザー）」のイベントタイプ設定。
> Calendly の Event Type 編集画面の各タブに対応して記述する。

---

## 基本情報（「What event is this?」タブ）

| 項目 | 設定値 |
|------|--------|
| **イベント名** | 無料個別相談 30分（AI活用アドバイザー） |
| **時間** | 30 minutes |
| **カラー** | 任意（青系が信頼感あり） |
| **Description（説明文）** | 下記参照 |
| **公開 URL** | `https://calendly.com/yn-factory/30min-consult`（作成時に設定） |

### Description（説明文）設定テキスト

```
地方中小企業の経営者・担当者様向けに、AI活用支援の個別ご相談を無料で承っています。

▼ こんな方にお勧めです
・社内でのAI活用をどこから始めればいいか分からない
・採用難・人手不足の解決にAIを活かしたい
・IT導入補助金・持続化補助金を活用したい

▼ ご相談の流れ（30分）
・現状ヒアリング（10分）
・AI活用プランのご提案（10分）
・質疑応答・次ステップ確認（10分）

担当者：YN Factory 代表 / 国家資格キャリアコンサルタント
AIと「人を活かす組織づくり」を両輪で支援します。
```

---

## 日時・空き枠設定（「When can people book this event?」タブ）

### Availability（利用可能時間）

1. 「**Weekly hours**」を選択
2. 以下の通り設定:

| 曜日 | 状態 | 時間帯 |
|------|------|--------|
| 月曜 | ON | 10:00 〜 18:00 |
| 火曜 | ON | 10:00 〜 18:00 |
| 水曜 | ON | 10:00 〜 18:00 |
| 木曜 | ON | 10:00 〜 18:00 |
| 金曜 | ON | 10:00 〜 18:00 |
| 土曜 | OFF | — |
| 日曜 | OFF | — |

> **オーナー判断**: 土日を開放したい場合は ON にしてよい。ただし最初は平日のみが負担が少ない。

### タイムゾーン設定

1. 「**Timezone display**」→「**Display local timezone to invitees**」を選択
2. オーナーのタイムゾーン: **Asia/Tokyo (JST)**

### バッファ時間（Buffer Time）

1. 「**Before event**」: **5 minutes**
2. 「**After event**」: **5 minutes**

> バッファを設定することで、予約が詰まっても準備・後処理の時間が確保できる。

### 受付ウィンドウ（Date Range）

1. 「**Rolling date range**」を選択
2. 「**14 calendar days**」（翌日から2週間先まで）に設定
3. 「**Minimum scheduling notice**」: **24 hours**（当日予約を防ぐ）

> 空き枠が多すぎると信頼感が下がる。2週間先まで見える設計が適切。

### 同時予約数の制限

1. 「**Maximum events per day**」: **3**（最初は無理しない設定）
2. 後で需要に応じて増やす

---

## 通知・キャンセルポリシー（「Notifications and Cancellation policy」タブ）

### メール通知の設定

**Confirmation（予約確認）**:
- 「Send confirmation email to invitee」: **ON**
- カスタムメッセージを設定（`auto-emails/booking-confirmation.md` の内容を使用）

**Reminders（リマインダー）**:
- リマインダー 1: **24 hours before** → メッセージは `auto-emails/reminder-24h.md` を使用
- リマインダー 2: **1 hour before** → メッセージは `auto-emails/reminder-1h.md` を使用

**オーナーへの通知**:
- 「Notify additional guests」または「CC email」に **info@ynfactory.online** を追加

### キャンセルポリシー（Cancellation policy）

```
ご予約の変更・キャンセルは、ご予約日前日の12:00（正午）までにお願いします。
変更・キャンセルはメール内の専用リンクからお手続きいただけます。
当日の急なキャンセルはご遠慮ください。
```

---

## 事前ヒアリング質問（「Invitee Questions」タブ）

詳細は `pre-meeting-questions.md` を参照。

Calendly の操作:
1. 「**Invitee Questions**」タブを開く
2. 「**+ Add a question**」で質問を1つずつ追加
3. 必須（Required）/任意（Optional）を各質問で設定

| # | 質問 | 形式 | 必須/任意 |
|---|------|------|-----------|
| 1 | 会社名 | 1行テキスト | 必須 |
| 2 | 業種 | 1行テキスト | 必須 |
| 3 | 従業員数（目安） | ラジオボタン | 必須 |
| 4 | 都道府県 | 1行テキスト | 必須 |
| 5 | 役職 | 1行テキスト | 必須 |
| 6 | 電話番号 | 電話番号 | 任意 |
| 7 | 事前にお聞きしたいこと（自由記述） | 複数行テキスト | 任意 |

---

## 確認画面設定（「Confirmation page」タブ）

1. 「**Display a confirmation page**」を選択
2. 「**Redirects to an external website**」は使わない（Calendly 標準のサンクスページで十分）
3. 確認ページに表示するメッセージ:

```
ご予約ありがとうございます！
まもなくご登録のメールアドレスに確認メールをお送りします。
当日は Zoom URL からご参加ください。

ご不明な点は info@ynfactory.online までご連絡ください。
```

---

## Event Type 設定完了チェックリスト

- [ ] イベント名「無料個別相談 30分（AI活用アドバイザー）」が設定されている
- [ ] 時間が「30 minutes」に設定されている
- [ ] 平日 10:00-18:00 が利用可能時間として設定されている
- [ ] 土日が OFF になっている
- [ ] バッファ前後5分が設定されている
- [ ] 受付ウィンドウが「翌日〜2週間先」になっている
- [ ] 最低予約通知が「24時間前」になっている
- [ ] 事前ヒアリング質問（7項目）が追加されている
- [ ] 確認メール・リマインダー（24h・1h）が設定されている
- [ ] キャンセルポリシーが表示されている
- [ ] 公開 URL が取得できている
