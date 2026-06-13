# 日次オペレーション チェックリスト

- **作成日**: 2026-06-09
- **対象工程**: 工程4（運用リズムの仕組み化）
- **目的**: 毎朝5〜10分の確認で「送らない日を作らない」を実現する

---

## 毎朝の実行手順（平日 07:30〜）

### ステップ1: sales-briefing スキルを起動する

```
/sales-briefing
```

以下の順でスキルが自動実行される:

1. VPSから approval_queue を取得
2. pending DMをオーナーに提示（業種・件数サマリー）
3. 承認/却下/修正を選択
4. 承認アクションをVPSに通知
5. 送信トリガーを実行
6. Telegramで結果通知
7. DASHBOARD_SALES.md §1 を更新

### ステップ2: 返信確認（2分）

Gmailの `info@yn-factory.com` 受信トレイを確認する。

- [ ] 新着返信があれば `DASHBOARD_SALES.md §6「返信対応待ち」` に追加
- [ ] 返信があった場合は **24時間以内に返信**（返信テンプレート: `.company/sales/system-2026-06/booking-ops/follow-up-email-templates.md`）
- [ ] Calendly予約通知があれば `.company/sales/system-2026-06/booking-ops/pre-meeting-brief-template.md` を起動してブリーフ生成

### ステップ3: Peatix確認（月曜・金曜のみ、1分）

Peatix管理画面で新着申込を確認する。

- [ ] 新着申込があれば `DASHBOARD_SALES.md §1「ウェビナー申込数」` を更新
- [ ] 申込者数が目標（5名）の50%未満（3名未満）なら次回の週次レビューで対策を検討

### ステップ4: 月曜のみ — 週次レビュー起動確認

sales-briefing のステップ7完了後に表示される月曜プロンプトに従って判断:

```
今日は月曜日です。週次営業レビューを実施しますか？
[Y] はい → /weekly-sales-review を起動
[N] いいえ → このまま終了
```

- **推奨**: 月曜は必ず「Y」を選択する（所要時間: 5〜10分）

---

## 停滞防止の強制ルール

### 今週の必達アクション（消えない forcing function）

**毎朝の sales-briefing 起動前に以下を確認すること:**

`DASHBOARD_SALES.md §6（アクション待ち一覧）` の「その他」欄に登録された
**今週の必達アクション**が完了しているか確認する。

```
未完了の場合: 今日の承認・送信の前に、まず必達アクションを完了させる（または完了できないブロッカーを確認する）
完了した場合: その他欄から削除して新しい必達アクションを週次レビューで設定する
```

**これは「やるまで消えない」仕組みです。**
毎週月曜の `/weekly-sales-review` で新しい必達アクション（1〜3個）を設定し、
達成するまで毎朝このチェックリストの冒頭に表示し続けます。

---

## 停滞アラート（自動発火条件）

以下の状態が続いたら `DASHBOARD_SALES.md §5（KPI警告ライン）` に警告が記録される。
daily-ops-checklist の実行時に §5 を確認し、警告があれば当日中に対処する。

| 条件 | 警告ライン | 対処の入口 |
|---|---|---|
| DM送信が3日連続ゼロ | 警告A: 本番送信ゼロ | `LAUNCH_CHECKLIST.md §工程8b` |
| Gmailに未読返信が2日以上放置 | 警告D: 商談数ゼロ | 今すぐ返信 / Calendly案内 |
| Calendly予約後ブリーフ生成が未着手 | （手動確認） | `booking-ops/pre-meeting-brief-template.md` |

---

## 緊急時（送信できない日）の対応

やむを得ず送信できない日は以下を実行する:

1. `DASHBOARD_SALES.md §4（週次サマリー）` の今週欄に送信ゼロと記録
2. 翌日の送信数を +5通ペースアップする（週合計5〜20通を維持）
3. 週に2日以上送信ゼロが続いた場合は、週次レビューで必達アクションを見直す

---

## 参照リスト

| 参照先 | 用途 |
|---|---|
| `.company/DASHBOARD_SALES.md` | 数値の読み書き先（毎朝更新） |
| `.company/sales/LAUNCH_CHECKLIST.md` | 本番送信できない場合の解決手順 |
| `.company/sales/system-2026-06/booking-ops/pre-meeting-brief-template.md` | Calendly予約受信後のブリーフ生成 |
| `.company/sales/system-2026-06/booking-ops/follow-up-email-templates.md` | 返信・フォローメールのテンプレート |
| `.claude/skills/sales-briefing/SKILL.md` | daily briefing スキル本体 |
| `.claude/skills/weekly-sales-review/SKILL.md` | 週次レビュースキル本体 |

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程4の成果物。*
*最終更新: 2026-06-09*
