# -*- coding: utf-8 -*-
"""配当均等反実仮想（_counterfactual_eq_payout）の検証テスト

VPS上で実行（本番DBのコピーに対して。本番は無改変）:
    cd /opt/keiba-unified/jra && cp data/keiba_live.db /tmp/cf_test.db && python3 test_cf_eq.py

テスト内容（2026-07-11に実施し合格）:
  A) 方向テスト: 的中レースの勝ち組合せだけ低est_odds(2.0)にすると、
     配当均等回収 > フラット回収 になる
  B) None経路: est_odds未記録の日付では cf_races=0（💱行が出ない）
  ※恒等テスト（均一オッズ→両者一致）は本番フラットの端数処理
   （最終組合せに余りが乗る）のため厳密には一致しない。これは仕様（レポート§3参照）
"""
import sys
import sqlite3

sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
import check_results as CR

DB = "/tmp/cf_test.db"
DATE = "2026-07-11"


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # B) None経路（est_odds未記録のまま）
    res0 = CR._check_source_results(conn, DATE, "morning")
    assert res0["cf_races"] == 0, f"None経路NG: cf_races={res0['cf_races']}"
    print("B) None経路 OK（est_odds未記録日は対象0R）")

    # A) 方向テスト
    c.execute("UPDATE predictions SET est_odds = 50.0 WHERE date=? AND amount>0", (DATE,))
    conn.commit()
    res1 = CR._check_source_results(conn, DATE, "morning")
    for r in res1["results"]:
        if r["hit"]:
            for hd in r["hit_details"]:
                c.execute("""UPDATE predictions SET est_odds=2.0
                             WHERE date=? AND race_id=? AND replace(combination,' ','')=?""",
                          (DATE, r["race_id"], hd["combination"].replace(" ", "")))
    conn.commit()
    res2 = CR._check_source_results(conn, DATE, "morning")
    assert res2["cf_races"] > 0
    assert res2["cf_eq_payout"] > res2["total_payout"], \
        f"方向NG: eq={res2['cf_eq_payout']} flat={res2['total_payout']}"
    print(f"A) 方向テスト OK（eq={res2['cf_eq_payout']:,} > flat={res2['total_payout']:,}）")

    lines = CR._format_source_section(res2, "テスト", conn, DATE)
    cf_lines = [ln for ln in lines if "配当均等" in ln]
    assert cf_lines, "💱行が出力されない"
    print("表示行:", cf_lines[0])
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
