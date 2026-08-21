# ソフトウェア設計記述書（SDD）v1.0

| 項目 | 内容 |
|---|---|
| プロジェクト | MMAT（Multi-Market Auto Trading） |
| 版 | 1.0 |
| 作成日 | 2026-08-21 |
| 準拠 | IEEE 1016（設計記述）／C4モデル |
| 入力 | `docs/SRS.md` v1.0、`docs/BACKTEST_PROTOCOL.md`、`harness/failure_patterns.md` |

## 設計の中心にある考え方

旧システムの失敗を並べ直すと、**構造で防げたはずのものが3つ**ある。

1. 検証環境と実行環境が別コードで、ズレが検出されないまま実運用に入った（FP-012）
2. 発注経路にリスクの関門がなく、各所で個別に判断していた（FP-005）
3. エラーが上位に伝わらず、無言で失敗し続けた（FP-006）

本設計は、この3つを**規律ではなく構造**で塞ぐことを最優先にする。具体的には、
「バックテスト・ペーパー・実弾は同一のコードパスを通り、差し替わるのは Executor だけ」（ADR-012）、
「全ての注文は例外なく RiskGate を通る」（ADR-007）、「失敗は必ず戦略状態に記録され通知される」（ADR-013）。

---

## 1. 論理ビュー（コンポーネント構成）

### 1.1 コンポーネント一覧

| ID | コンポーネント | 責務 | 依存先 | 対応要件 |
|---|---|---|---|---|
| C-01 | DataIngestor | 提供元別アダプタでデータを取得し正規化する | 外部API | FR-DATA-001, 004, 007, 008, 010 |
| C-02 | DataQualityChecker | 品質チェック6項目と提供元間の差分実測 | C-01 | FR-DATA-002, 005 |
| C-03 | DataStore | 時系列（Parquet）と状態（SQLite）の永続化 | — | FR-DATA-003, FR-REC-001 |
| C-04 | StrategyEngine | 戦略プラグインを読み込みシグナルを算出する | C-03 | FR-SIG-001, 002 |
| C-05 | BacktestRunner | 分割・ウォークフォワード・DSR・コスト感度の実行 | C-03, C-04, C-08 | FR-BT-001〜009 |
| C-06 | RiskGate | 全注文の事前審査。上限違反を拒否する | C-03, C-09 | FR-RISK-001〜009 |
| C-07 | OrderRouter | 冪等キー付与、注文状態機械の管理、再送制御 | C-06, C-08, C-10 | FR-EXEC-004, 006, 007 |
| C-08 | ExecutionAdapter | 取引所ごとの発注・残高照会・約定取得を抽象化 | 外部API | FR-EXEC-001, 002, 003, 005, 008 |
| C-09 | PositionManager | 保有ポジションと損益・DDの算出 | C-03, C-10 | FR-RISK-004, 005 |
| C-10 | Ledger | 注文・約定の追記のみの記録 | C-03 | FR-REC-001〜005 |
| C-11 | Notifier | 通知の送信、失敗時の保持と再送 | 外部API | FR-MON-001〜004 |
| C-12 | Scheduler | 市場ごとの稼働カレンダーに従いタスクを起動する | 全体 | FR-MON-002 |
| C-13 | ConfigManager | 設定値の読み込みと起動時検証 | — | FR-RISK-009, FR-DATA-003 |
| C-14 | Reconciler | 起動時・定期に取引所の実状態と記録を照合する | C-08, C-09, C-10 | FR-EXEC-007、§10信頼性 |

### 1.2 依存関係

```
Scheduler ──> DataIngestor ──> DataQualityChecker ──> DataStore
                                                        │
                                                        v
                                                  StrategyEngine
                                                        │ signal
                                                        v
                                                    RiskGate ──(拒否)──> Notifier
                                                        │ 承認
                                                        v
                                                   OrderRouter
                                                        │
                                                        v
                                              ExecutionAdapter（差し替え点）
                                        ├── GmoSpotAdapter（暗号資産・実弾）
                                        ├── GmoFxAdapter（FX・実弾）
                                        ├── PaperAdapter（ペーパー・日本株もここ）
                                        └── BacktestAdapter（バックテスト）
                                                        │
                                                        v
                                              Ledger ──> PositionManager
                                                        │
                                                        v
                                                     Notifier

Reconciler ──> ExecutionAdapter / Ledger / PositionManager（起動時・定期）
ConfigManager ──> 全コンポーネント（起動時に検証、欠落なら起動中止）
```

