-- リアルタイム気配スナップショットテーブル
-- kabu PUSH API から取得した寄り前気配データを格納する
CREATE TABLE IF NOT EXISTS quotes_snapshot (
    id               INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    symbol           TEXT    NOT NULL,   -- 銘柄コード（例: "7203"）
    timestamp        TEXT    NOT NULL,   -- 取得日時 (ISO 8601, JST)
    ask_sign         TEXT,               -- 売り気配フラグ（例: "0101"=通常, "0103"=特別）
    bid_sign         TEXT,               -- 買い気配フラグ
    current_price    REAL,               -- 現在値（または最終約定価格）
    calc_price       REAL,               -- 想定約定価格（CalcPrice）
    over_sell        REAL,               -- 板外売り合計（OverSellQty）
    under_buy        REAL,               -- 板外買い合計（UnderBuyQty）
    sell_levels_json TEXT,               -- 売り板10本 JSON（[{"price": X, "qty": Y, "sign": Z}]）
    buy_levels_json  TEXT                -- 買い板10本 JSON
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_quotes_symbol_ts ON quotes_snapshot(symbol, timestamp);
