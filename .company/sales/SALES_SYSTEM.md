# 営業オペレーティングシステム — 全体マップ（入口）

- **作成日**: 2026-06-09
- **目的**: 高単価AIコンサル（AI活用アドバイザー）の営業を、オーナーの週5時間を「商談だけ」に集中させて回す仕組み
- **このファイルの役割**: 営業システム全体の入口。次回セッション・別PCからはまずここを読む
- **方針の核**: 5月に作った戦略・システムを **作り直さず「動かす」**。停滞を二度と起こさない強制力を組み込む

> ⚠️ **最重要の事実**: 営業システム自体は2026-05に91〜97点で完成済みだったが、**本番送信GO・ウェビナー設置などの手動ローンチ手順が未実行のまま約5週間休眠**していた。本システムの本質は「新機能」ではなく「**確実にローンチし、毎週前進させる運用**」である。

---

## 🚀 START HERE — 最初にやること（約1時間で本番起動）

停滞の唯一の解は「オーナーがローンチ手順を実行すること」。下記1ファイルだけ見れば画面操作レベルで完了する。

➡️ **[LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md)** を開き、「最初の1時間でやること」から順に実行

その中の最優先3つ:
1. **From問題は案Cで即割り切る**（gmail.com送信のまま・Reply-To/署名はinfo@）→ 送信を止めない
2. **本番送信GO**（自分宛テスト1通→確認→DAILY_LIMIT 1→5→30→…段階引き上げ）
3. **Peatixウェビナー公開**（KGI: 2026-07-15までに第1回開催）

> **人脈ゼロからの早期リード獲得はこれ** ➡️ **[EARLY_LEADS_PLAYBOOK.md](EARLY_LEADS_PLAYBOOK.md)**
> 士業パートナー勧誘（最優先・今週着手）／バリューファーストDM改訂／有料広告テスト／リードマグネット制作／意図プラットフォーム登録 の5打ち手と7週間週次ロードマップ

---

## 🧭 5つの構成要素

| # | 要素 | ファイル | 役割 | 品質 |
|---|---|---|---|---|
| 1 | **営業戦略書** | [STRATEGY.md](STRATEGY.md) | ポジショニング・ICP・L1/L2/L3・ファネル・KGI/KPI・ユニットエコノミクスの**単一ソースオブトゥルース** | 87→polish |
| 2 | **起動チェックリスト** | [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) | 休眠システムを本番起動する画面操作レベル手順（From問題/ウェビナー/Calendly/本番送信） | 90 |
| 3 | **商談導線** | [system-2026-06/booking-ops/](system-2026-06/booking-ops/README.md) | 予約→事前リサーチ→提案書→フォロー→オンボード→経理を**商談以外ほぼ自動化**（7ファイル） | 88 |
| 4 | **運用リズム** | `/weekly-sales-review` スキル ＋ [daily-ops-checklist.md](daily-ops-checklist.md) ／ [weekly-review-checklist.md](weekly-review-checklist.md) | 毎朝の承認＋毎週のレビュー。**停滞防止の強制力4つ**を内蔵 | 91 |
| 5 | **KPIダッシュボード** | [../DASHBOARD_SALES.md](../DASHBOARD_SALES.md) | DM送信→返信→商談→提案→成約のファネルを転換率込みで可視化。KGI進捗バー | 88 |
| 6 | **早期リード源プレイブック** | [EARLY_LEADS_PLAYBOOK.md](EARLY_LEADS_PLAYBOOK.md) | 人脈ゼロからの早期リード獲得。士業パートナー化・広告・LM・意図プラットフォーム 5打ち手と7週間週次ロードマップ（オーナー承認 2026-06-09） | — |

補足:
- 要件定義書: [`.company/requirements/sales-system-2026-06/REQUIREMENTS.md`](../requirements/sales-system-2026-06/REQUIREMENTS.md)
- 既存の集客自動化（軸C DM生成）: `sales-ops/`（ローカル）＋ VPS `/opt/sales-ops/`（参照元・リポジトリ外）
- 既存の商談コンテンツ（流用元）: `.company/outputs/sales-content/`（30分台本・PPTX・オファーL1-L3・契約書）

---

## 🔁 日々の回し方（オーナーの動き）

```
【毎朝07:30】 /sales-briefing
   軸Cのpending DMを承認 → VPS送信 → DASHBOARD更新 → Telegram報告
   （月曜のみ）→ /weekly-sales-review を起動

【毎週月曜】 /weekly-sales-review
   先週KPI集計 → 目標/警告ラインと比較 → 未達への具体策を提案
   → 今週の必達アクション1〜3個を確定（完了するまで毎朝再掲）
   → .company/reviews/YYYY-WXX-sales.md に記録

【予約が入ったら】 booking-ops/ の導線に乗る
   事前リサーチブリーフ(自動) → 商談(オーナー・ここだけ集中) → 提案書(自動ドラフト)
   → フォローメール(テンプレ) → 成約ならオンボード → 経理連携(請求書)
```

**オーナーが手で頭を使うのは「商談そのもの」だけ。前後はすべてテンプレ／自動。**

---

## 🎯 KGI（確定 / オーナー承認 2026-06-09）

| 指標 | 目標 | 期限 |
|---|---|---|
| 有料個別商談（Zoom）実施数 | **3〜5件（実施）** | 2026-07-31 |
| 士業パートナー接触・共催打診 | **1〜2件** | 2026-07-31 |
| 有料広告・リードマグネット稼働 | **稼働開始** | 2026-07-31 |
| ウェビナー開催 | **1回以上** | 2026-07-15 |
| 本番DM送信累計 | **100件以上** | 2026-07-31 |
| 初契約獲得（L1以上・MRR 4万円以上） | **1件** | **2026-09-30** |
| MRR 20万円達成 | **MRR 20万円** | **2026-12-31** |

- 進捗はすべて [DASHBOARD_SALES.md](../DASHBOARD_SALES.md) で追跡
- 早期リード獲得の実行計画 → [EARLY_LEADS_PLAYBOOK.md](EARLY_LEADS_PLAYBOOK.md)

---

## ⚠️ 既知の制約（品質チェックで判明した実システムの欠陥）

正直に記載。本番起動前に認識しておくこと。

1. **`conversations` テーブルへの送信記録は現状コード未実装**（`gmail_sender.py` がINSERTしない）。LAUNCH.md完了条件4は現状達成不可。送信記録は `approval_queue.status='sent'` とGmail送信済みフォルダで代替確認。将来 `gmail_sender.py` に実装余地あり。
2. **ウェビナー/予約URLは `.env` に書いても反映されない**（`config.py` が未読込）。`sales-ops/src/tracks/c_outbound/personalizer.py` の `PROMPT_TEMPLATE` に直書きする（手順はLAUNCH_CHECKLISTに記載）。
3. **From表示は当面 gmail.com のまま**（案C）。プロ化したい場合は案A（Workspace SMTP/アプリパスワード）→案B（OAuth）をLAUNCH_CHECKLISTの手順で。

---

## 📌 次回セッション/別PCでの再開手順

1. このファイル（SALES_SYSTEM.md）を読む
2. [DASHBOARD_SALES.md](../DASHBOARD_SALES.md) で現在地（送信数・返信・商談・成約・KGI残日数）を確認
3. ローンチ未完なら [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) を継続
4. 稼働中なら `/sales-briefing`（朝）・`/weekly-sales-review`（月曜）を回す