**ExecutionAdapter が唯一の差し替え点である。** バックテスト・ペーパー・実弾で
上流（DataIngestor〜RiskGate〜OrderRouter）は同一のコードを通る。これがシグナル一致率98%
（FR-SIG-003）を規律ではなく構造で担保する。

### 1.3 主要インターフェース

```
DataIngestor.fetch(source, symbol, start, end) -> DataFrame | raise DataFetchError
DataQualityChecker.check(df, spec) -> QualityReport(passed: bool, items: list)
StrategyEngine.generate(strategy_id, as_of) -> list[Signal]
    Signal = {strategy_id, symbol, side, size_ratio, as_of, inputs: dict}
RiskGate.evaluate(signal, account_state) -> Decision
    Decision = {approved: bool, reason: str | None, adjusted_size: Decimal}
OrderRouter.submit(decision) -> OrderResult
    冪等キー = sha256(strategy_id + symbol + as_of(ISO8601) + side)
ExecutionAdapter.place(order) -> Fill | raise ExecutionError
ExecutionAdapter.fetch_balance(asset) -> Decimal        # FR-EXEC-001
ExecutionAdapter.quantize(symbol, qty) -> Decimal       # FR-EXEC-002 切り捨て
ExecutionAdapter.fetch_order(idempotency_key) -> OrderState
Ledger.append(record) -> None                           # 更新・削除は実装しない
Notifier.send(level, message) -> bool
```

**エラー時の振る舞い**: 各インターフェースは戻り値で失敗を表現せず、例外を送出する。
例外は必ず Scheduler のタスク境界で捕捉され、`strategy_state` への記録と Notifier への通知を伴う（ADR-013）。

---

## 2. プロセスビュー（フロー・並行性）

### 2.1 メインフロー（1サイクル）

1. Scheduler が市場の稼働カレンダーを参照し、対象市場のタスクを起動する
2. ConfigManager が設定値を検証する（欠落があれば起動中止・FR-RISK-009）
3. DataIngestor が最新データを取得する
4. DataQualityChecker が6項目を検査する。不合格なら当該市場のサイクルを中止し通知する
5. StrategyEngine が確定バーのみでシグナルを算出する（FR-SIG-001）
6. RiskGate が上限9項目を審査する。拒否ならその理由を通知し、発注しない
7. OrderRouter が冪等キーを付与し、ExecutionAdapter へ渡す
8. ExecutionAdapter が**実残高を照会してから**数量を確定し、発注する（FR-EXEC-001）
9. 約定結果を Ledger に追記し、PositionManager が損益とDDを更新する
10. 日次1回、Notifier が状態を送信する

### 2.2 並行性

| 処理 | 並行度 | 理由 |
|---|---|---|
| 市場ごとのサイクル | 逐次 | 資金は共有であり、RiskGate の判定に競合を持ち込まない |
| データ取得 | 提供元ごとに最大2並列 | レート制限（GMOコイン 20req/s）を下回るよう制御 |
| 発注 | 逐次 | 二重発注と残高の競合を防ぐ |
| バックテスト | 戦略ごとに並列可 | 状態を共有しないため |

**発注経路を逐次に固定するのは設計判断である。** 50万円規模では並行化の利益より、
競合による二重発注・残高不整合のリスクの方が大きい。

### 2.3 注文の状態機械

```
NEW ──submit──> SUBMITTED ──> FILLED
                    │            PARTIALLY_FILLED ──> (残数量を再評価)
                    │            REJECTED ──> 失敗回数++
                    │            CANCELED
                    └──応答なし──> UNKNOWN ──fetch_order──> 上記のいずれかへ確定
```

- **UNKNOWN の間、当該戦略の新規発注を停止する**（FR-EXEC-007）
- REJECTED が同一理由で3回連続した時点で戦略を停止する（FR-EXEC-006）
- 起動時に UNKNOWN の注文が残っていれば、Reconciler が照会して確定させてから通常動作に戻る

### 2.4 エラーハンドリングフロー

| 事象 | 動作 | リトライ |
|---|---|---|
| データ取得のタイムアウト | 当該市場のサイクル中止・通知 | 3回（指数バックオフ 2/4/8秒） |
| 発注のネットワークエラー | UNKNOWN へ遷移し照会 | 照会は5回まで |
| 発注の業務エラー（残高不足等） | 記録・通知、失敗回数++ | **リトライしない** |
| レート制限超過 | 待機して次サイクルへ | 同一サイクル内では再試行しない |
| 通知の送信失敗 | 内容を保持し次回にまとめて再送 | 次回サイクル |

