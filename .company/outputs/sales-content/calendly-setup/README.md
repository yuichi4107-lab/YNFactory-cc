# Calendly 個別Zoom予約システム — 全体ガイド

> **このファイルの位置づけ**: オーナーが Calendly を実際にセットアップする際の手順書。
> Calendly のアカウント操作は オーナーが手動で行う。AIエージェントはアカウント設定を行わない。
>
> **キャリアコンサルタント国家資格保持** の差別化を全面に出した、信頼感のある予約導線を構築する。

---

## 全体像

```
ウェビナーLP / DM メール
        ↓
  Calendly 予約ページ
  https://calendly.com/yn-factory/30min-consult
        ↓
  予約時フォーム（7項目ヒアリング）
        ↓
  ┌─ 申込者へ: 予約確認メール（Zoom URL 含む）
  └─ オーナーへ: 新規予約通知（Gmail / Slack）
        ↓
  24時間前リマインダー（申込者）
        ↓
  1時間前リマインダー（申込者）
        ↓
  【30分 個別 Zoom 商談】
        ↓
  フォローアップメール（A/B/C 3パターン）
```

---

## Step 1: Calendly アカウントを準備する

### 1-1. アカウント作成 / ログイン

1. ブラウザで `https://calendly.com` を開く
2. 右上「Sign up」または「Log in」をクリック
3. **Google アカウント（info@ynfactory.online）でログイン**を推奨
   - Google Calendar との連携が後で楽になる

### 1-2. プロフィール設定

1. 右上アイコン → **「Account settings」** をクリック
2. **「Profile」** タブを開く
3. 以下を設定:

| 項目 | 設定値 |
|------|--------|
| Name | YN Factory |
| Welcome message | 「AIを活用して経営を加速させたい中小企業の経営者様へ。国家資格キャリアコンサルタントとして、人を活かすAI活用を一緒に考えます。」 |
| Profile image | ロゴまたは顔写真をアップロード |

4. 右上「Save changes」をクリック

---

## Step 2: Event Type（予約枠）を作成する

1. ダッシュボード上部「**+ New event type**」ボタンをクリック
2. 「**One-on-one**」を選択
3. **「Create」**をクリック

詳細な設定項目は `event-type-config.md` を参照。

---

## Step 3: 事前ヒアリング質問を設定する

予約フォームに組み込む質問は `pre-meeting-questions.md` を参照。

Calendly での操作:
1. Event Type の編集画面 → **「Invitee Questions」**タブ
2. 「**+ Add a question**」で質問を追加

---

## Step 4: 自動送信メールを設定する

Event Type の編集画面 → **「Notifications and Cancellation policy」** タブ

| メール種類 | 設定ファイル |
|------------|--------------|
| 予約確認メール（即時送信） | `auto-emails/booking-confirmation.md` |
| 24時間前リマインダー | `auto-emails/reminder-24h.md` |
| 1時間前リマインダー | `auto-emails/reminder-1h.md` |

> フォローアップメール（商談後）は Calendly の自動送信ではなく、オーナーが手動で送る。
> 3パターンは `auto-emails/post-meeting-followup.md` を参照。

---

## Step 5: Google Calendar を連携する

手順は `google-calendar-sync.md` を参照。

連携のメリット:
- Google Calendar の予定が埋まっている時間は Calendly でも予約不可になる
- 予約が入ると Google Calendar に自動で予定が追加される

---

## Step 6: Zoom を連携する

手順は `zoom-integration.md` を参照。

連携のメリット:
- 予約ごとに Zoom URL が自動生成される
- 確認メール・リマインダーに Zoom URL が自動挿入される

---

## Step 7: 公開 URL を確認・コピーする

1. ダッシュボード → 作成した Event Type の「**Share**」ボタン
2. URL をコピー（例: `https://calendly.com/yn-factory/30min-consult`）
3. 以下の場所にこの URL を貼り付ける:
   - ウェビナー LP の CTA ボタン（`{{consult_booking_url}}`）
   - DM メールテンプレートの CTA（`{{webinar_url}}` と同様に管理）
   - 個別 Zoom 商談後のフォローアップメール（B パターン: フォローアップ Zoom 予約）

---

## Step 8: テスト予約を実施する

本番運用前に必ず自分でテスト予約を行い、以下を確認する:

- [ ] 予約ページが正常に表示される
- [ ] 日時選択ができる
- [ ] 事前ヒアリング質問（7項目）が表示される
- [ ] 予約完了後、申込者メール（確認メール）が届く
- [ ] オーナー（info@ynfactory.online）に通知メールが届く
- [ ] Google Calendar に予定が追加される
- [ ] Zoom URL が確認メールに含まれている
- [ ] 24時間前・1時間前のリマインダー設定が入っている（実際の送信はテスト時点では確認不要）

---

## 運用フロー（予約が入った後）

1. **予約通知を受信** → オーナーの Gmail / Google Calendar で確認
2. **事前ヒアリング回答を確認** → 予約者の会社・業種・規模・課題を把握して当日の準備
3. **当日 Zoom を開始** → 台本は `.company/outputs/sales-content/individual-zoom-30min/script.md` を参照
4. **商談後 30 分以内にフォローアップメールを送信**
   - A（即決）: `auto-emails/post-meeting-followup.md` の Pattern A を使用
   - B（検討）: Pattern B を使用（1週間後フォロー Zoom の予約リンクを含む）
   - C（見送り）: Pattern C を使用

---

## キャンセル / リスケジュール対応

Calendly の設定で「キャンセルポリシー」を表示可能:

1. Event Type 編集 → 「Notifications and Cancellation policy」タブ
2. 「**Cancellation Policy**」に以下を入力:

```
ご予約の変更・キャンセルは Zoom 前日 12:00 までにお願いします。
キャンセルリンクは確認メールに記載されています。
当日キャンセルはご遠慮ください。
```

---

## 他ツールとの連携

yntools / sales-ops との連携設計は `integration-with-other-tools.md` を参照。

---

## よくあるトラブルシューティング

| 症状 | 対処 |
|------|------|
| 確認メールが届かない | Calendly の Notifications 設定を再確認。迷惑メールフォルダも確認 |
| Zoom URL が自動生成されない | Zoom 連携が未設定の可能性。`zoom-integration.md` を再確認 |
| Google Calendar と同期されない | `google-calendar-sync.md` の「双方向同期」設定を確認 |
| 予約可能時間が表示されない | 「Availability」設定で平日 10:00-18:00 が正しく設定されているか確認 |
| 無料枠のイベントタイプが1つしか作れない | Calendly Free プランの制限。個別 Zoom 1種類のみで初期運用する |
