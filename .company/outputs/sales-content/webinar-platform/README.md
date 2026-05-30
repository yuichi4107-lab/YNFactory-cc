# ウェビナー集客基盤 運用ガイド

**作成日**: 2026-05-04
**対象ウェビナー**: 人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選
**担当**: 中田 Yuichi（YN Factory）

---

## ファイル構成

```
webinar-platform/
├── README.md                              ← このファイル（全体運用ガイド）
├── landing-page.html                      ← ウェビナーLP（HTML/CSS/JS完結）
├── signup-form.md                         ← Peatixイベントページ設定例
├── peatix-vs-self-hosted.md              ← Peatix vs 自社ホスト比較・推奨
└── auto-emails/
    ├── registration-confirmation.md       ← 申込完了メール
    ├── reminder-1day-before.md            ← 前日リマインダーメール
    ├── reminder-1hour-before.md           ← 1時間前リマインダーメール
    └── post-webinar-followup.md          ← 終了後フォローアップメール
```

---

## 公開URL案

### MVP フェーズ（推奨）: Peatix

```
https://peatix.com/event/{イベントID}
```

`signup-form.md` の手順でPeatixにイベントを作成した際に発行されるURL。
このURLをDMテンプレートの `{{webinar_url}}` に設定する。

### 安定化後: 自社ホスト

```
https://tools.ynfactory.online/webinar/
または
https://ynfactory.online/webinar-ai-5select/
```

`landing-page.html` をVPS（ConoHa: tools.ynfactory.online）に配置し、
独自ドメインで公開する。配置先は工程7（VPSパイプライン改修）で決定する。

---

## 申込 → 開催 → フォローの全体フロー

```
【告知期間（開催2週間前〜）】
    │
    ├─ DM送付: dm_v1/v2/v3 に {{webinar_url}} を挿入して送付
    ├─ SNS投稿: X / Instagram / Threads で告知
    └─ HP掲載: メール署名にもURLを追加

    ↓

【申込受付】
    │
    ├─ [Peatix] 申込者が Peatix でチケット取得
    │      │
    │      └─ 自動: 申込完了メール送信
    │            （registration-confirmation.md）
    │
    └─ [自社ホスト（将来）] landing-page.html のフォーム送信
           │
           └─ Webhook → Gmail API で申込完了メール自動送信

    ↓

【開催準備（開催3日前〜）】
    │
    ├─ Zoom ミーティングURLを確定・申込者にメールで送付
    │    (registration-confirmation.md に記載済みでなければ)
    ├─ 持ち帰り資料（handout）を Google Drive にアップロード
    └─ アンケートフォーム（Google Forms）の準備

    ↓

【前日リマインダー（開催前日 15:00）】
    │
    └─ [Peatix] 「参加者へのメール配信」→ スケジュール送信
         （reminder-1day-before.md）

    ↓

【1時間前リマインダー（開催1時間前）】
    │
    └─ [Peatix] 「参加者へのメール配信」→ スケジュール送信
         （reminder-1hour-before.md）

    ↓

【ウェビナー開催（90分）】
    │
    ├─ Zoom でウェビナー実施
    ├─ 当日CTA: 無料個別相談（30分）の予約を案内
    │    → {{consult_booking_url}} （工程5 Calendly で設定）
    └─ 持ち帰り資料を当日配布（チャット欄でURL共有）

    ↓

【終了後フォローアップ（終了2〜3時間以内）】
    │
    └─ [手動] 全参加者にメール一括送付
         （post-webinar-followup.md）
         内容:
         ・持ち帰り資料ダウンロードURL（{{handout_url}}）
         ・アンケートURL
         ・無料個別相談予約CTA（{{consult_booking_url}}）

    ↓

【個別相談フォロー（ウェビナー後1〜2週間）】
    │
    ├─ 個別相談予約が入ったら翌営業日以内に確認メール
    ├─ 予約なしの参加者に1週間後にフォローメール（任意）
    └─ 参加者データをDMリストに追加（同意確認済みの場合）

    ↓

【次回ウェビナーへ】
    │
    └─ 参加者へ次回ウェビナーの案内を送付
         → 月1回のメルマガ的な継続接点に発展させる
```

---

## 差し込み変数一覧（全メール共通）