**業務エラーをリトライしないのは FP-005 への直接の対策である。**
残高不足の決済注文を再送し続けたことが21日間のループを生んだ。

---

## 3. データビュー

### 3.1 保存方式

| 種別 | 方式 | 理由 |
|---|---|---|
| 時系列データ（OHLCV・資金調達率） | Parquet（銘柄・年ごとに分割） | 列指向で読み込みが速く、10年分でも扱える |
| 状態・記録（注文・約定・ポジション・損益） | SQLite（WALモード） | 単一ノードで十分。トランザクションが必要 |
| 設定 | YAML + `.env` | 設定は版管理し、秘密情報のみ `.env` |

**格納先は同期フォルダ配下を禁止する**（FR-DATA-003・FP-008）。起動時に ConfigManager が検査する。

### 3.1.1 スワップの二層構成（v1.2で追加）

FXのスワップは、**公正値と業者マージンを分離して保持する**。

| レイヤー | 提供元 | 期間 | 役割 |
|---|---|---|---|
| `fair_swap` | 東京金融取引所（TFX） | 2005年7月〜（21年） | 市場の公正なスワップ水準 |
| `broker_margin` | GMOコイン外国為替FX | 2023年4月〜 | 執行先が上乗せするマージン |

検証時のスワップ = `fair_swap` − `broker_margin`（マージンは片側22〜28円/万通貨/日、年率0.5〜0.7%で安定）。

**この分離が必要な理由**: 執行先の実績は3年分しかなく10年の検証要求を満たせない。一方TFXは21年分あるが
業者のマージンを含まない。両者を掛け合わせて初めて、規約上クリーンなまま長期のキャリー検証が成立する。

**最大のバグ源は付与日数である。** TFXのデータは付与日数の列を持たないため、週末・祝日をまたぐ日の
3日分付与などを自前で判定する必要がある。この判定は**単一の関数に集約し、検証と実行の両方から
同じ関数を呼ぶ**（FR-DATA-009）。ここが二重実装になると、バックテストと実運用で損益が静かにずれる。

**TFXは「予告なく変更・削除」と明記しているため、取得したデータはスナップショットとして保存する**
（FR-DATA-010）。保存しないと、提供元の更新で過去の検証結果が再現できなくなる。

### 3.2 データモデル（主要テーブル）

| テーブル | 主なカラム | 制約 |
|---|---|---|
| instruments | symbol(PK), market, tick_size, qty_step, min_qty | — |
| ohlcv | symbol, ts, o, h, l, c, v, source | PK(symbol, ts, source) |
| fair_swap | pair, ts, swap_buy, swap_sell, source | PK(pair, ts) |
| broker_margin | pair, ts, margin_buy, margin_sell | PK(pair, ts) |
| snapshots | source, period, file_path, fetched_at, hash | 取得時のまま保存し変更しない |
| signals | id(PK), strategy_id, symbol, ts, side, size_ratio, inputs(JSON) | — |
| orders | idempotency_key(PK), strategy_id, symbol, side, qty, price, state, submitted_at | **追記のみ**。状態遷移は order_events で表現 |
| order_events | id(PK), idempotency_key(FK), from_state, to_state, reason, ts | 追記のみ |
| fills | id(PK), idempotency_key(FK), qty, price, fee, filled_at | 追記のみ |
| positions | symbol(PK), qty, avg_price, opened_at, strategy_id | 決済時に削除 |
| pnl_daily | date, market, realized, unrealized, dd | PK(date, market) |
| strategy_state | strategy_id(PK), status, stop_reason, stopped_at, consecutive_failures | — |
| alerts | id(PK), level, message, sent, created_at | 追記のみ |
| backtest_runs | id(PK), strategy_id, is_range, oos_range, holdout_range, trials, holdout_accessed_at, metrics(JSON) | holdout_accessed_at は1回のみ書き込み可 |

### 3.3 ライフサイクル

| データ | 保持 |
|---|---|
| 時系列データ | 恒久（検証の再現性のため削除しない） |
| orders / order_events / fills | 恒久（帳簿保存・FR-REC-001） |
| pnl_daily | 恒久 |
| alerts | 恒久 |
| アプリケーションログ | 90日 |
| バックアップ | 日次。同期フォルダ配下に置かない |

