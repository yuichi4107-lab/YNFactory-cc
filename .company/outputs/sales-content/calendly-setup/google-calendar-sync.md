# Google Calendar 連携設定手順

> **目的**: Calendly と Google Calendar を双方向同期させ、予約の衝突を防ぐ。
> **所要時間**: 約10分

---

## 連携のメリット

| メリット | 説明 |
|---------|------|
| ブロック自動化 | Google Calendar に予定がある時間帯は Calendly でも自動的に予約不可になる |
| 予定の自動追加 | Calendly で予約が入ると Google Calendar に自動で追加される |
| Zoom URL の連携 | Zoom 連携と組み合わせると、Google Calendar の予定に Zoom URL が含まれる |
| 衝突防止 | プライベートの予定・他の打ち合わせと Zoom 相談が重複しない |

---

## Step 1: Calendly と Google Calendar を連携する

### 操作手順

1. Calendly にログインした状態で、右上のアバターアイコンをクリック
2. 「**Integrations & apps**」または「**Calendar connections**」をクリック
3. 「**Google Calendar**」を見つけて「**Connect**」をクリック
4. Google のログイン画面が開く → **info@ynfactory.online** でログイン
5. Calendly からのカレンダーアクセス許可を求める画面 → 「**許可**」をクリック
6. 「Connected」と表示されれば連携完了

---

## Step 2: チェック（空き確認）用カレンダーを設定する

Calendly は複数の Google Calendar を「チェック用」として設定できる。
設定したカレンダーに予定があれば、その時間帯は予約不可になる。

### 操作手順

1. Calendly 設定 → 「**Calendar connections**」
2. 「**Check for conflicts**」の欄に表示されるカレンダーリストを確認
3. 以下のカレンダーを **チェックマーク ON** にする:
   - メインカレンダー（info@ynfactory.online）
   - 個人のプライベートカレンダー（もしあれば）
   - sales-ops の予定を管理しているカレンダー（もしあれば）

---

## Step 3: 追加（書き込み）用カレンダーを設定する

Calendly での予約が入ったとき、どのカレンダーに予定を書き込むかを設定する。

### 操作手順

1. Calendly 設定 → 「**Calendar connections**」
2. 「**Add to calendar**」の欄でカレンダーを選択
3. **「info@ynfactory.online（メインカレンダー）」** を選択
4. 「Save」をクリック

---

## Step 4: 予定の衝突検出テストをする

1. Google Calendar でテスト用の予定を作成（例: 明日の 14:00-15:00 に「テスト予定」）
2. Calendly の予約ページを開く（`https://calendly.com/yn-factory/30min-consult`）
3. 明日の 14:00 が選択不可（グレーアウト）になっていれば成功
4. テスト予定を削除して元に戻す

---

## Step 5: 双方向同期の確認

1. Calendly でテスト予約を行う（別のメールアドレスで）
2. Google Calendar を開き、予約時間帯に「無料個別相談 30分」の予定が追加されているか確認
3. 予定の詳細に Zoom URL が含まれているか確認

---

## よくある問題と対処

| 症状 | 原因 | 対処 |
|------|------|------|
| Google Calendar と連携できない | ブラウザのポップアップブロック | ポップアップを許可してから再試行 |
| 予定が追加されない | 「Add to calendar」で正しいカレンダーが未選択 | Step 3 を再確認 |
| Google Calendar の予定が反映されない | 「Check for conflicts」で対象カレンダーが未選択 | Step 2 を再確認 |
| 同期に遅延がある | Calendly のリフレッシュ間隔（通常数分） | しばらく待ってから再確認 |

---

## メモ: 複数デバイスでの確認

オーナーが複数の PC（自宅・職場等）を使っている場合:
- Google Calendar はクラウド同期なので、どのデバイスからでも同じ状態が見られる
- Calendly もブラウザ/アプリでログインすれば同じ設定が使える
- スマートフォンの Google Calendar アプリでも予約通知を受け取れる（推奨）
