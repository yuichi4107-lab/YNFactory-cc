---
title: 競馬予想AI モデル反映再開 実機作業指示書
status: active
created: "2026-08-18"
target: "JRA中央競馬（keiba-unified/jra）＋ばんえい"
env: "ConoHa VPS 163.44.101.31 /opt/keiba-unified/ ・ Windows（JVデータ）・ Drive/GitHub"
---

# 競馬予想AI モデル反映再開 実機作業指示書

## 0. この指示書の前提

**背景**: データ取得は開催日ごとに継続して動いている。止まっているのは「集めたデータをモデルへ反映する」側で、
最後に本番モデルが更新されたのは **2026-07-05（朝C5bのみ）**。以降6週間、判定待ちのまま放置されている。

**この指示書の情報源はリポジトリの記録（handoff-log 2026-06〜08、TODO、コード）だけで、VPS実機は未確認**。
記録上の期待値と実機の実態がズレている可能性があるため、**S0の棚卸しを必ず先に行い、ズレたら以降の手順を読み替える**。

### 記録上の現況（2026-08-18時点）

| 項目 | 記録上の状態 | 最終更新 |
|---|---|---|
| 朝C5b `model_v2_no_odds.pkl` | 本番。学習≤2026-07-04、閾値0.92 | 2026-07-05 |
| ライブFULL | **学習窓2022-2024のまま**（7/5のOOS対決で「現行維持」判定） | 更新なし |
| `model_jv_no_odds.pkl`（調教8特徴量・84列） | `source=morning_jv` でシャドー並走のみ。学習≤2026-07-11 | 2026-07-12 |
| 配当均等 vs フラット | `est_odds` 記録を7/12から並走開始、約1か月後に判定 | 2026-07-11 |
| ばんえい | 記録上、再学習の実施記録なし。cronは predict / collect / review のみ | 不明 |
| `auto_retrain.py` | 四半期cron（1/4/7/10月2日01:00）だが **AUTO_SWAP=0 の観察モード**。次回2026-10-02 | 2026-07-05 |
| JRA-VAN JVデータ | Windows タスク `YNFactory-JVDataUpdate` 毎日06:05 → VPSへ scp | 2026-07-11 |

### 未決のまま期限を過ぎているもの

1. **JVシャドーの本番差替判定** — 7/26頃に判定する約束。**3週間超過**。
2. **配当均等 vs フラットの切替判定** — 7/12開始・約1か月後＝いま。
3. EV選択器（G2）のライブシャドー開始 — オーナー判断待ち（本指示書の対象外、S1完了後に再提案）。

### 安全ルール（作業中ずっと適用）

- **本番反映・モデル差替・cron変更・DB書き換えは、実行直前に必ずオーナー承認を取る**（`02_設定/docs/approval-rules.md`）。
  読み取り・集計・バックテスト・`/tmp` へのDBコピーは承認不要で進めてよい。
- **DBを触る前に必ずバックアップ**。命名は既存慣例に合わせる: `keiba_live.db.bak.YYYYMMDD_<用途>`。
- **分析は本番DBを直接触らない**。`/tmp/` へコピーし、index を張ってから回す（7月までの標準手順）。
- **Drive側（G:）で `git` を実行しない**。エラーが出たら `git_drive_guard.py check`。
- ターミナル出力は200行以内。大量ログは `head` / `tail` / リダイレクトで抑える。
- スクリプトを書き換えるときは `*.bak.YYYYMMDD_<用途>` を残す（7月までの慣例）。

---

## 1. 作業順

| # | 作業 | 優先 | 目安 | 承認 |
|---|---|---|---|---|
| S0 | 現況棚卸し（実機の実態確認） | 必須・最初 | 30分 | 不要 |
| S1 | JVシャドーの本番差替判定 | **最優先** | 1〜2時間 | 差替時に必要 |
| S2 | 配当均等 vs フラットの切替判定 | 高 | 1時間 | 切替時に必要 |
| S3 | ライブFULLの再学習・再評価 | 中 | 2〜3時間 | 差替時に必要 |
| S4 | ばんえいの再学習要否の確認 | 中 | 30分 | 再学習実行時に必要 |
| S5 | コード所在の一元化（欠落スクリプトの回収） | 中 | 1時間 | push時に不要 |
| S6 | 記録・引き継ぎ | 必須・最後 | 20分 | 不要 |

