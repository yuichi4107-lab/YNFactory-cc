-- 販売管理システム スキーマ（DB設計書 v1.2 準拠）
-- 初期版で作成するテーブルのみ。attachments / users はオプション機能のため作成しない。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    honorific       TEXT    DEFAULT '御中',
    postal_code     TEXT,
    address         TEXT,
    phone           TEXT,
    default_contact TEXT,
    closing_day     INTEGER NOT NULL DEFAULT 99
                    CHECK (closing_day BETWEEN 1 AND 31 OR closing_day = 99),
    note            TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS suppliers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    postal_code TEXT,
    address     TEXT,
    phone       TEXT,
    note        TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS sales_orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no          INTEGER NOT NULL UNIQUE,
    order_date        DATE    NOT NULL,
    customer_due_date DATE    NOT NULL,
    customer_id       INTEGER NOT NULL REFERENCES customers(id),
    customer_contact  TEXT,
    customer_order_no TEXT,
    status            TEXT    NOT NULL DEFAULT 'ordered'
                      CHECK (status IN ('ordered','po_issued','delivered','invoiced','paid','cancelled')),
    created_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_so_order_no    ON sales_orders(order_no);
CREATE INDEX IF NOT EXISTS idx_so_customer_id ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_so_order_date  ON sales_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_so_status      ON sales_orders(status);

CREATE TABLE IF NOT EXISTS sales_order_lines (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    line_no        INTEGER NOT NULL DEFAULT 1,
    product_name   TEXT    NOT NULL,
    model_no       TEXT,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit           TEXT    DEFAULT 'ヶ',
    unit_price     INTEGER NOT NULL CHECK (unit_price >= 0),
    note           TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (sales_order_id, line_no)
);
CREATE INDEX IF NOT EXISTS idx_sol_sales_order_id ON sales_order_lines(sales_order_id);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id      INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    sales_order_line_id INTEGER REFERENCES sales_order_lines(id),
    supplier_id         INTEGER NOT NULL REFERENCES suppliers(id),
    po_date             DATE    NOT NULL,
    supplier_due_date   DATE    NOT NULL,
    product_name        TEXT    NOT NULL,
    model_no            TEXT,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    unit                TEXT    DEFAULT 'ヶ',
    unit_price          INTEGER NOT NULL CHECK (unit_price >= 0),
    note                TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_po_sales_order_id ON purchase_orders(sales_order_id);
CREATE INDEX IF NOT EXISTS idx_po_supplier_id    ON purchase_orders(supplier_id);

CREATE TABLE IF NOT EXISTS deliveries (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL UNIQUE REFERENCES sales_orders(id) ON DELETE CASCADE,
    delivery_date  DATE    NOT NULL,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no   TEXT    NOT NULL UNIQUE,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    period_start DATE    NOT NULL,
    period_end   DATE    NOT NULL,
    issue_date   DATE    NOT NULL,
    subtotal     INTEGER NOT NULL,
    tax          INTEGER NOT NULL,
    total        INTEGER NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'issued'
                 CHECK (status IN ('issued','paid','cancelled')),
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (period_start <= period_end)
);
CREATE INDEX IF NOT EXISTS idx_inv_customer_id ON invoices(customer_id);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id          INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    sales_order_line_id INTEGER NOT NULL REFERENCES sales_order_lines(id),
    amount              INTEGER NOT NULL,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_il_invoice_id ON invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_il_line_id    ON invoice_lines(sales_order_line_id);

CREATE TABLE IF NOT EXISTS company_settings (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    company_name   TEXT    NOT NULL DEFAULT '',
    postal_code    TEXT,
    address        TEXT,
    phone          TEXT,
    invoice_reg_no TEXT,
    bank_info      TEXT,
    tax_rate       INTEGER NOT NULL DEFAULT 10,
    next_order_no  INTEGER NOT NULL DEFAULT 10100,
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT OR IGNORE INTO company_settings (id) VALUES (1);