| 変数 | 内容 | 設定タイミング |
|---|---|---|
| `{{name}}` | 申込者の氏名 | 申込フォームから自動取得 |
| `{{company_name}}` | 会社名 | 申込フォームから自動取得 |
| `{{webinar_date}}` | 開催日時（例: 2026年6月17日（水）19:00〜20:30） | イベント作成時に確定 |
| `{{zoom_url}}` | ZoomミーティングURL | Zoomで作成後に設定 |
| `{{handout_url}}` | 持ち帰り資料のダウンロードURL | ウェビナー後に設定 |
| `{{consult_booking_url}}` | 無料個別相談予約URL | 工程5（Calendly）で設定 |

---

## 持ち帰り資料ファイルの場所

以下のファイルが既存の成果物として存在する（ウェビナー当日に使用）:

```
.company/outputs/sales-content/webinar-v1-jinzai-busoku/
├── handout-prompt-collection.pdf        ← AIプロンプト集
└── handout-roadmap-worksheet.pdf        ← AI活用ロードマップワークシート
```

Google Drive の「共有リンク」として発行し、`{{handout_url}}` に設定する。
（有効期限: ウェビナー終了後7日間を推奨）

---

## 開催スケジュール（推奨）

| 回 | 開催日 | 告知開始 | 申込締切 | 備考 |
|---|---|---|---|---|
| 第1回 | 2026年6月17日（水）19:00 | 2026年6月3日 | 2026年6月14日 | 定員10名目標 |
| 第2回 | 2026年7月15日（水）19:00 | 2026年7月1日 | 2026年7月12日 | 第1回の反省を反映 |
| 第3回以降 | 毎月第3水曜 | 2週間前 | 3日前 | 月1回定例化 |

> 最初は「10名集まれば合格」の目標設定。無理に30名を目指さない。
> 5名でも開催し、「やりきった実績」を積むことが重要。

---

## Peatix 運用チェックリスト

### イベント作成時
- [ ] `signup-form.md` の設定例を使ってイベントを作成
- [ ] 開催日時を設定（告知開始から2週間以上後）
- [ ] アンケート項目（業種・従業員数・都道府県・課題）を追加
- [ ] 申込完了メールの本文を `registration-confirmation.md` に差し替え
- [ ] イベントページを公開（SNS・DM用URLを控える）

### 開催3日前
- [ ] 前日リマインダーを `reminder-1day-before.md` でスケジュール送信設定（前日15:00）
- [ ] 1時間前リマインダーを `reminder-1hour-before.md` でスケジュール送信設定（開催1時間前）
- [ ] 参加者リストのCSVをダウンロードして確認

### 開催当日
- [ ] Zoom ミーティングを準備し、URLを確認
- [ ] 持ち帰り資料の Google Drive リンクを確認（有効期限設定）
- [ ] ウェビナー開催（Zoom）

### 開催後（終了2〜3時間以内）
- [ ] `post-webinar-followup.md` を使って全参加者にメール送付
- [ ] `{{handout_url}}` に実際のダウンロードURLを挿入
- [ ] `{{consult_booking_url}}` に Calendly URL を挿入（工程5完了後）
- [ ] Google Forms アンケートのURLを確認・挿入

---

## FAQ（運用者向け）

**Q: Peatix のアカウントをまだ持っていない場合は？**
A: https://peatix.com から無料でオーガニザー登録できます。本人確認は不要で即日公開可能。

**Q: Zoom の URL はいつ申込者に伝えるべきか？**
A: 申込完了メールに記載するか（事前確定の場合）、または「前日メールで送付」とアナウンスする。前者が参加者の安心感は高い。

**Q: 定員が埋まった場合はどうするか？**
A: Peatixの「キャンセル待ち」機能を有効にするか、次回開催案内へ誘導する。

**Q: 参加者ゼロでも開催するか？**
A: 1〜2名でも開催する。経験値が積まれ、次回改善につながる。録画し台本精度を上げることに集中する。

**Q: 個別相談の予約URLはいつ設定できるか？**
A: 工程5（Calendly設定）完了後。それまでは「info@ynfactory.online へメールで連絡」と案内する。

---

## 関連ファイル・リンク

| ファイル・リソース | 場所 |
|---|---|
| ウェビナー台本（完成版） | `.company/outputs/sales-content/webinar-v1-jinzai-busoku/` |
| 個別Zoom提案資料 | `.company/outputs/sales-content/individual-zoom-30min/` |
| オファー資料（L1/L2/L3） | `.company/outputs/sales-content/offer-materials/` |
| Peatix管理画面 | https://peatix.com/organizer |
| Zoom管理画面 | https://zoom.us/meeting |
| Google Drive（資料格納） | （オーナーのGoogleドライブ） |