S1が終わるまでS2以降に進まない。S1の差替はモデル本体の変更で、S2（賭け金配分）の評価前提を変えるため、
**同じ週末に両方を変えない**。片方ずつ入れて、次の週末で効果を確認する。

---

## S0. 現況棚卸し（最初に必ず実行）

目的: 記録と実機のズレを洗い出す。ここで想定外が出たら、以降の手順より**実機の実態を優先**する。

### S0-1. cron と稼働状況

```bash
ssh root@163.44.101.31
crontab -l | grep -i keiba
ls -la /opt/keiba-unified/jra/data/logs/
tail -30 /opt/keiba-unified/jra/data/logs/morning.log
tail -30 /opt/keiba-unified/jra/data/logs/results.log
```

確認すること:
- 記録上の期待cron: 朝7:00 `run_morning` / 7:06 `run_jv_shadow` / 9:30 `run_live` / 9:35 サンタン /
  **19:30 `check_results`**（8/2に17:30から変更）/ 火7:30 enrich / 月18:00 audit / 四半期 auto_retrain
- 直近の土日（8/16・8/17）が正常完了しているか。エラーで落ちている週末がないか。
- **8月に入ってからのTelegram通知が届いているか**をオーナーに確認する。7月以降このプロジェクトの記録が
  一切ないため、「動いているつもりで止まっていた」可能性を先に潰す。

### S0-2. モデルファイルの実態

```bash
ls -la --time-style=long-iso /opt/keiba-unified/jra/data/models/
```

`model_v2_no_odds.pkl` / `model_jv_no_odds.pkl` / ライブFULL用モデル の3つについて、
**ファイル日付が記録（7/5・7/12）と一致するか**を見る。7/12以降に更新されていたら、
誰かが（または auto_retrain が）差し替えている可能性があるので、`.bak.*` を辿って経緯を確認する。

### S0-3. DBの中身

```bash
cp /opt/keiba-unified/jra/data/keiba_live.db /tmp/keiba_check.db
sqlite3 /tmp/keiba_check.db
```

```sql
-- source別の記録件数と期間（morning / live / morning_jv / live_santan があるはず）
SELECT source, COUNT(*) AS races, MIN(date) AS from_d, MAX(date) AS to_d
FROM prediction_results GROUP BY source ORDER BY source;

-- 直近10開催日が精算されているか（未精算日の検出）
SELECT date, source, COUNT(*), SUM(hit), SUM(bet_total), SUM(payout)
FROM prediction_results WHERE date >= '2026-07-12'
GROUP BY date, source ORDER BY date DESC, source;

-- est_odds の記録状況（S2で使う）
SELECT date, COUNT(*) AS n, SUM(est_odds IS NOT NULL) AS with_odds
FROM predictions WHERE date >= '2026-07-12' GROUP BY date ORDER BY date DESC LIMIT 15;

-- データ欠損の再発チェック（7/8に修復した3か所）
SELECT COUNT(*) FROM races WHERE date >= '2026-07-12' AND (track_condition IS NULL OR track_condition = '');
SELECT COUNT(*) FROM results r JOIN races ra ON r.race_id = ra.race_id
WHERE ra.date >= '2026-07-12' AND (r.passing IS NULL OR r.last_3f IS NULL);
```

**`morning_jv` の件数が0、または7月で止まっていたらS1は実施不能**。その場合はシャドーcronが動いていない
ということなので、S1の代わりに「シャドー復旧＋2週末の再取得」に切り替え、オーナーへ報告する。

### S0-4. JVデータの鮮度

Windows側:
```
type C:\Users\fcmdt\jvdata\update.log | more
dir C:\Users\fcmdt\jvdata\jvdata.sqlite
schtasks /query /tn "YNFactory-JVDataUpdate" /v /fo list
```
VPS側:
```bash
ls -la --time-style=long-iso /opt/keiba-unified/jra/data/jvdata.sqlite
```

