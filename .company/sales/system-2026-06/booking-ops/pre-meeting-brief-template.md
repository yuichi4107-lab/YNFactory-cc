# 事前リサーチブリーフ — 生成テンプレートと手順

- **担当**: Claude支援（オーナーが起動）
- **目標時間**: Calendly予約通知受信から10分以内に完了
- **成果物**: 商談前日までに読める1枚ブリーフ（A4相当）

---

## 手順：予約通知を受けたら

### STEP 1: Calendlyからの予約情報を収集（2分）

Calendlyからの予約確認メールを開き、以下を確認する。

- [ ] 相手の**氏名**（フルネーム）
- [ ] 相手の**メールアドレス**（ドメインから会社名を確認）
- [ ] **会社名**（Calendlyの事前質問で取得済みの場合はそれを使う）
- [ ] **役職**（Calendlyの事前質問で取得済みの場合）
- [ ] **商談日時**
- [ ] **Calendlyの事前質問への回答**（設定済みの場合）

> Calendlyの事前質問設定については `.company/outputs/sales-content/calendly-setup/pre-meeting-questions.md` を参照。
> 設定済みの場合、「現在の課題」「従業員規模」「AI活用状況」がすでに取得できている。

---

### STEP 2: Claudeでブリーフを生成（5分）

以下のプロンプトをClaude（claude.ai または Claude Code）に貼り付けて実行する。

```
## 商談前リサーチブリーフ生成プロンプト

以下の情報から、商談前リサーチブリーフを生成してください。

### 入力情報

- 会社名: {{company_name}}
- 担当者名: {{contact_name}}
- 役職: {{contact_title}}
- 業種（わかる場合）: {{industry}}
- 従業員規模（わかる場合）: {{employees}}
- Calendly事前回答（あれば貼り付け）:
  {{calendly_answers}}

### 生成するブリーフの構成

以下の6セクションを含むブリーフを出力してください。

#### 1. 企業概要（3行以内）
- 推定業種・主要事業
- 従業員規模の目安
- 地域・ビジネス特性

#### 2. 想定課題（課題仮説3つ）
以下のICPを参考に、業種・規模から考えられる課題を推定してください。
- 採用難・人手不足
- AI/DX推進の停滞
- 社員がAIを使えない/使ってくれない
- 特定業務の属人化・効率化ニーズ
※Calendly事前回答がある場合は、それを最優先で反映する

#### 3. 推奨プラン仮説
- 推奨: L? （根拠を1文で）
- 代替: L? （根拠を1文で）

#### 4. アイスブレイク候補（2案）
業種・地域・会社規模から考えられる自然な話題（押しつけにならないもの）

#### 5. 想定反論と対応メモ
- 反論1: 「（予算・タイミング等）」→ 対応例: ...
- 反論2: 「（競合・必要性等）」→ 対応例: ...

#### 6. 当日の注意点（1〜2行）
業種特有の配慮事項や、特に丁寧に聞くべきポイント

---

出力形式: Markdown。全体でA4 1枚相当（500〜800字程度）に収めてください。
```

---

### STEP 3: ブリーフを保存（1分）

生成されたブリーフを以下のパスに保存する。

```
.company/sales/clients/brief-{{YYYY-MM-DD}}-{{company_name}}.md
```

例: `.company/sales/clients/brief-2026-07-10-yamamoto-tax.md`

---

### STEP 4: 商談前日の確認（2分）

商談前日（または当日朝）に以下を確認する。

- [ ] ブリーフを再読した
- [ ] 既存台本（`script.md`）の時間配分を頭に入れた
- [ ] ヒアリング質問リスト（`hearing-questions.md`）を印刷または手元に用意した
- [ ] クロージングフロー（`closing-flow.md`）を確認した
- [ ] 商談用スライド（`slides.pptx`）を開いて動作確認した
- [ ] Zoom URLを確認した（Calendlyが自動発行している）

---

## ブリーフ出力テンプレート（保存形式）

生成後、以下のヘッダーを付けてファイルに保存する。

```markdown
---
date: "{{商談日時}}"
company: "{{会社名}}"
contact: "{{担当者名}}"
plan_hypothesis: "L?"
status: brief-ready
---

# 商談前ブリーフ: {{会社名}} / {{担当者名}}様

## 1. 企業概要
（生成内容を貼り付け）

## 2. 想定課題（課題仮説）
（生成内容を貼り付け）

## 3. 推奨プラン仮説
（生成内容を貼り付け）

## 4. アイスブレイク候補
（生成内容を貼り付け）

## 5. 想定反論と対応メモ
（生成内容を貼り付け）

## 6. 当日の注意点
（生成内容を貼り付け）

---
*生成日: {{YYYY-MM-DD}}*
*参照元: .company/sales/system-2026-06/booking-ops/pre-meeting-brief-template.md*
```

---

## gBizINFO補足リサーチ（時間があれば追加）

VPSのDBに相手企業のデータが存在する場合は追加情報として活用できる。

```
# DBで企業情報を確認するSQL（VPS上で実行）
# ※VPSへのSSHアクセスが必要

SELECT company_name, contact_email, location, industry, size_employees, website_url, segment,
       hp_summary, personalization_hints
FROM companies
WHERE company_name LIKE '%{{会社名キーワード}}%'
   OR contact_email LIKE '%{{ドメイン}}%';
```

> companies テーブルの実列名（`sales-ops/src/core/db.py` で確認済み）:
> `id / source / segment / company_name / website_url / contact_email / industry / size_employees / location / hp_summary / personalization_hints / status / created_at`
> `location` 列は存在する。`hp_summary`（HP要約）と `personalization_hints`（パーソナライズヒント）もブリーフ生成に活用できる。
> 設計詳細は `.company/engineering/docs/sales-ops-design.md` を参照。

企業のWebサイト（`website_url`）がある場合はブラウザで開き、「事業内容」「採用ページ」「代表メッセージ」を確認するとブリーフの精度が上がる。

---

## 既存台本へのリンク（商談当日に参照するファイル）

| ファイル | パス | 用途 |
|---|---|---|
| 30分商談台本 | `.company/outputs/sales-content/individual-zoom-30min/script.md` | 全体の流れ・トーク例 |
| ヒアリング質問リスト | `.company/outputs/sales-content/individual-zoom-30min/hearing-questions.md` | 5〜15分パート |
| クロージングフロー | `.company/outputs/sales-content/individual-zoom-30min/closing-flow.md` | 25〜30分パート |
| 商談用スライド | `.company/outputs/sales-content/individual-zoom-30min/slides.pptx` | 当日画面共有 |

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程3の成果物。*
*最終更新: 2026-06-09*