---

## 4. 物理ビュー（デプロイ構成）

### 4.1 実行環境

| 項目 | 内容 |
|---|---|
| ホスト | ConoHa VPS 1台（Linux） |
| OS | Ubuntu LTS |
| ランタイム | Python 3.11+ |
| プロセス管理 | systemd（`mmat.service`） |
| 主要依存 | pandas, pyarrow, httpx, pydantic, APScheduler, pytest |

**Windows機は不要である。** 日本株の発注を行わない決定（D2）により、kabuステーションAPIの
常駐要件が消え、Linux 1台に集約できた。

### 4.2 ディレクトリ構成

```
mmat/
  src/mmat/
    ingest/        # C-01, C-02  提供元別アダプタ
    store/         # C-03
    strategies/    # C-04  戦略プラグイン（1戦略1ファイル）
    backtest/      # C-05
    risk/          # C-06
    execution/     # C-07, C-08  取引所別アダプタ
    portfolio/     # C-09, C-10
    notify/        # C-11
    scheduler/     # C-12
    config/        # C-13
    recon/         # C-14
  tests/{unit,integration,e2e}/
  config/          # YAML（版管理する）
  data/            # Parquet + SQLite（版管理しない・同期フォルダ禁止）
  scripts/
```

### 4.3 デプロイとロールバック

1. CI でテスト・lint・型検査を通す
2. wheel をビルドし、成果物としてVPSへ転送する
3. 直前の成果物を保持したまま新版を配置し、systemd を再起動する
4. ヘルスチェック（起動・設定検証・取引所への疎通）が失敗したら直前の成果物へ戻す

**VPSへソースを丸ごと置く方式は採らない**（FP-010：依存不足で起動不能になった）。

---

## 5. C4モデル

### 5.1 Container

| Container | 技術 | 責務 |
|---|---|---|
| MMAT Daemon | Python / systemd | スケジュール実行、シグナル生成、発注、監視 |
| Time-series Store | Parquet | 検証用データの保持 |
| State Store | SQLite | 注文・約定・ポジション・損益の記録 |
| Exchange APIs | GMOコイン（現物・FX） | 発注・残高照会・約定取得 |
| Data Sources | GMOコイン公開API（暗号資産） / HistData（FX価格） / TFX（FXスワップ公正値） | 検証用データの提供 |
| Notification | Telegram Bot API | 通知の送信 |

### 5.2 Component（MMAT Daemon の内部）

§1.1 のC-01〜C-14がそのまま Component にあたる。公開APIは §1.3 に定義した。

---

## 6. ADR（設計判断の記録）

### ADR-001: 実装言語に Python 3.11 を採用する
- **決定**: Python 3.11 以上を用いる
- **理由**: 時系列処理と数値計算の資産（pandas/pyarrow/numpy）が揃っており、旧システムもPythonで運用実績がある
- **代替案**: Rust（性能は上だが数値検証のエコシステムが薄く、開発速度が落ちる）／TypeScript（金融時系列のライブラリが弱い）
- **レベル**: L2-慎重
- **影響要件**: 全般

### ADR-002: 時系列は Parquet、状態は SQLite に分けて保存する
- **決定**: OHLCV等の時系列は Parquet、注文・ポジション等の状態は SQLite に置く
- **理由**: 10年分の時系列を SQLite に入れると読み込みが遅い。一方で注文管理にはトランザクションが要る。用途が異なるため分離する
- **代替案**: 全てSQLite（読み込みが遅い）／PostgreSQL（単一ノードには過剰で運用コストが増える）／DuckDB（有力だが、状態管理の実績はSQLiteが厚い）
- **レベル**: L3-柔軟
- **影響要件**: FR-DATA-003, FR-REC-001

### ADR-003: バックテストエンジンを自前で実装する
- **決定**: 薄いイベント駆動のバックテストエンジンを自作する
- **理由**: `BACKTEST_PROTOCOL.md` が要求する機能（HOLDOUTアクセスの1回制限、試行回数の記録、Deflated Sharpe、コスト3水準の同時出力、ギャップ時の始値約定）は、既存OSSの標準機能に揃っていない。外部フレームワークに合わせて制約を緩めるのは本末転倒である
- **代替案**: backtrader（メンテナンスが停滞）／vectorbt（高速だがベクトル化前提で先読みを作り込みやすい）／nautilus_trader（高機能だが学習コストと依存が重い）
- **リスクと対策**: 自作は先読みバイアスを作り込む危険がある。対策として、同一戦略をベクトル化実装でも計算し、両者の結果を突合する自己テストを置く（FR-BT-006）
- **レベル**: L2-慎重
- **影響要件**: FR-BT-001〜009