**VPS側の jvdata.sqlite が数日以上古いと、シャドーの成績自体が鮮度ガードで落ちている可能性がある**。
S1の判定前にここを確認する。

### S0-5. 棚卸し結果の記録

以下の表を埋めてから次へ進む。

| 確認項目 | 記録上の期待 | 実機の実測 | 判定 |
|---|---|---|---|
| 直近土日のcron完走 | 正常 | | |
| `morning_jv` の記録開催日数 | 5週末前後 | | |
| `model_jv_no_odds.pkl` 日付 | 2026-07-12 | | |
| `est_odds` 記録日数 | 7/12以降ほぼ全日 | | |
| jvdata.sqlite 鮮度 | 前日06:05 | | |
| 未精算日 | なし | | |

---

## S1. JVシャドーの本番差替判定【最優先】

### 目的

調教特徴量モデル（`model_jv_no_odds.pkl`）を朝予想の本番へ昇格させるかを決める。
7/12のOOS実験では朝C5b @0.92 で **88.1% → 94.4%（+6.3pt）**、@0.94 で100.7%と採用基準（+2pt）を超えており、
**現時点で最大の改善候補**。ただし本番昇格の判断はフォワード実績（シャドー期間）で行う。

### S1-1. 比較集計

`/tmp/keiba_check.db` に対して実行する（本番DBは触らない）。

```sql
-- 全体比較（シャドー開始 2026-07-18 以降）
SELECT source,
       COUNT(*) AS races,
       SUM(hit) AS hits,
       ROUND(100.0 * SUM(hit) / COUNT(*), 1) AS hit_rate,
       SUM(bet_total) AS bet,
       SUM(payout) AS payout,
       SUM(profit) AS profit,
       ROUND(100.0 * SUM(payout) / SUM(bet_total), 1) AS roi
FROM prediction_results
WHERE date >= '2026-07-18' AND source IN ('morning', 'morning_jv')
GROUP BY source;

-- 週末単位（ロバスト性の確認）
SELECT date, source, COUNT(*) AS races, SUM(hit) AS hits,
       ROUND(100.0 * SUM(payout) / SUM(bet_total), 1) AS roi, SUM(profit) AS profit
FROM prediction_results
WHERE date >= '2026-07-18' AND source IN ('morning', 'morning_jv')
GROUP BY date, source ORDER BY date, source;

-- 上位1日を除外しても優位が残るか（7月までの標準ロバスト性チェック）
-- 各sourceの利益上位1日を特定してから、その日を除いて再集計する
SELECT source, date, SUM(profit) AS profit FROM prediction_results
WHERE date >= '2026-07-18' AND source IN ('morning', 'morning_jv')
GROUP BY source, date ORDER BY source, profit DESC;
```

**注意**: 両者は同じ日に別々にレースを選ぶため、**レース数が揃わない**。ROIの単純比較に加えて、
**同一レースで両者が買った分だけを抜き出した比較**も見る（選択器としての優劣が分離できる）。

```sql
-- 同一レースでの直接対決
SELECT COUNT(*) AS common_races,
       SUM(a.hit) AS morning_hits, SUM(b.hit) AS jv_hits,
       ROUND(100.0 * SUM(a.payout) / SUM(a.bet_total), 1) AS morning_roi,
       ROUND(100.0 * SUM(b.payout) / SUM(b.bet_total), 1) AS jv_roi
FROM prediction_results a
JOIN prediction_results b ON a.date = b.date AND a.race_id = b.race_id
WHERE a.source = 'morning' AND b.source = 'morning_jv' AND a.date >= '2026-07-18';
```

### S1-2. 判定基準

`auto_retrain.py` の差替条件に、フォワード判定として2条件を足したものを使う。

