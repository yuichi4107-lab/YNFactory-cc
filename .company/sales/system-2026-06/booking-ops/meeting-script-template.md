# 商談進行ガイド — 当日チェックリスト

- **担当**: オーナー（商談本体）
- **所要時間**: 30分
- **台本本体**: `.company/outputs/sales-content/individual-zoom-30min/script.md`（工程10成果物・完成済み）
- **本ファイルの用途**: 予約直後〜当日の進行チェックリスト。台本の補完と運用のガイド。

> **重要**: 詳細なトーク内容・セリフ・ノートはすべて `script.md` に記載済み。本ファイルは「それを運用に組み込む」ための進行チェックです。商談当日は `script.md` を読んで臨んでください。

---

## 予約直後（当日まで）にやること

- [ ] 予約確認メールを受信した（Calendly自動送信）
- [ ] ブリーフを生成した（`pre-meeting-brief-template.md` を参照）
- [ ] ブリーフを `.company/sales/clients/brief-{{日付}}-{{会社名}}.md` に保存した
- [ ] 商談日時をカレンダーに登録した（Zoom URLを含める）

---

## 商談前日〜当日朝にやること

- [ ] ブリーフ（`brief-{{日付}}-{{会社名}}.md`）を再読した
- [ ] `script.md` の時間配分（0〜5分/5〜15分/15〜25分/25〜30分）を頭に入れた
- [ ] `hearing-questions.md`（ヒアリング質問10項目）を確認した
- [ ] `closing-flow.md`（クロージングSTEP1〜3）を確認した
- [ ] `slides.pptx` を開き、ページ構成を確認した
- [ ] Zoom URLに問題がないことをテスト接続で確認した
- [ ] マイク・カメラの動作確認をした
- [ ] 背景・照明を整えた（清潔感のある背景、顔への適切な光）

---

## 商談当日 — 5分前にやること

- [ ] Zoomを起動し、ホストとして入室した
- [ ] 画面共有の準備をした（`slides.pptx` を開いた状態）
- [ ] ブリーフ・ヒアリングシートを手元（または別画面）に用意した
- [ ] メモツールを開いた（ヒアリング内容を書き留める）

---

## 商談 30分の進行（時間配分）

| 時間 | パート | 参照ファイル | 担当 |
|---|---|---|---|
| 0〜5分 | 自己紹介・今日の流れ共有 | `script.md` §0〜5分パート | オーナー |
| 5〜15分 | ヒアリング（課題・現状を引き出す） | `hearing-questions.md` + `script.md` §5〜15分パート | オーナー |
| 15〜25分 | プラン提示（L1/L2/L3から1つ推奨） | `script.md` §15〜25分パート + `slides.pptx` | オーナー |
| 25〜30分 | クロージング（次ステップ3択を提示） | `closing-flow.md` + `script.md` §25〜30分パート | オーナー |

### 各パートのポイント（script.md からの抜粋）

**0〜5分 自己紹介パート**
- 「キャリアコンサルタント×AI」の3本柱を早めに出す（`script.md` §自己紹介3本柱）
- 「今日すぐ決めなくていい」と冒頭で伝え、相手の警戒心を解く

**5〜15分 ヒアリングパート**
- こちらが話しすぎない。相手が話し終わるまで待つ
- Q4（採用・育成の課題）はキャリコン視点の核心。丁寧に深掘りする
- ブリーフの「想定課題」が当たっているか確認しながら聞く

**15〜25分 プラン提示パート**
- ブリーフの「推奨プラン仮説」を起点に、ヒアリング内容で補正する
- L1/L2/L3を全部すすめず「御社には〇〇が合っていると思います」と1択に絞る
- 補助金の可能性がある場合（特にL3）は「活用できる可能性があります」と一言添える

**25〜30分 クロージングパート**（`closing-flow.md` STEP1〜3 に従う）
- STEP1: 「いちばん響いた部分はどこでしたか？」で共感を確認
- STEP2: 推奨プランを1つに絞って再提示（根拠付き）
- STEP3: 次ステップ3択（A:即決 / B:1週間後フォローZoom / C:見送り）を提示

---

## 商談後にやること（当日中）

- [ ] メモをまとめた（課題・関心ポイント・推奨プラン・次ステップの選択）
- [ ] クライアントファイルを作成または更新した（`.company/sales/clients/{{会社名}}.md`）
- [ ] 次ステップの選択に応じて以下を実行した：
  - **A（即決）**: `onboarding-checklist.md` に進む。契約書を送付する
  - **B（1週間後フォロー）**: フォローZoomの日程をCalendlyで設定。`follow-up-email-templates.md` パターンBを送信
  - **C（見送り）**: `follow-up-email-templates.md` パターンCを送信
- [ ] 提案書PPTXのドラフト生成が必要な場合（特にBの場合）: `proposal-auto-draft.md` に進む

---

## クライアントファイル記録テンプレート

商談完了後、以下の形式で `.company/sales/clients/{{会社名}}.md` を作成または更新する。

```markdown
---
company: "{{会社名}}"
contact: "{{担当者名}}"
status: "prospect" # prospect → active → inactive
last_meeting: "{{商談日}}"
recommended_plan: "L?"
next_action: "フォロー送信 / フォローZoom / 契約書送付 / なし"
next_action_date: "{{YYYY-MM-DD}}"
---

# {{会社名}} / {{担当者名}}様

## 商談記録: {{商談日}}

### ヒアリング内容
- 業種・規模: 
- 現在のAI活用状況: 
- 主な課題感: 
- 予算感: 

### 響いたポイント
（クロージングSTEP1の回答を記録）

### 推奨プランと根拠
- 推奨: L?
- 根拠: 

### 次ステップ
- 選択: A（即決）/ B（検討中）/ C（見送り）
- 次アクション日: {{YYYY-MM-DD}}
- 内容: 

## 通信履歴
- {{YYYY-MM-DD}}: 商談実施
```

---

## 既存成果物へのリンク一覧

| ファイル名 | パス |
|---|---|
| 30分商談台本（本体） | `.company/outputs/sales-content/individual-zoom-30min/script.md` |
| ヒアリング質問リスト | `.company/outputs/sales-content/individual-zoom-30min/hearing-questions.md` |
| クロージングフロー | `.company/outputs/sales-content/individual-zoom-30min/closing-flow.md` |
| 商談用スライド | `.company/outputs/sales-content/individual-zoom-30min/slides.pptx` |
| L1オファー説明書 | `.company/outputs/sales-content/offer-materials/plans/L1-light-advisor.md` |
| L2オファー説明書 | `.company/outputs/sales-content/offer-materials/plans/L2-standard-advisor.md` |
| L3オファー説明書 | `.company/outputs/sales-content/offer-materials/plans/L3-3month-implementation.md` |

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程3の成果物。*
*最終更新: 2026-06-09*
