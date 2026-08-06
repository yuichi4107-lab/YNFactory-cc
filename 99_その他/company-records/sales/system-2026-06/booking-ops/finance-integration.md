# 経理連携 — 成約から請求書発行まで

- **担当**: Claude支援（オーナーが起動）
- **目標時間**: 契約締結後24時間以内に請求書生成・保存完了
- **保存先**: `.company/finance/invoices/`
- **経理ルール準拠**: `.company/finance/CLAUDE.md`

---

## 全体の流れ

```
契約書返送（成約確定）
        ↓
[STEP 1] 請求書データを整理（2分）
        ↓
[STEP 2] 請求書を生成（Claude支援 / 3分）
        ↓
[STEP 3] .company/finance/invoices/ に保存（1分）
        ↓
[STEP 4] 顧客に請求書を送付（オーナー実行 / 5分）
        ↓
[STEP 5] PMにプロジェクト作成依頼（2分）
        ↓
[STEP 6] MRRをDASHBOARD_SALES.mdに反映（1分）
```

---

## STEP 1: 請求書データを整理

以下の情報を確認する（クライアントファイルと契約書から）。

| 項目 | 内容 | 参照先 |
|---|---|---|
| 顧客会社名 | {{client_company_name}} | クライアントファイル |
| 担当者名（請求書宛名） | {{contact_name}} 様 | クライアントファイル |
| プラン名 | L1 ライト顧問 / L2 スタンダード顧問 / L3 集中導入PJ | 契約書 |
| 月額（税抜） | 40,000円 / 80,000円 | 契約書 |
| 消費税（10%） | 4,000円 / 8,000円 | 計算 |
| 月額（税込） | 44,000円 / 88,000円 | 計算 |
| L3の場合: 総額（税抜） | 300,000円 | 契約書 |
| L3の場合: 総額（税込） | 330,000円 | 計算 |
| 契約開始月 | {{YYYY-MM}} | 契約書 |
| 支払期日 | 月末締め翌月末払い（標準） | 契約書 |
| 請求書番号 | {{contract_number}}-INV-001 | 契約番号から生成 |
| 振込先 | 後述の振込先情報 | オーナー管理 |

---

## STEP 2: 請求書を生成

### 方法A: Claudeに生成させる（推奨）

以下のプロンプトをClaudeに実行させる。

```
## 請求書生成プロンプト

以下の情報で請求書Markdownを生成してください。
.company/finance/CLAUDE.md のルール（請求書ステータス: draft → sent → paid → overdue、金額は税込・税抜を明記）に従ってください。

### 入力情報

- 請求書番号: {{contract_number}}-INV-001
- 発行日: {{YYYY-MM-DD}}
- 支払期日: {{YYYY-MM-DD}}（標準: 月末締め翌月末払い）
- 請求先会社名: {{client_company_name}}
- 請求先担当者名: {{contact_name}}
- 件名: AI活用顧問委託料（{{プラン名}} / {{請求対象月}}月分）
- 月額（税抜）: {{金額}}円
- 消費税（10%）: {{消費税額}}円
- 月額（税込）: {{税込金額}}円

### 振込先（オーナーが記入して使う）
- 金融機関名:
- 支店名:
- 口座種別:
- 口座番号:
- 口座名義:

---

出力: 以下のテンプレートに従ったMarkdown形式の請求書。
ヘッダーのFrontmatter（date/client/amount/status/due_date）を正しく埋めること。
```

### 方法B: テンプレートから手動作成

`.company/finance/invoices/_template.md` をコピーし、以下の項目を記入する。

> 注意: `_template.md` の既定は `status: unpaid` だが、これは `.company/finance/CLAUDE.md` のフロー（draft→sent→paid→overdue）に存在しないステータスである。コピー後は必ず `status: draft` に書き換えること。

```markdown
---
date: "{{YYYY-MM-DD}}"
client: "{{client_company_name}}"
amount: {{税込金額}}
status: draft
due_date: "{{YYYY-MM-DD}}"
---

# 請求書: {{client_company_name}} - {{YYYY-MM-DD}}

**請求書番号**: {{contract_number}}-INV-001
**発行日**: {{YYYY-MM-DD}}
**お支払期日**: {{YYYY-MM-DD}}

**請求先**:
{{client_company_name}}
{{contact_name}} 様

## 明細

| 項目 | 数量 | 単価（税抜） | 小計（税抜） |
|------|------|------|------|
| AI活用顧問委託料（{{プラン名}} / {{請求対象月}}月分） | 1 | {{金額}}円 | {{金額}}円 |

## 合計

| 項目 | 金額 |
|---|---|
| 小計（税抜） | {{金額}}円 |
| 消費税（10%） | {{消費税額}}円 |
| **合計（税込）** | **{{税込金額}}円** |

## お振込先

| 項目 | 内容 |
|---|---|
| 金融機関 | （銀行名） |
| 支店名 | （支店名） |
| 口座種別 | 普通 |
| 口座番号 | （口座番号） |
| 口座名義 | ナカタ ユウイチ / YN Factory 中田雄一 |

## 支払い状況

- [ ] 送付済み
- [ ] 入金確認済み

---

発行者: YN Factory 中田雄一（info@yn-factory.com）
```