### ADR-004: 取引所ごとの差異を ExecutionAdapter に隔離する
- **決定**: 発注・残高照会・数量丸め・約定取得を ExecutionAdapter インターフェースに集約する
- **理由**: J-Quants の V1→V2 移行でクライアントが全損した（FP-009）。外部APIの変更はアダプタ内に閉じ込める
- **代替案**: 各所から直接API呼び出し（変更時の影響範囲が読めない）
- **レベル**: L1-不変
- **影響要件**: §10保守性・移植性

### ADR-005: 単一プロセスの常駐デーモンとし、発注経路を逐次にする
- **決定**: 市場ごとにプロセスを分けず、1デーモン内で逐次に処理する
- **理由**: 資金は市場をまたいで共有されるため、RiskGate の判定に競合を持ち込むと上限が守られない。50万円規模で並行化の利益は小さい
- **代替案**: 市場ごとにプロセス分離（障害は隔離できるが、資金上限の一貫性を保つ機構が別途必要になる）
- **レベル**: L2-慎重
- **影響要件**: FR-RISK-001〜003

### ADR-006: 冪等キーを決定論的に生成する
- **決定**: `sha256(strategy_id + symbol + as_of + side)` を冪等キーとし、取引所の client_order_id に渡す
- **理由**: 再起動やリトライで同じシグナルから同じキーが再生成され、取引所側で二重発注が弾かれる
- **代替案**: UUID（再起動後に同一性を判定できない）／DBのシーケンス（DB障害時に一意性が崩れる）
- **レベル**: L1-不変
- **影響要件**: FR-EXEC-004

### ADR-007: 全ての注文が RiskGate を通る経路を1本にする
- **決定**: ExecutionAdapter を呼び出せるのは OrderRouter のみとし、OrderRouter は RiskGate の承認なしに発注しない
- **理由**: 旧システムはリスク判断が各所に散っており、抜け道があった。関門を1つにすれば、抜け道は設計上作れない
- **代替案**: 各戦略が自分でリスクを判断する（実装者の規律に依存し、抜けが生じる）
- **レベル**: L1-不変
- **影響要件**: FR-RISK-001〜009

### ADR-008: 通知は Telegram を使う
- **決定**: 既存の Telegram Bot を流用する
- **理由**: shorts-factory で運用実績があり、追加コストがない
- **代替案**: メール（見落としやすい）／LINE（旧システムで使用したがAPI仕様の変更が多い）
- **レベル**: L3-柔軟
- **影響要件**: FR-MON-001〜004

### ADR-009: APIキーは出金権限なし・IP制限ありで発行する
- **決定**: 発注と照会の権限のみを持つキーを発行し、取引所側でVPSのIPに限定する
- **理由**: 鍵が漏れた場合の最大損害を、出金不能という形で構造的に制限する
- **代替案**: 全権限のキー（漏洩時に資金が流出する）
- **レベル**: L1-不変
- **影響要件**: SEC-02, SEC-03

### ADR-010: DRY_RUN を既定とし、実発注には二重の条件を課す
- **決定**: `DRY_RUN=true` を既定値とし、実発注は「設定で false」かつ「起動引数 `--live`」の両方が揃った場合のみ有効にする
- **理由**: 設定ファイルの取り違えだけで実弾が動く状態を作らない
- **代替案**: 設定値のみで切り替え（1箇所の誤りで実発注が起きる）
- **レベル**: L1-不変
- **影響要件**: §5 フェーズ計画（P5まで実弾禁止）

### ADR-011: 内部時刻を UTC に統一する
- **決定**: 保存・計算は全てUTC、通知の表示のみJSTへ変換する
- **理由**: 3市場は稼働時間が異なり、夏時間もある。内部で混在させるとバー確定の判定を誤る
- **代替案**: JST統一（海外市場のバー境界の扱いが煩雑になる）
- **レベル**: L1-不変
- **影響要件**: FR-SIG-001

