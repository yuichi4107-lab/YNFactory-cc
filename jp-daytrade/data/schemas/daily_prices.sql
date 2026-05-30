-- 日足価格テーブル
-- J-Quants /prices/daily_quotes から取得した日足データを格納する
CREATE TABLE IF NOT EXISTS daily_prices (
    id                INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    code              TEXT    NOT NULL,   -- 銘柄コード（例: "7203"）
    date              TEXT    NOT NULL,   -- 日付 (YYYY-MM-DD)
    open              REAL,               -- 始値
    high              REAL,               -- 高値
    low               REAL,               -- 安値
    close             REAL,               -- 終値
    volume            REAL,               -- 出来高（株）
    turnover          REAL,               -- 売買代金（円）
    adjustment_factor REAL    NOT NULL DEFAULT 1.0  -- 株式分割等の調整係数
);

-- インデックス
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_prices_code_date ON daily_prices(code, date);
CREATE        INDEX IF NOT EXISTS idx_daily_prices_date       ON daily_prices(date);