---

## STEP 3: ファイルに保存

以下のパスルールで保存する（`.company/finance/CLAUDE.md` のルール準拠）。

```
.company/finance/invoices/{{YYYY-MM-DD}}-{{client_company_name}}.md
```

**例**:
```
.company/finance/invoices/2026-07-15-yamamoto-tax.md
```

---

## STEP 4: 顧客に請求書を送付（オーナー実行）

請求書Markdownをメール添付のためにPDF化する方法（どれかを選ぶ）。

1. Markdown → PDF変換ツールを使う（Pandoc等、VPS上で `pandoc invoice.md -o invoice.pdf`）
2. ブラウザでMarkdownファイルを開き、印刷→PDF保存
3. Word/Googleドキュメントに貼り付けてPDF出力

**送付メール件名例**: 「【YN Factory】{{請求対象月}}月分 AI活用顧問委託料 ご請求書送付のご連絡」

---

## STEP 5: PMにプロジェクト作成依頼

成約した案件は `.company/sales/CLAUDE.md` の受注時ルールに従い、PMにプロジェクト作成を依頼する。

```markdown
## PM向けプロジェクト作成依頼

以下の案件が成約しました。プロジェクトを `pm/projects/` に作成してください。

- **プロジェクト名**: AI顧問サポート - {{company_name}}
- **プラン**: {{L?}} {{プラン名}}
- **契約開始日**: {{YYYY-MM-DD}}
- **月額MRR**: {{金額}}円/月
- **担当者**: 中田雄一（オーナー）
- **MTG頻度**: 月1回（L1）/ 月2回（L2）/ 週1回（L3）
- **契約書パス**: `.company/sales/clients/contracts/{{YYYY-MM-DD}}-contract-{{company_name}}.pdf`
```

---

## STEP 6: MRRをDASHBOARD_SALES.mdに反映

成約を`.company/DASHBOARD_SALES.md`（工程5で作成）の以下のセクションに反映する。

- 「現状スナップショット」の「成約数」と「MRR」を更新する
- 「ファネル可視化」の成約数を更新する
- 「アクション待ち一覧」から該当案件を完了に移す

---

## MRR・請求条件まとめ

| プラン | 月額（税抜） | 月額（税込） | 支払条件 | 請求タイミング |
|---|---|---|---|---|
| L1 ライト顧問 | 40,000円 | 44,000円 | 月末締め翌月末払い | 月初に当月分を請求 |
| L2 スタンダード顧問 | 80,000円 | 88,000円 | 月末締め翌月末払い | 月初に当月分を請求 |
| L3 集中導入PJ | 300,000円（総額・税抜） | 330,000円（総額・税込） | 契約締結時一括前払い | 契約締結直後 |

> L3の場合、契約締結直後に3ヶ月分を一括請求する。

---

## 継続請求（L1/L2）の月次作業

毎月1日（または月初最初の営業日）に以下を実行する。

- [ ] 当月分の請求書を生成した（STEP 2 を繰り返す。請求書番号をインクリメント）
  - 番号例: `2026-001-INV-001` → `2026-001-INV-002` → ...
- [ ] `.company/finance/invoices/` に保存した
- [ ] 顧客に送付した
- [ ] ファイルの `status: sent` に更新した
- [ ] 入金確認後: `status: paid` に更新した
- [ ] 未入金の場合（期日から7日後）: 秘書のTODOにリマインダーを追加する

---

## 解約・終了時の経理処理

顧客から解約連絡を受けた場合:

- [ ] 最終月の請求書を発行した（月途中解約の場合は日割り計算）
- [ ] クライアントファイルのステータスを `inactive` に更新した
- [ ] PMにプロジェクトのクローズを依頼した
- [ ] `DASHBOARD_SALES.md` のMRRを更新した

---

*本ファイルは `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程3の成果物。*
*経理ルール参照: `.company/finance/CLAUDE.md`*
*最終更新: 2026-06-09*