### ADR-012: 検証・ペーパー・実弾を同一コードパスにする
- **決定**: ExecutionAdapter のみを差し替え、上流のデータ取得・シグナル生成・リスク審査は共通のコードを通す
- **理由**: 旧システムは検証と実行が別実装で、ズレが検出されなかった（FP-012）。同一コードなら、シグナル一致率98%（FR-SIG-003）は規律ではなく構造で保証される
- **代替案**: 検証用と実行用を分けて実装（最適化はしやすいが、ズレの検出が人手の照合に依存する）
- **レベル**: L1-不変
- **影響要件**: FR-SIG-003, FR-BT-007

### ADR-013: 例外はタスク境界で必ず捕捉し、記録と通知を伴わせる
- **決定**: Scheduler の各タスク境界で例外を捕捉し、`strategy_state` への記録と Notifier への通知を必ず行う
- **理由**: 旧システムはエラーがログに出るだけで、通知にも停止にも繋がらず21日間気づかれなかった（FP-006）
- **代替案**: ログ出力のみ（人が見に行かない限り気づけない）
- **レベル**: L1-不変
- **影響要件**: FR-MON-001, FR-EXEC-006

---

## 7. トレーサビリティ（要件 → コンポーネント → テスト）

| 要件 | コンポーネント | TC |
|---|---|---|
| FR-DATA-001, 004, 006 | C-01 | TC-D01, D04, D06 |
| FR-DATA-002, 005 | C-02 | TC-D02, D05 |
| FR-DATA-003 | C-03, C-13 | TC-D03 |
| FR-BT-001〜009 | C-05 | TC-B01〜B09 |
| FR-SIG-001, 002 | C-04 | TC-S01, S02 |
| FR-SIG-003 | C-04, C-05（ADR-012による構造的保証） | TC-S03 |
| FR-SIG-004 | C-08（PaperAdapter） | TC-S04 |
| FR-EXEC-001, 002, 003, 005, 008 | C-08 | TC-E01〜E03, E05, E08 |
| FR-EXEC-004, 006, 007 | C-07 | TC-E04, E06, E07 |
| FR-RISK-001〜003, 007, 008 | C-06 | TC-R01〜R03, R07, R08 |
| FR-RISK-004, 005 | C-06, C-09 | TC-R04, R05 |
| FR-RISK-006 | C-06, C-12 | TC-R06 |
| FR-RISK-009 | C-13 | TC-R09 |
| FR-MON-001〜004 | C-11 | TC-M01〜M04 |
| FR-REC-001〜005 | C-10 | TC-C01〜C05 |
| 信頼性（状態復元） | C-14 | TC-P04 |

**全てのMust要件がコンポーネントとテストに接続されている。未接続0件。**

---

## 8. 実装容易性への配慮

| 項目 | 方針 |
|---|---|
| 依存の最小化 | ネイティブ拡張が必要な重量級ライブラリを避ける。pandas / pyarrow / httpx / pydantic を基本とする |
| APIキーなしでのテスト | ExecutionAdapter のモック実装を用意し、**キーがなくても全テストが通る**状態にする |
| 戦略の追加 | 1戦略1ファイルのプラグイン形式。`generate(df, params) -> Signal` を実装するだけで追加できる |
| 設定の検証 | 起動時に pydantic で型と必須項目を検証し、欠落があれば起動しない |

---

## 9. 未解決事項が設計に与える影響

| # | 未解決 | 設計への影響 |
|---|---|---|
| U1 | ~~FXのスワップ実績データの入手可否~~ | **解決**。TFXを公正値レイヤーとして採用し、GMOコイン実績でマージンを校正する二層構成とした（§3.1.1）。対象戦略6件はすべて維持 |
| U2 | 野村AM CSV の自動取得の可否 | **不採用と判断**。C-01 の該当アダプタを実装せず、日本株のペーパー検証を保留する。実弾に影響しない |
| U3 | 執行先データでの検証完結の可否 | **暗号資産は完結できる**（GMOコイン日足2018年9月〜）。FR-DATA-005 の対象はFXのみとなり、暗号資産についてR2が消滅した。FXは価格の提供元が別のため差分実測を継続する |


---

## 10. 変更履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-08-21 | 1.0 | 初版。4ビュー・C4・ADR 13件 |
| 2026-08-21 | 1.1 | SRS v1.2 を反映。スワップの二層構成（§3.1.1）を追加し、暗号資産の検証データ提供元を執行先自身へ変更。これにより検証と実行のズレ（R2）が暗号資産については消滅した |
