# -*- coding: utf-8 -*-
"""G2 Step1: OOF（out-of-fold）方式でisotonic較正曲線を学習する

学習データ（≤2025-12-31、Bモデルと同一）を race_id 単位の5-foldに分割し、
各foldの検証予測を集めて「モデル出力確率 → 実確率」の較正曲線を2本学習:
  - iso_top3: score → P(3着以内)
  - iso_win:  score → P(1着)   ※Harville近似の入力に使う
OOS期間（2026-03-14以降）には一切触れない。

出力: /tmp/g2_cal_no_odds.pkl, /tmp/g2_cal_full.pkl
      （dict: iso_top3, iso_win, oof_brier_raw, oof_brier_cal, n）
"""
import sys, os, time, pickle
sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
os.chdir("/opt/keiba-unified/jra")
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.isotonic import IsotonicRegression
import model_v2

FEATS = "/tmp/train_feats_v3.pkl"
TRAIN_END = "2025-12-31"

PARAMS = {
    "objective": "binary", "metric": "binary_logloss", "boosting_type": "gbdt",
    "num_leaves": 63, "learning_rate": 0.05, "feature_fraction": 0.8,
    "bagging_fraction": 0.8, "bagging_freq": 5, "min_child_samples": 50,
    "lambda_l1": 0.1, "lambda_l2": 1.0, "verbose": -1, "n_jobs": -1,
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main():
    df = pd.read_pickle(FEATS)
    df = df[df["date"] <= TRAIN_END].reset_index(drop=True)
    log(f"train rows={len(df)} (<= {TRAIN_END})")
    win_label = (df["finish_position"] == 1).astype(int).values

    for kind, cols in [("no_odds", model_v2.FEATURE_COLS_NO_ODDS),
                       ("full", model_v2.FEATURE_COLS_FULL)]:
        X = df[cols].values
        y = df["label"].values
        groups = df["race_id"].values
        oof = np.full(len(df), np.nan)
        gkf = GroupKFold(n_splits=5)
        for fold, (tr, va) in enumerate(gkf.split(X, y, groups)):
            dtr = lgb.Dataset(X[tr], label=y[tr])
            dva = lgb.Dataset(X[va], label=y[va], reference=dtr)
            m = lgb.train(PARAMS, dtr, num_boost_round=600, valid_sets=[dva],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
            oof[va] = m.predict(X[va], num_iteration=m.best_iteration)
            log(f"{kind} fold{fold+1}: best_iter={m.best_iteration}")
        assert not np.isnan(oof).any()

        iso_top3 = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso_top3.fit(oof, y)
        iso_win = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso_win.fit(oof, win_label)

        brier_raw = float(np.mean((oof - y) ** 2))
        brier_cal = float(np.mean((iso_top3.predict(oof) - y) ** 2))
        out = dict(iso_top3=iso_top3, iso_win=iso_win,
                   oof_brier_raw=brier_raw, oof_brier_cal=brier_cal, n=len(df))
        with open(f"/tmp/g2_cal_{kind}.pkl", "wb") as f:
            pickle.dump(out, f)
        log(f"{kind}: OOF Brier raw={brier_raw:.5f} -> cal={brier_cal:.5f} saved")

        # 参考: 較正曲線の形（10分位）
        qs = np.quantile(oof, np.linspace(0, 1, 11))
        for i in range(10):
            m_ = (oof >= qs[i]) & (oof <= qs[i + 1])
            log(f"  bin{i}: pred={oof[m_].mean():.3f} actual={y[m_].mean():.3f} "
                f"cal={iso_top3.predict(oof[m_]).mean():.3f}")
    print("G2 CALIBRATION DONE", flush=True)


if __name__ == "__main__":
    main()
