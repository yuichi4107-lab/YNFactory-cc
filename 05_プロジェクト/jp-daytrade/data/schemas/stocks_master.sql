-- 銘柄マスターテーブル
-- J-Quants /listed/info から取得した銘柄情報を格納する
CREATE TABLE IF NOT EXISTS stocks_master (
    code             TEXT    NOT NULL PRIMARY KEY,  -- 銘柄コード（例: "7203"）
    name             TEXT    NOT NULL,              -- 銘柄名
    market           TEXT    NOT NULL,              -- 市場区分（例: "グロース", "プライム"）
    market_cap       REAL,                          -- 時価総額（円）
    last_price       REAL,                          -- 直近株価（円）
    unit_shares      INTEGER NOT NULL DEFAULT 100,  -- 単元株数
    is_value_stock   INTEGER NOT NULL               -- 値嵩フラグ: 1=値嵩（除外対象）, 0=対象
                         AS (
                             CASE WHEN last_price > 3000
                                    OR (last_price * unit_shares) > 300000
                                  THEN 1
                                  ELSE 0
                             END
                         ) STORED,
    updated_at       TEXT    NOT NULL               -- 最終更新日時 (ISO 8601)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_stocks_master_market       ON stocks_master(market);
CREATE INDEX IF NOT EXISTS idx_stocks_master_market_cap   ON stocks_master(market_cap);
CREATE INDEX IF NOT EXISTS idx_stocks_master_is_value     ON stocks_master(is_value_stock);