| # | 条件 | 基準 |
|---|---|---|
| 1 | サンプル数 | 両者とも **60レース以上**（未達なら判定不能→シャドー継続） |
| 2 | ROI | JVが本番を **+3pt超** 上回る |
| 3 | 的中率 | JVの的中率が本番より **-1pt以内**（大きく落ちていない） |
| 4 | ロバスト性 | 利益上位1日を除外しても2の優位が維持される |
| 5 | 週末勝率 | 週末単位でJVが **過半数で勝ち越し** |

- **5条件すべて満たす → 差替を提案し、承認を得て実施（S1-3へ）**
- **1が未達 → シャドーを2週末延長**し、次回判定日をTODOに登録して終了
- **2〜5のいずれか未達 → 差替しない**。シャドーは継続。理由を記録して終了
- **JVが明確に劣る（ROI -3pt超）→ シャドー停止を提案**（cron削除は承認必須）

判定不能・見送りも立派な結論なので、無理に差し替えない。7月の教訓（小標本での過学習実例）を踏襲する。

### S1-3. 差替手順（判定合格かつオーナー承認後のみ）

記録上、差替には以下が必要とされている。**実機のスクリプトを読んで、この2点以外に依存がないか必ず確認してから実施する**。

1. `run_morning.py` のモデルパスと特徴量ビルダーをJV版へ差し替え
2. `auto_retrain.py` の `TRACKS` 定義を更新（再学習対象を新構成に合わせる）

```bash
# 1. バックアップ（必須）
cd /opt/keiba-unified/jra/scripts
cp run_morning.py run_morning.py.bak.$(date +%Y%m%d)_jvswap
cp auto_retrain.py auto_retrain.py.bak.$(date +%Y%m%d)_jvswap
cp ../data/models/model_v2_no_odds.pkl ../data/models/model_v2_no_odds.pkl.bak.$(date +%Y%m%d)_pre_jv

# 2. 編集後、必ず構文チェック
python3 -m py_compile run_morning.py auto_retrain.py

# 3. E2E空撃ち（予測を保存せず・通知を出さずに最後まで通す）
#    ※ 実機のオプション名を --help で確認してから実行すること
python3 run_morning.py --help
```

**E2Eで確認すること**:
- jvdata鮮度ガードが正常に効くか（古いデータで安全停止するか）
- Telegram通知が二重に飛ばないか
- `source` が `morning` で保存されるか（`morning_jv` のまま保存されると集計が壊れる）

**切り戻し手順**（差替後に問題が出たら即実行）:
```bash
cd /opt/keiba-unified/jra/scripts
cp run_morning.py.bak.YYYYMMDD_jvswap run_morning.py
cp auto_retrain.py.bak.YYYYMMDD_jvswap auto_retrain.py
python3 -m py_compile run_morning.py auto_retrain.py
```

### S1-4. 差替後の扱い

- 差替後の**最初の週末は必ず結果を確認する**（19:30の集計とTelegram通知）。
- シャドー枠（`run_jv_shadow.py`）は、差替後は旧モデル側を並走させる形に入れ替えるか、
  役割が無くなったなら停止する。**どちらにするかをオーナーに確認**してから実施する。
- 差替から4週末後に「昇格が正しかったか」を再評価する予定をTODOへ登録する。

---

## S2. 配当均等 vs フラットの切替判定

### 目的

7/12から `est_odds` を記録して並走している「配当均等配分」と現行「フラット配分」を比較し、切替可否を決める。
7/11の再検証では配当均等が **92.6% vs フラット86.8%（+5.8pt）** と優位だったが、これはバックテスト。
今回はフォワード実績で判断する。

### S2-1. データの所在を先に確認

`check_results.py` の `_counterfactual_eq_payout()` は **17:30（現19:30）報告に💱行として表示するための計算**で、
**結果をDBに保存しているかどうかは実機で確認が必要**。

```bash
grep -n "_counterfactual_eq_payout" -A 30 /opt/keiba-unified/jra/scripts/check_results.py | head -60
```

- **保存している場合** → その列/テーブルを集計する
- **保存していない場合** → 日次のTelegram通知ログか `results.log` から💱行を拾って集計するか、
  `predictions.est_odds` と `payouts` から再計算する小スクリプトを書く（`/tmp` で実行、本番DB無改変）

