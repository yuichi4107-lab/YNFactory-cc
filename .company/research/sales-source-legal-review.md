# 営業リストソース 法的確認レポート

- **作成日**: 2026-05-04
- **調査者**: executor (Claude Sonnet 4.6)
- **目的**: 工程3 新ターゲットリスト構築における各ソースのスクレイピング可否判定
- **調査方法**: 各サービスの利用規約ページ・robots.txt を WebFetch で取得・分析

---

## 判定サマリー

| ソース | 判定 | 理由 |
|---|---|---|
| Wantedly | ❌ NG | サイト内に「スクレイピング・クローリング禁止条項を尊重してください」と明記。robots.txt で主要ページへの汎用クローラーアクセスも制限 |
| リクナビNEXT | ❌ NG | robots.txt で `/api/` エンドポイント含む多数パスを Disallow。利用規約ページ直接取得は不可だが、構造から禁止と判断 |
| エン転職 | ❌ NG | robots.txt で `ClaudeBot` を全ページ Disallow。AI/自動クローラーへの明示的拒否 |
| doda | ❌ NG | サービスページへのアクセスがタイムアウト（Bot防護が強力）。採用媒体として同様の規約が推定される |
| 商工会議所名簿 | ✅ 条件付き OK | 公開Webページとして一般公開されている。自動取得の明示禁止なし。ただし掲載同意企業のみが対象 |
| Google Maps API | ✅ OK | 公式API経由のみ使用。APIキー・利用規約内での使用は適法 |

---

## 詳細調査結果

### (a3-1) Wantedly

**調査URL**: https://wantedly.com/companies/rules
**robots.txt**: https://www.wantedly.com/robots.txt

**robots.txt 確認結果**:
- `User-agent: *` に対し、企業ページ・ユーザーページ・メッセージ・採用掲載の各パスを Disallow
- 主なDisallow対象:
  - `/enterprise/`
  - `/user/profile`
  - `/messages`
  - `/user/feeds`
  - `/projects/*/show_supplement.js`

