# 商談導線 全体フロー — booking-ops

- **作成日**: 2026-06-09
- **対象工程**: 工程3（商談集中の運用導線設計）
- **目的**: オーナーの手動工数を「商談そのもの」だけに絞り、前後をすべて自動/テンプレで処理する

---

## 全体フロー図

```
【Calendly予約完了】
        ↓ （自動: Calendly確認メール送信）
[1. 事前リサーチ] ← pre-meeting-brief-template.md
        Claude支援: 10分以内にブリーフ生成
        ↓
[2. 当日商談 30分] ← meeting-script-template.md
        オーナー: 商談に集中（台本・ヒアリングシートを手元に）
        ↓
[3. 提案書ドラフト生成] ← proposal-auto-draft.md
        Claude支援: 商談後24h以内にPPTXドラフト生成
        ↓
[4. フォローメール送信] ← follow-up-email-templates.md
        オーナー: パターンを選んで送信（コピペ30秒）
        ↓ （成約の場合）
[5. 契約・オンボーディング] ← onboarding-checklist.md
        Claude支援 + オーナー: 契約書送付〜キックオフ設定
        ↓
[6. 経理連携] ← finance-integration.md
        Claude支援: 請求書生成→ .company/finance/invoices/ 保存
```

---

## 各フェーズの担当と工数

| フェーズ | 実施タイミング | 担当 | 目安工数 |
|---|---|---|---|
| 事前リサーチブリーフ生成 | 予約後30分以内 | Claude支援（オーナーが起動） | 10分以内 |
| 商談当日の進行 | 商談当日 | **オーナー（メイン）** | 30分 |
| 提案書PPTXドラフト | 商談後24h以内 | Claude支援（オーナーが起動） | 15分 |
| フォローメール送信 | 商談後24h以内 | オーナー（コピペ送信） | 5分 |
| 契約書送付 | 成約確認後即日 | オーナー（テンプレ流用） | 10分 |
| オンボードキックオフ設定 | 契約締結後3日以内 | オーナー（チェックリスト従う） | 20分 |
| 請求書生成・保存 | 契約締結後即日 | Claude支援（オーナーが起動） | 5分 |

**商談本体以外の合計オーナー工数目安: 約50分/案件**

---

## 参照する既存資産（流用・参照元）

| 資産 | パス | 用途 |
|---|---|---|
| 30分商談台本（完成） | `03_成果物/outputs/sales-content/individual-zoom-30min/script.md` | 商談当日の進行（工程10成果物） |
| ヒアリング質問リスト | `03_成果物/outputs/sales-content/individual-zoom-30min/hearing-questions.md` | 商談前ブリーフ・当日用 |
| クロージングフロー | `03_成果物/outputs/sales-content/individual-zoom-30min/closing-flow.md` | 商談クロージング |
| 商談用スライド | `03_成果物/outputs/sales-content/individual-zoom-30min/slides.pptx` | 商談当日提示（提案書ベース） |
| L1オファー説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L1-light-advisor.md` | 提案書生成の入力 |
| L2オファー説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L2-standard-advisor.md` | 提案書生成の入力 |
| L3オファー説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L3-3month-implementation.md` | 提案書生成の入力 |
| オファー比較表 | `03_成果物/outputs/sales-content/offer-materials/plans/comparison-table.md` | 提案書に差し込む |
| 契約書テンプレ（L1/L2） | `03_成果物/outputs/sales-content/offer-materials/contracts/contract-L1-L2-monthly.md` | 成約後の契約書送付 |
| 契約書テンプレ（L3） | `03_成果物/outputs/sales-content/offer-materials/contracts/contract-L3-project.md` | 成約後の契約書送付 |
| Calendlyセットアップ | `03_成果物/outputs/sales-content/calendly-setup/` | 予約フロー前提 |

---

## 各ファイルの役割

| ファイル | 役割 |
|---|---|
| `pre-meeting-brief-template.md` | 予約受信後→10分で読めるブリーフ生成（Claudeプロンプト込み） |
| `meeting-script-template.md` | 商談当日の進行チェックリスト（既存台本へのリンク込み） |
| `proposal-auto-draft.md` | 商談後のPPTXドラフト自動生成手順 |
| `follow-up-email-templates.md` | A/B/Cの3パターンフォローメール（コピペ即送信） |
| `onboarding-checklist.md` | 契約後のオンボーディング完全チェックリスト |
| `finance-integration.md` | 経理連携手順（請求書→invoices/保存〜MRR反映まで） |

**どのファイルから始めるか**: Calendly予約通知が届いたら `pre-meeting-brief-template.md` を開く。成約後は `onboarding-checklist.md` → `finance-integration.md` の順に進む。

**ノーショー（無断キャンセル）時の対処**: 予約時刻から15分待っても入室がない場合、「お時間になりましたがご入室が確認できておりません。再調整はこちらから: [CalendlyのURL]」と短いメールを1通送り、クライアントファイルを `status: prospect` のまま保持する。翌週に再アプローチを検討する。

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程3の成果物。*
*最終更新: 2026-06-09*
