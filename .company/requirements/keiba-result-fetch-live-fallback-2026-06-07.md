---
title: JRA競馬 結果取得の当日ライブ・フォールバック追加
date: 2026-06-07
status: approved
owner: secretary/engineering
related: last_session_summary_v2026_06_06_keiba_no_odds
---

# 要件定義書: 結果(着順)自動取得の修復 — 当日ライブ・フォールバック追加

## 背景 / 発端
オーナーTelegram報告「競馬予想の結果について、推奨レースがあるのに『推奨レースなし』となっている」。
本番VPS(163.44.101.31 /opt/keiba-unified/jra)のDB・ログを直接調査し、**予想は正常・結果(着順)取得が壊れている**ことを確認。

## 根本原因（確定）
`check_results.py scrape_day_results()` の結果取得2経路が両方失敗:
1. **JRA公式**: `_build_jra_result_cname_map()` が0件を返す（4/4までは正常→6/6・6/7で回帰）。
2. **netkeibaフォールバック `scrape_race()`**: `db.netkeiba.com`（履歴DB＝当日反映が遅い）を参照。17:30時点で `race_table_01` 未掲載 → 「No result table」。

結果 → 全23レース `finish_position=0` → 照合可能な完走レース0 → 各ソースで「推奨レースなし」表示。
レポートのヘッダ「推奨:N」と本文「推奨レースなし」の矛盾もこれが原因。

実証: 当日ライブ結果ページ `race.netkeiba.com/race/result.html?race_id=...`（**EUC-JP**・`ResultTableWrap`/`All_Result_Table`・払戻 `Payout_Detail_Table`）には17:30時点で着順・払戻が掲載済。手動で全レース着順・払戻をパース可能と確認。

## ゴール
毎週末の結果照合(17:30 cron)で、当日中に着順・払戻が確実に取得され、的中/回収/ROIが正しく集計される。

## スコープ
### やる
1. `scraper_legacy.py` に当日ライブ取得関数 `scrape_result_live_netkeiba(race_id, conn)` を新規追加。
   - `race.netkeiba.com/race/result.html` を EUC-JP デコード。
   - 着順テーブル → 既存 results 行を `UPDATE results SET finish_position=? WHERE race_id=? AND horse_number=?`（エントリ情報を壊さない）。
   - 払戻テーブル `Payout_Detail_Table` → `payouts` に INSERT OR REPLACE。
     - bet_type 正規化: `3連複→三連複`, `3連単→三連単`（他はそのまま）。
     - combination 形式: 既存DB踏襲の `"a - b"`（馬連/枠連/ワイド/三連複は数値昇順ソート）。payout は円数値、人気は整数。
   - 成功条件: 着順>0 を1件以上書き込めた場合 True。
2. `check_results.py scrape_day_results()` の取得順を **JRA公式 → 当日ライブnetkeiba → db.netkeiba(履歴)** に変更（当日ライブを優先フォールバックに挿入）。
3. 今日6/7分を**バックフィル**して正しいレポート相当を再生成・検証。
4. JRA公式CNAME取得が0件になる回帰の**原因調査**（最低限の切り分け。ライブnetkeibaフォールバックで実害は解消するため、恒久JRA修正は別チケット可）。
5. 本番(VPS)反映 + Drive正本(keiba-unified/)へ同期。

### やらない
- 予想ロジック・閾値・配分の変更（無関係）。
- 馬単/三連単など現行予想が使わない券種の照合最適化（payoutsには格納するが照合対象外）。
- JRA公式パスの恒久的な作り直し（今回は調査メモまで。フォールバックで担保）。

## 完了条件（検証可能チェックリスト）
- [ ] `scrape_result_live_netkeiba` が今日の推奨5レースで着順>0をDBに書き込む。
- [ ] 同関数が `payouts` に馬連・三連複の払戻を正しい bet_type / combination 形式で格納。
- [ ] `check_results.py` 再実行で、6/7の各ソースが「推奨レースなし」ではなく推奨レース数・的中/不的中・ROIを表示。
- [ ] 手動復元値（朝 阪神2R[10,5,3]/阪神6R[4,11,15]不的中、ライブ 東京5R[2,4,3]不的中、C3 阪神7R[8,5,16]/阪神9R[4,10,14]不的中）と一致。
- [ ] 既存の正常系（過去日のdb.netkeiba取得）を壊さない（フォールバック順序のみ追加）。
- [ ] 冪等性: 既に finish_position>0 のレースはスキップ（再実行で二重加算しない）。
- [ ] 本番VPS反映 + Drive正本同期完了。

## 品質基準（採点観点）
- 正確性: 着順・払戻のパースが手動復元値と完全一致。
- 堅牢性: EUC-JPデコード、テーブル未掲載時の安全な False 返却、例外で全体を落とさない。
- 非破壊: 既存results行のエントリ情報・他経路を壊さない。冪等。
- 影響局所化: 変更は結果取得経路のみ。予想系に副作用なし。

## 工程
- 工程1: ライブ取得関数の実装＋単体検証（推奨5レースで着順・払戻一致）。
- 工程2: scrape_day_results へのフォールバック組込み＋6/7バックフィル＋レポート再生成検証。
- 工程3: JRA公式回帰の原因切り分けメモ。
- 工程4: 本番反映・Drive同期・ハンドオフ。
