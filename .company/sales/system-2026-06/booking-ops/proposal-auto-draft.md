# 提案書 自動ドラフト生成フロー

- **担当**: Claude支援（オーナーが起動）
- **目標時間**: 商談後24時間以内にドラフト完成
- **ベース**: 既存PPTX（`03_成果物/outputs/sales-content/individual-zoom-30min/slides.pptx`）を流用
- **スキル活用**: `anthropic-skills:pptx` スキルで生成・差し替え

---

## 概要

商談後のPPTXドラフトは「既存スライドを個社カスタマイズ」する方式で作成する。

- **ゼロから作らない**: `slides.pptx`（工程10成果物）がベーステンプレートとして機能する
- **差し替えのみ**: 企業名・課題・推奨プランなど「個社固有の情報」だけを差し替える
- **15分以内に完成**: Claudeが差し替え内容を生成し、オーナーはPPTXに貼り付けるだけ

---

## STEP 1: 商談メモから入力変数を整理（3分）

商談後のクライアントファイル（`.company/sales/clients/{{会社名}}.md`）を確認し、以下の変数を埋める。

```
【提案書生成 入力変数】

会社名: {{company_name}}
担当者名: {{contact_name}}
業種: {{industry}}
従業員規模: {{employees}}
主な課題（ヒアリングより）: {{main_challenge}}
関心ポイント（クロージングSTEP1の回答）: {{interest_point}}
推奨プラン: {{recommended_plan}}  # L1 / L2 / L3
推奨理由（1〜2文）: {{reason}}
補助金の提案: {{subsidy}}  # あり / なし
提案日: {{proposal_date}}
```

---

## STEP 2: Claudeでスライド差し替え内容を生成（5分）

以下のプロンプトをClaudeに実行させる。

```
## 提案書スライド差し替え内容 生成プロンプト

以下の変数を使い、個社向け提案書のスライド差し替え内容を生成してください。

### 入力変数
- 会社名: {{company_name}}
- 担当者名: {{contact_name}}
- 業種: {{industry}}
- 主な課題: {{main_challenge}}
- 関心ポイント: {{interest_point}}
- 推奨プラン: {{recommended_plan}}
- 推奨理由: {{reason}}
- 補助金の提案: {{subsidy}}
- 提案日: {{proposal_date}}

### 生成する内容（スライド差し替え箇所）

#### 表紙スライド（差し替え）
タイトル: 「{{company_name}} 様 AI活用顧問サービス ご提案」
サブタイトル: 「{{proposal_date}} / YN Factory 中田雄一」

#### 御社の課題認識スライド（差し替え）
課題タイトル: （{{main_challenge}}を1行のキャッチで）
課題本文: （{{main_challenge}}を経営者目線で2〜3行に言語化。押しつけにならず「〜ではないでしょうか」という問いかけ形式）

#### 解決策・推奨プランスライド（差し替え）
推奨プランの見出し: 「{{recommended_plan}}: {{プラン名}}」
プランの一言説明: （{{reason}}を踏まえた、{{company_name}}様向けの一言）
推奨の根拠: （{{interest_point}}を踏まえた2〜3行）

#### 次ステップスライド（差し替え）
（以下の3択から、商談で選ばれた選択肢に応じて最適なテキストを生成）
- B（検討中）の場合: 「1週間以内にご返答をお待ちしています。ご不明点はinfo@yn-factory.comへ」
- A（即決）の場合: 「本日ご確認いただいた内容で契約書をご送付します」

#### 補助金スライド（{{subsidy}}=ありの場合のみ生成）
補助金活用の見出しと本文（「活用できる可能性があります」という表現を使い、保証しない旨を含める）

---

出力形式: 各スライドの差し替えテキストをMarkdownで出力。PPTXの該当スライドに貼り付けられる形式で。
```

---

## STEP 3: PPTXに差し替えて保存（5分）

### 方法A: pptxスキルを使う（推奨）

Claude Code 上で以下のコマンドを実行する。

```
/pptx
```

スキル起動後、以下のテキストをそのままClaude Codeのチャットに貼り付けて送信する（`{{}}` 内は実際の値に置き換える）。