### S2-2. 判定基準

| # | 条件 | 基準 |
|---|---|---|
| 1 | サンプル | **6週末以上**かつ est_odds 記録率が9割以上の日のみ対象 |
| 2 | ROI差 | 配当均等がフラットを **+3pt超** 上回る |
| 3 | ロバスト性 | 利益上位1日を除外しても2が維持される |
| 4 | 月次 | 月別で配当均等が勝ち越している |

満たせば `predictor_v1.py` の `_allocate_by_odds` のウェイトを戻す（現行はフラット化のため `1.0` 固定、
配当均等は `1/est_odds`）。**S1の差替と同じ週末に入れないこと**。

満たさなければフラット継続。並走記録はそのまま続け、次回判定を1か月後にTODO登録する。

---

## S3. ライブFULLモデルの再学習・再評価

### 目的

ライブ予想のFULLモデルは **学習窓2022-2024のまま**で、実質「初期データ」。
7/5に新旧を比較して「現行維持」と判定しているが、**その比較はデータ修復（7/8）より前**で、
`track_condition` が4か月空・通過順欠損というデータで学習・評価していた。**前提が変わったので再評価する**。

### 手順

```bash
cd /opt/keiba-unified/jra/scripts
python3 auto_retrain.py --help   # まずオプションを確認
```

`auto_retrain.py` は「DBコピー → 特徴量並列ビルド → 候補学習（OOS13週除外）→ 本番vs候補OOS対決 →
差替判定 → 全量学習 → pickle構造検証 → swap（バックアップ+自動revert付き）→ Telegram報告」を
一気通貫で行う実装になっている。**`AUTO_SWAP=0`（観察モード）のまま手動実行し、レポートだけ受け取る**。

- 実行は数十分〜かかる想定（7/5のSMOKEテストで11.5分）。`nohup` + ログリダイレクトで回し、
  ターミナルに大量出力を流さない。
- 差替条件は auto_retrain 既定（両者OOS60R以上・ROI+3pt超・的中率-1pt以内）。
- **候補が勝った場合も自動では差し替えない**。オーナー承認を取ってから `AUTO_SWAP` を使うか手動swapする。

### 補足：構造ギャップの扱い

QC指摘として「**全量学習したモデル自体はバックテストされていない**」という構造ギャップが記録されている
（OOS対決に勝った候補と、最終的に本番へ入る全量学習モデルは厳密には別物）。
無人差替（`AUTO_SWAP=1`）を有効化する前に、この点をオーナーと議論する。今回は有効化しない。

---

## S4. ばんえいの再学習要否

記録上、ばんえいは**再学習の実施記録がなく、cronにも再学習タスクがない**（predict / collect / review のみ）。
初期学習のまま運用されている可能性が高い。

```bash
# モデルの最終学習日を確認
ls -la --time-style=long-iso <ばんえいのmodelsディレクトリ>
# 収集データの期間を確認
python3 main.py evaluate --help
```

確認して、
- 直近データで `python3 main.py evaluate` を回し、初期学習時と比べて成績が劣化しているかを見る
- 劣化していれば `python3 main.py train` で再学習し、evaluate で新旧比較（**判定基準はJRAと同じ+3pt/-1pt**）
- 併せて「四半期ごとの再学習をcron化するか」をオーナーに提案する（JRA側の `auto_retrain` と同じ観察モードで）

ばんえいは投資判断に使っていない前提なので、S1〜S3が終わってから着手してよい。

---

## S5. コード所在の一元化

### 現状（このリポジトリで確認済み）

- `05_プロジェクト/keiba-unified/jra/scripts/` には **7/11の `est_odds` 反実仮想まで反映済み**
  （`check_results.py` に `_counterfactual_eq_payout`、`predictions` に `est_odds`）。
- 一方、**7月に新規作成された以下のファイルが存在しない**:
  `auto_retrain.py` / `audit_results.py` / `enrich_results.py` / `run_jv_shadow.py` / `jvdata/`（`jvlink_client.py`, `jv_dump.py`）/ サンタン関連
