# list-builder v2 工程3 進捗まとめ

- **作成日**: 2026-05-04
- **ステータス**: 調査・設計完了 / 実装は工程7へ
- **担当**: executor (Claude Sonnet 4.6)

---

## 1. 法的判定結果サマリー

| ソース | 判定 | 理由 | 実装可否 |
|---|---|---|---|
| Wantedly (a3) | ❌ NG | サイト内にスクレイピング禁止の明示あり | 不可 |
| リクナビNEXT (a3) | ❌ NG | robots.txt に `/api/` Disallow | 不可 |
| エン転職 (a3) | ❌ NG | robots.txt で ClaudeBot を全サイト Disallow | 不可 |
| doda (a3) | ❌ NG | Bot防御で取得不可（採用媒体として禁止前提） | 不可 |
| 商工会議所名簿 (a4) | ✅ 条件付き OK | 公開情報・明示禁止なし | 低頻度取得なら可 |
| Google Maps API (a5) | ✅ OK | 公式API正規利用 | 完全可 |

**結論**: 採用媒体 (a3) は全4サービスが NG。工程3の実装ソースは **a5（Google Maps）と a4（商工会議所）** に絞る。

---

## 2. 推奨ソースランキング Top 3

### 1位: Google Maps API（a5）— 即実装推奨

**理由**:
- 既存コード（v1）がすでに動作している
- 公式API利用で法的リスクゼロ
- 非首都圏フィルタ・規模推定を追加するだけで v2 完成
- 1回の実行で20〜50社取得可能

**実装工数**: 半日〜1日（既存コードへの差分追加）

---

### 2位: 商工会議所名簿（a4）— Phase 2 推奨

**理由**:
- 法的に条件付きOK（採用媒体より安全）
- 業種・地域絞り込みが可能なサイトが複数確認できた
- 代表者名・事業概要も取得可能で DM パーソナライズ精度向上

**実装工数**: 2〜3日（サイト別スクレイパー作成 × 5サイト）

**対象サイト（優先順）**:
1. 新潟商工会議所: http://www.niigata-cci.or.jp/db/（業種×地域2軸）
2. 鹿児島商工会議所: https://www.kagoshima-cci.or.jp/meikan/index.php（代表者名あり）
3. 長野商工会議所: https://www.nagano-cci.or.jp/search/（業種フィルタあり）
4. 札幌商工会議所: https://www.sapporo-cci.or.jp/web/purpose/01/e_search.html（エリア×業種）
5. 金沢商工会議所: https://www.kanazawa-cci.or.jp/service/info/companylink.html（五十音一覧）

---

### 3位: gBizINFO（経産省公式API）— 調査推奨

**理由**:
- 経産省が提供する公式の法人情報API（無料）
- 業種・都道府県・従業員数でフィルタリング可能
- スクレイピング不要でAPIキー不要
- 採用媒体に比べリスクゼロ

**課題**: 工程3の要件定義書に記載がないため、工程7または次フェーズで追加検討推奨

**調査URL**: https://info.gbiz.go.jp/

---

## 3. 成果物一覧

| ファイル | 内容 | ステータス |
|---|---|---|
| `.company/research/sales-source-legal-review.md` | 5ソースの法的確認結果 | 完成 |
| `.company/research/chamber-of-commerce-sources.md` | 商工会議所5件の公開名簿調査 | 完成 |
| `.company/engineering/docs/list-builder-v2-design.md` | 既存コード分析 + v2 設計書 | 完成 |
| `/opt/sales-ops/migrations/002_source_check_expansion.sql` | companies.source CHECK制約拡張 | VPS配置済み（未実行） |
| `/opt/sales-ops/migrations/002_source_check_expansion_rollback.sql` | ロールバックSQL | VPS配置済み（未実行） |

---

## 4. マイグレーション準備状況

### 002_source_check_expansion.sql

**変更内容**: `companies.source` の CHECK 制約に以下を追加

```
現在: CHECK(source IN ('google_maps', 'biz_db', 'manual'))
変更後: CHECK(source IN ('google_maps', 'biz_db', 'manual',
                          'chamber_of_commerce', 'wantedly',
                          'rikunabi', 'enjapan', 'doda'))
```

**配置場所**: `/opt/sales-ops/migrations/002_source_check_expansion.sql`
**実行コマンド**: `python3 /opt/sales-ops/migrations/run_migration_v2.py --file 002_source_check_expansion.sql`
**注意**: VPS上での実行はオーナー承認後に行うこと。現時点では SQL ファイルの配置のみ完了。

---

## 5. 次アクション（次フェーズ・実装フェーズ）

### 短期（工程7で実装）

- [ ] `list_builder_v2.py` の実装（設計書 `list-builder-v2-design.md` に従う）
  - 非首都圏フィルタ（30都市ローテーション）
  - AI/IT系除外ロジック
  - `prefecture` / `is_metro` 自動セット
  - 規模推定（Claude Haiku API）
- [ ] `002_source_check_expansion.sql` の VPS 実行（オーナー承認後）
- [ ] `run_list_builder.py` を v2 に切り替え

### 中期（工程8後）

- [ ] 商工会議所スクレイパー実装（優先5サイト）
  - 新潟 → 鹿児島 → 長野 → 札幌 → 金沢の順で着手
- [ ] gBizINFO API の調査・評価

### 長期（次フェーズ）

- [ ] Wantedly / 採用媒体の公式API交渉（提携の可能性探索）
- [ ] 全国商工会議所ネットワークのカバレッジ拡大（30都市以上）

---

## 6. 工数見積もり（実装フェーズ）

| タスク | 工数 | 担当 |
|---|---|---|
| list_builder_v2 実装（a5） | 0.5日 | executor |
| マイグレーション実行 | 0.1日 | executor |
| run_list_builder.py 切り替え | 0.5日 | executor（工程7） |
| テスト作成・実行 | 0.5日 | executor |
| 商工会議所スクレイパー 5サイト | 2〜3日 | executor（工程7以降） |
| **合計（a5先行）** | **1.5日** | |
| **合計（a4含む完全版）** | **4〜5日** | |