```
03_成果物/outputs/sales-content/individual-zoom-30min/slides.pptx を読み込んでください。
次に、以下の差し替え内容を対応するスライドに適用してください。

【表紙】タイトルを「{{company_name}} 様 AI活用顧問サービス ご提案」に、サブタイトルを「{{proposal_date}} / YN Factory 中田雄一」に変更する。
【課題認識スライド】課題テキストを「{{STEP2で生成した課題認識スライドのテキスト}}」に差し替える。
【推奨プランスライド】見出しを「{{recommended_plan}}: {{プラン名}}」、本文を「{{STEP2で生成した推奨プランのテキスト}}」に差し替える。
【次ステップスライド】本文を「{{STEP2で生成した次ステップのテキスト}}」に差し替える。
（L3の場合）【補助金スライド】本文を「{{STEP2で生成した補助金テキスト}}」に差し替える。

完成したファイルを .company/sales/proposals/{{YYYY-MM-DD}}-proposal-{{company_name}}.pptx として保存してください。
```

### 方法B: 手動差し替え（pptxスキルが使えない場合）

1. `slides.pptx` を開く
2. STEP 2 で生成したテキストを該当スライドに貼り付ける（差し替え箇所は5〜6スライド）
3. `.company/sales/proposals/{{YYYY-MM-DD}}-proposal-{{company_name}}.pptx` として保存する

**差し替えスライドの目安（slides.pptx の構成に従う）:**
- 表紙: 会社名・日付
- 課題認識スライド: 個社の課題テキスト
- 推奨プランスライド: プラン名・推奨理由
- 次ステップスライド: 選択した行動
- 補助金スライド（L3の場合）: あれば差し替え

---

## STEP 4: 提案書送付（オーナーが実行 / 5分）

1. 生成した PPTX を PDF に書き出す（PowerPoint → ファイル → エクスポート → PDF）
2. フォローメール（`follow-up-email-templates.md` パターンB）に添付して送信する

---

## 保存パスルール

```
.company/sales/proposals/{{YYYY-MM-DD}}-proposal-{{company_name}}.pptx
.company/sales/proposals/{{YYYY-MM-DD}}-proposal-{{company_name}}.pdf
```

例:
```
.company/sales/proposals/2026-07-11-proposal-yamamoto-tax.pptx
.company/sales/proposals/2026-07-11-proposal-yamamoto-tax.pdf
```

---

## 参照する既存資産

| 資産 | パス | 用途 |
|---|---|---|
| 商談用スライド（ベース） | `03_成果物/outputs/sales-content/individual-zoom-30min/slides.pptx` | 差し替えのベーステンプレート |
| L1説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L1-light-advisor.md` | L1提案時のプラン詳細テキスト |
| L2説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L2-standard-advisor.md` | L2提案時のプラン詳細テキスト |
| L3説明書 | `03_成果物/outputs/sales-content/offer-materials/plans/L3-3month-implementation.md` | L3提案時のプラン詳細テキスト |
| オファー比較表 | `03_成果物/outputs/sales-content/offer-materials/plans/comparison-table.md` | 比較表スライドの差し替えテキスト |
| 補助金資料 | `03_成果物/outputs/sales-content/offer-materials/subsidy/subsidy-guide.md` | 補助金スライドの参照 |

---

## 個社カスタマイズの最小工数まとめ

差し替えが必要な箇所は以下の5〜6点のみ。それ以外はベーステンプレートのまま使用する。

| スライド | 差し替え内容 | 工数 |
|---|---|---|
| 表紙 | 会社名・日付 | 30秒 |
| 課題認識 | 個社の課題テキスト（Claudeが生成） | 貼り付け30秒 |
| 推奨プラン | プラン名・推奨理由（Claudeが生成） | 貼り付け30秒 |
| 次ステップ | 選択肢に応じたテキスト（Claudeが生成） | 貼り付け30秒 |
| 補助金（L3のみ） | 補助金テキスト（Claudeが生成） | 貼り付け30秒 |

**合計手動工数: 約5分（STEP 3 の手動差し替え時）**

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程3の成果物。*
*最終更新: 2026-06-09*