- handoff-logが参照するコミット `d125302` `02d7f27` は **このリポジトリに存在しない**
  → 別リポジトリ（旧 `yuichi4107-lab/ClaudeCode` の可能性）かVPS単独で作られたとみられる。

### 作業

1. VPS `/opt/keiba-unified/` で `git remote -v` / `git log --oneline -20` を確認し、上記ファイルの出所を特定する
2. 別リポジトリにあるなら、そこから該当ファイルを取り出して Drive正本へ集約する
3. VPSにしか無いファイルは VPS → Drive へコピーする（**VPS側が正**。Drive側の古い版で上書きしない）
4. Drive → ローカル → GitHub の順に同期し、`05_プロジェクト/keiba-unified/` へコミットする
   - **Drive（G:）でgitを実行しない**
   - 差分が大きいので `git status` を必ず確認してからコミットする

これをやっておかないと、次に別PCから触るときに「本番と手元のコードが違う」事故が再発する。
7/11にも「run_today.py のDrive正本が古くVPS版で上書きしてから編集した」という同種の事象が起きている。

---

## S6. 記録・引き継ぎ

1. **判定レポートを残す**: `.company/projects/競馬予想AI/2026-08-XX-<内容>.md`（7月までの慣例に合わせる）
   - S0の棚卸し表、S1〜S3の集計結果と判定、実施したこと・見送ったことと理由、切り戻し手順
2. **TODOを更新**: 7/12・7/16・7/21に残っている以下2件を、実施結果に応じて閉じるか書き換える
   - 「JRA競馬: 次の土曜に(1)朝C5b新モデル初稼働…」
   - 「JRA競馬:【オーナー判断】EV選択器のライブシャドー並走を開始するか」
3. **次回判定日をTODOに登録**（シャドー延長した場合・差替後の再評価・S2の再判定）
4. `HANDOFF.md` の「稼働中システム」行（最終更新 2026-07-05）を更新
5. セッション終了時に `/handoff`

---

## 付録A. 承認が必要な操作の一覧

作業中、以下は**実行直前に個別承認**を取る。一度の承認を次に持ち越さない。

- 本番モデルファイルの差し替え（S1-3、S3）
- `run_morning.py` / `auto_retrain.py` / `predictor_v1.py` の本番編集（S1-3、S2）
- cronの追加・変更・削除（シャドー停止を含む）
- 本番DB（`keiba_live.db`）への書き込みを伴う操作
- `AUTO_SWAP=1` への変更

承認不要で進めてよいもの: 読み取り・`/tmp`へのDBコピー・集計SQL・バックテスト・レポート作成・
バックアップの作成・GitHubへのコード同期。

## 付録B. 判定記録テンプレート

```
### JVシャドー差替判定（判定日: 2026-08-__）

対象期間: 2026-07-18 〜 2026-08-__（__週末）

| 指標 | morning（本番） | morning_jv（シャドー） | 差 |
|---|---|---|---|
| レース数 | | | |
| 的中率 | | | |
| ROI | | | |
| 収支 | | | |
| 上位1日除外ROI | | | |
| 週末勝ち越し | | | |

判定条件: ①60R以上 [ ] ②ROI+3pt超 [ ] ③的中率-1pt以内 [ ] ④上位日除外で維持 [ ] ⑤週末過半勝ち越し [ ]

結論: 差替 / シャドー継続（次回判定 __月__日）/ シャドー停止
理由:
実施内容:
切り戻し手順:
```

## 付録C. 参照

- 3か月見直しレポート: `99_その他/company-records/research/topics/2026-06-04-jra-keiba-3month-review.md`
- オッズ非依存＋配当均等の検証: `99_その他/company-records/research/topics/2026-06-06-jra-keiba-no-odds-investigation.md`
- 7月の作業履歴: `.company/secretary/handoff-log/2026-07.md`（`v2026_07_05_*` 〜 `v2026_07_12_jv_model`）
- 承認ルール: `02_設定/docs/approval-rules.md`
- 品質ループ: `02_設定/docs/quality-loop.md`
- Drive/git安全: `02_設定/docs/git-drive-safety.md`
