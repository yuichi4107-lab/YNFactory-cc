# CEO判断ログ: Sales OS（営業自律実行システム）立ち上げ

- **日付**: 2026-04-19
- **発議**: オーナー（「営業が弱い、自律的に毎日考えて実行してほしい」）
- **ステータス**: 決裁済み（設計書オーナー承認）
- **関連ドキュメント**: `.company/engineering/docs/sales-ops-design.md`

## 決定事項

1. **プロジェクト名**: Sales OS
2. **スコープ**: 3軸並行の営業オペレーション自律化
   - 軸A: フリーランス案件獲得
   - 軸B: YNツール集客
   - 軸C: 法人AIコンサル（**メイン**）
3. **実装方針**: 案Y（Track別マイクロパイプライン）を採用
4. **実行エンジン**: E3（VPS cron + Claude Code朝セッション ハイブリッド）
5. **外部送信ポリシー**: P2（朝バッチ承認制）— 全軸統一
6. **軸Cターゲット**: T1（中小企業経営者）+ T2（士業・制作会社）
7. **軸Cオファー**: O3（yn-tools法人プラン月2万〜）フロント + O1（AI顧問）アップセル
8. **段階実装**: Phase 1〜4（Phase1-3 で 55-75h、4-6週間）
9. **KGI**: 2026-06-30時点で MRR 20万円

## 振り分け計画（PM向け）

### Phase 1（優先度: 最高、着手: 即）
- 軸CのMVP（list_builder → personalizer → approval_queue → gmail_sender → /sales-briefing）
- PMはこれを5-7工程に分解しチケット化
- executor → quality-checker（85点以上で次工程）のループで実装

### Phase 2 以降
- Phase 1完了後にPMが再度チケット生成

## 他プロジェクトとの干渉

- JP-DAYTRADEは戦略ピボット探索フェーズ中（並行して進められる）
- AI投資ショート戦略は工程7でAPIキー待ち（並行可）
- ばんえい予想はVPS本番稼働中（干渉なし、同じVPS上で別ディレクトリ）

## リスク認識

- VPS同時稼働プロジェクトが増える（ばんえい + sales-ops）→ リソース監視が必要
- 送信誤爆の法人向けリスクは P2 承認制で低減
- Google Maps APIの無料枠を超えると有料化必要

## 次のアクション

1. `writing-plans` スキルで Phase 1 の実装プランを作成
2. プランを `.company/engineering/plans/sales-ops-phase1-plan.md` に保存
3. PMがプランから `pm/tickets/` にチケット生成
4. executor で工程1から実装開始