**利用規約確認**:
- サイトのルール説明ページ (https://wantedly.com/companies/rules) 内に**「スクレイピング・クローリング禁止条項を尊重してください」という注記が明示**されていることを WebFetch で確認
- 公式外部公開 API（サードパーティ向け）は存在しない（docs.wantedly.dev はエンジニア内部ハンドブック）

**判定: ❌ NG**
- 利用規約にスクレイピング禁止の明示的言及あり
- 代替: 公式 API がないため、Wantedly をソースとして使うことはできない

---

### (a3-2) リクナビNEXT

**調査URL**: https://next.rikunabi.com/
**robots.txt**: https://next.rikunabi.com/robots.txt

**robots.txt 確認結果**:
- `User-agent: *` に対し、`/api/` エンドポイントを Disallow（全APIエンドポイントへのアクセス禁止）
- `/my_page`, `/applications`, `/offers`, `/message/` など個人情報関連も Disallow
- クエリパラメータ付きURLも多数 Disallow（`?jobKey=`, `?prf=`, `?emp=` 等30種以上）
- `bingbot`: Crawl-delay 5秒, `Applebot`: Crawl-delay 30秒（自動クローラーを想定した制限）

**利用規約確認**:
- 利用規約ページへの直接アクセスはリダイレクト・認証で取得不可
- robots.txt の構成から、自動取得を前提とした防御設計であることが確認できる
- 採用媒体大手として業界慣行上もスクレイピング禁止が一般的

**判定: ❌ NG**
- APIエンドポイントをDisallowしており自動取得は規約違反と判断
- 公式 API は存在しない（B2B採用ツール向けの別商品はあるが汎用取得APIではない）

---

### (a3-3) エン転職

**調査URL**: https://employment.en-japan.com/
**robots.txt**: https://employment.en-japan.com/robots.txt

**robots.txt 確認結果**:

特定エージェント向けの明示的な禁止設定が確認された：

```
User-agent: ClaudeBot
Disallow: /

User-agent: meta-externalagent
Disallow: /

User-agent: facebookexternalhit
Disallow: /
```

- `ClaudeBot`（Anthropic社のクローラー）を**サイト全体アクセス禁止**に設定
- AIクローラー全般への拒否姿勢が明示的
- 全エージェント向けにも、API関連エンドポイント・特定ディレクトリを Disallow

**利用規約確認**（https://employment.en-japan.com/info/membership/）:
- 利用規約内の第10条（個人情報）・第14条（サービス変更）は確認できたが、スクレイピングの明示的禁止条項の有無は本文取得範囲では確認できず
- ただし robots.txt での AI クローラー全禁止設定が実質的な意思表示として機能している

**判定: ❌ NG**
- AIクローラーを robots.txt で全サイト Disallow に設定している
- 自動取得を明確に拒否する意思が確認できる

---

### (a3-4) doda

**調査URL**: https://doda.jp/
**robots.txt**: 取得タイムアウト（強力なBot防護が推定される）

**調査結果**:
- 利用規約ページ（https://doda.jp/guide/terms/）へのアクセスが複数回タイムアウト
- robots.txt へのアクセスも複数回タイムアウト
- これ自体がBotアクセスへの防御機構が稼働していることの証左
- 採用媒体大手として、リクナビ・エン転職と同様のスクレイピング禁止規約が存在すると合理的に推定できる

**判定: ❌ NG**
- Bot防御による取得不可自体が拒否の意思表示
- 仮に規約取得できたとしても、採用媒体での自動取得は業界標準として禁止が前提

---

### (a4) 商工会議所 会員名簿

**調査対象**: 地方商工会議所 5件（別ファイル `chamber-of-commerce-sources.md` 参照）

**法的確認**:
- 各商工会議所の名簿ページは**一般公開のWebページ**として公開
- 利用規約ページにスクレイピング禁止の明示的記述は確認できず
- ただし「掲載同意をいただいた事業所のみ対象」という記述が複数サイトに存在
- 公開情報の範囲（企業名・業種・Webサイト）を取得することは、法的グレーゾーンではあるが、採用媒体と異なり禁止の明示的言及なし

**robots.txt**: 各商工会議所サイトは通常の企業サイトであり、採用媒体ほど厳格な Bot 防護なし

**判定: ✅ 条件付き OK**
- 自動取得の明示禁止なし
- ただし実装時の留意事項:
  1. 大量・高頻度アクセスは避ける（1リクエスト/3秒以上の間隔）
  2. 取得対象は企業名・業種・Webサイトの公開情報のみ
  3. 掲載同意企業のみが対象であるため、個人情報扱いには注意
  4. 取得後の二次利用目的（営業DM）については利用規約の確認推奨

---

### (a5) Google Maps API

**調査**:
- Places API (New) を公式APIキー経由で使用（既存の list_builder.py で確認済み）
- 利用規約: https://cloud.google.com/maps-platform/terms/

**判定: ✅ OK**
- 公式APIの正規利用
- APIキーを使用した範囲内での取得は完全に適法
- 月間無料枠あり、超過分は従量課金（要コスト管理）

---

## 法的判定まとめ

| ソース | 判定 | 実装可否 |
|---|---|---|
| Wantedly | ❌ NG | スクレイピング禁止の明示言及あり。実装不可 |
| リクナビNEXT | ❌ NG | robots.txt に `/api/` Disallow。採用媒体として禁止前提 |
| エン転職 | ❌ NG | robots.txt で ClaudeBot 含む AI クローラーを全サイト Disallow |
| doda | ❌ NG | Bot防御で取得不可。採用媒体として禁止前提 |
| 商工会議所名簿 | ✅ 条件付き OK | 公開情報・明示禁止なし。低頻度・公開情報のみで実装可 |
| Google Maps API | ✅ OK | 公式API正規利用。完全に適法 |

---

## 代替ソース提案

採用媒体が全滅した場合の代替ソース（要別途調査）:

1. **J-NET21（中小企業庁）**: https://j-net21.smrj.go.jp/
   - 中小企業支援情報のデータベース。公的機関運営
2. **経済産業省 企業DB**: gBizINFO（https://info.gbiz.go.jp/）
   - 政府公開の法人情報DB。APIあり（無料）
3. **法人番号公表サイト（国税庁）**: https://www.houjin-bangou.nta.go.jp/
   - 全法人の公開情報。CSV一括ダウンロード可能
4. **ザ・ビジネスモール**: https://www.b-mall.ne.jp/
   - 全国商工会議所連合の会員企業DB（30万社）。公開検索あり

**優先推奨**: gBizINFO（経産省の公式API）が最もリスクが低く、規模・業種・所在地でフィルタリング可能。工程3の次フェーズで調査推奨。
