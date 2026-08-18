# -*- coding: utf-8 -*-
"""データアクセス層。金額・期間の計算ルールは domain へ委譲する。"""
from __future__ import annotations

from . import domain

# 受注額・発注額・納品日・先頭明細を案件単位で持つ共通SELECT
ORDER_BASE_SQL = """
SELECT so.id, so.order_no, so.order_date, so.customer_due_date, so.customer_id,
       so.customer_contact, so.customer_order_no, so.status,
       c.name AS customer_name, c.honorific, c.closing_day,
       c.postal_code AS customer_postal_code, c.address AS customer_address,
       (SELECT COALESCE(SUM(l.quantity * l.unit_price), 0)
          FROM sales_order_lines l WHERE l.sales_order_id = so.id) AS order_amount,
       (SELECT COALESCE(SUM(p.quantity * p.unit_price), 0)
          FROM purchase_orders p WHERE p.sales_order_id = so.id) AS purchase_amount,
       (SELECT d.delivery_date FROM deliveries d WHERE d.sales_order_id = so.id) AS delivery_date,
       (SELECT l.product_name FROM sales_order_lines l
         WHERE l.sales_order_id = so.id ORDER BY l.line_no LIMIT 1) AS product_name,
       (SELECT l.model_no FROM sales_order_lines l
         WHERE l.sales_order_id = so.id ORDER BY l.line_no LIMIT 1) AS model_no,
       (SELECT l.quantity FROM sales_order_lines l
         WHERE l.sales_order_id = so.id ORDER BY l.line_no LIMIT 1) AS quantity,
       (SELECT l.unit FROM sales_order_lines l
         WHERE l.sales_order_id = so.id ORDER BY l.line_no LIMIT 1) AS unit,
       (SELECT COUNT(*) FROM sales_order_lines l WHERE l.sales_order_id = so.id) AS line_count
  FROM sales_orders so
  JOIN customers c ON c.id = so.customer_id
"""


# ------------------------------------------------------------------ マスタ
def list_customers(conn, active_only=True):
    sql = "SELECT * FROM customers"
    if active_only:
        sql += " WHERE is_active = 1"
    return conn.execute(sql + " ORDER BY name").fetchall()


def get_customer(conn, customer_id):
    return conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()


CUSTOMER_FIELDS = ("name", "honorific", "postal_code", "address", "phone",
                   "default_contact", "closing_day", "note")


def save_customer(conn, data, customer_id=None):
    values = [data.get(f) for f in CUSTOMER_FIELDS]
    if customer_id:
        assigns = ", ".join(f + " = ?" for f in CUSTOMER_FIELDS)
        conn.execute("UPDATE customers SET " + assigns +
                     ", updated_at = datetime('now','localtime') WHERE id = ?",
                     values + [customer_id])
        return customer_id
    cols = ", ".join(CUSTOMER_FIELDS)
    marks = ", ".join("?" * len(CUSTOMER_FIELDS))
    return conn.execute("INSERT INTO customers (" + cols + ") VALUES (" + marks + ")",
                        values).lastrowid


def deactivate_customer(conn, customer_id):
    conn.execute("UPDATE customers SET is_active = 0,"
                 " updated_at = datetime('now','localtime') WHERE id = ?", (customer_id,))


def list_suppliers(conn, active_only=True):
    sql = "SELECT * FROM suppliers"
    if active_only:
        sql += " WHERE is_active = 1"
    return conn.execute(sql + " ORDER BY name").fetchall()


SUPPLIER_FIELDS = ("name", "postal_code", "address", "phone", "note")


def save_supplier(conn, data, supplier_id=None):
    values = [data.get(f) for f in SUPPLIER_FIELDS]
    if supplier_id:
        assigns = ", ".join(f + " = ?" for f in SUPPLIER_FIELDS)
        conn.execute("UPDATE suppliers SET " + assigns +
                     ", updated_at = datetime('now','localtime') WHERE id = ?",
                     values + [supplier_id])
        return supplier_id
    cols = ", ".join(SUPPLIER_FIELDS)
    marks = ", ".join("?" * len(SUPPLIER_FIELDS))
    return conn.execute("INSERT INTO suppliers (" + cols + ") VALUES (" + marks + ")",
                        values).lastrowid


def deactivate_supplier(conn, supplier_id):
    conn.execute("UPDATE suppliers SET is_active = 0,"
                 " updated_at = datetime('now','localtime') WHERE id = ?", (supplier_id,))


COMPANY_FIELDS = ("company_name", "postal_code", "address", "phone",
                  "invoice_reg_no", "bank_info", "tax_rate")


def get_company(conn):
    return conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone()


def save_company(conn, data):
    assigns = ", ".join(f + " = ?" for f in COMPANY_FIELDS)
    conn.execute("UPDATE company_settings SET " + assigns +
                 ", updated_at = datetime('now','localtime') WHERE id = 1",
                 [data.get(f) for f in COMPANY_FIELDS])


# ------------------------------------------------------------------ 受注
def take_next_order_no(conn) -> int:
    """管理No. を採番する。transaction() の内側で呼ぶこと（DB設計書 3.1）。"""
    row = conn.execute("SELECT next_order_no FROM company_settings WHERE id = 1").fetchone()
    order_no = int(row["next_order_no"])
    conn.execute("UPDATE company_settings SET next_order_no = ?,"
                 " updated_at = datetime('now','localtime') WHERE id = 1", (order_no + 1,))
    return order_no


def create_order(conn, header, line) -> int:
    """案件ヘッダ + 受注明細1行を登録し、sales_orders.id を返す。"""
    order_no = take_next_order_no(conn)
    order_id = conn.execute(
        "INSERT INTO sales_orders (order_no, order_date, customer_due_date, customer_id,"
        " customer_contact, customer_order_no) VALUES (?,?,?,?,?,?)",
        (order_no, header["order_date"], header["customer_due_date"], header["customer_id"],
         header.get("customer_contact"), header.get("customer_order_no"))).lastrowid
    conn.execute(
        "INSERT INTO sales_order_lines (sales_order_id, line_no, product_name, model_no,"
        " quantity, unit, unit_price, note) VALUES (?,1,?,?,?,?,?,?)",
        (order_id, line["product_name"], line.get("model_no"), line["quantity"],
         line.get("unit") or "ヶ", line["unit_price"], line.get("note")))
    return order_id


def update_order(conn, order_id, header, line) -> None:
    conn.execute(
        "UPDATE sales_orders SET order_date = ?, customer_due_date = ?, customer_id = ?,"
        " customer_contact = ?, customer_order_no = ?,"
        " updated_at = datetime('now','localtime') WHERE id = ?",
        (header["order_date"], header["customer_due_date"], header["customer_id"],
         header.get("customer_contact"), header.get("customer_order_no"), order_id))
    conn.execute(
        "UPDATE sales_order_lines SET product_name = ?, model_no = ?, quantity = ?, unit = ?,"
        " unit_price = ?, note = ?, updated_at = datetime('now','localtime')"
        " WHERE sales_order_id = ? AND line_no = 1",
        (line["product_name"], line.get("model_no"), line["quantity"],
         line.get("unit") or "ヶ", line["unit_price"], line.get("note"), order_id))


def get_order(conn, order_id):
    return conn.execute(ORDER_BASE_SQL + " WHERE so.id = ?", (order_id,)).fetchone()


def get_order_by_no(conn, order_no):
    return conn.execute(ORDER_BASE_SQL + " WHERE so.order_no = ?", (order_no,)).fetchone()


def get_order_lines(conn, order_id):
    return conn.execute("SELECT * FROM sales_order_lines WHERE sales_order_id = ?"
                        " ORDER BY line_no", (order_id,)).fetchall()


def set_status(conn, order_id, status):
    conn.execute("UPDATE sales_orders SET status = ?,"
                 " updated_at = datetime('now','localtime') WHERE id = ?", (status, order_id))


def search_orders(conn, f):
    """一覧の絞り込み。f: date_field/date_from/date_to/customer_id/supplier_id/status/keyword"""
    where, params = ["1=1"], []
    if f.get("date_field", "order_date") == "order_date":
        date_field = "so.order_date"
    else:
        date_field = "(SELECT d.delivery_date FROM deliveries d WHERE d.sales_order_id = so.id)"
    if f.get("date_from"):
        where.append(date_field + " >= ?")
        params.append(f["date_from"])
    if f.get("date_to"):
        where.append(date_field + " <= ?")
        params.append(f["date_to"])
    if f.get("customer_id"):
        where.append("so.customer_id = ?")
        params.append(f["customer_id"])
    if f.get("supplier_id"):
        where.append("EXISTS (SELECT 1 FROM purchase_orders p"
                     " WHERE p.sales_order_id = so.id AND p.supplier_id = ?)")
        params.append(f["supplier_id"])
    if f.get("status"):
        where.append("so.status = ?")
        params.append(f["status"])
    if f.get("keyword"):
        where.append("EXISTS (SELECT 1 FROM sales_order_lines l WHERE l.sales_order_id = so.id"
                     " AND (l.product_name LIKE ? OR IFNULL(l.model_no,'') LIKE ?))")
        kw = "%" + f["keyword"] + "%"
        params += [kw, kw]
    sort = {"order_no": "so.order_no", "order_date": "so.order_date",
            "customer": "c.name", "due": "so.customer_due_date"}.get(f.get("sort"), "so.order_no")
    direction = "ASC" if f.get("dir") == "asc" else "DESC"
    sql = ORDER_BASE_SQL + " WHERE " + " AND ".join(where) + " ORDER BY " + sort + " " + direction
    return conn.execute(sql, params).fetchall()


def summarize(rows):
    """期間合計。取消案件は集計に含めない。"""
    live = [r for r in rows if r["status"] != "cancelled"]
    order_amount = sum(r["order_amount"] for r in live)
    purchase_amount = sum(r["purchase_amount"] for r in live)
    return {"count": len(live), "order_amount": order_amount,
            "purchase_amount": purchase_amount, "profit": order_amount - purchase_amount}


def summarize_by_customer(rows):
    """客先別集計（客先・件数・受注額・発注額・粗利）。"""
    acc = {}
    for r in rows:
        if r["status"] == "cancelled":
            continue
        item = acc.setdefault(r["customer_id"], {
            "customer_id": r["customer_id"], "customer_name": r["customer_name"],
            "count": 0, "order_amount": 0, "purchase_amount": 0, "profit": 0})
        item["count"] += 1
        item["order_amount"] += r["order_amount"]
        item["purchase_amount"] += r["purchase_amount"]
        item["profit"] = item["order_amount"] - item["purchase_amount"]
    return sorted(acc.values(), key=lambda x: -x["order_amount"])


# ------------------------------------------------------------------ 発注
def list_purchase_orders(conn, order_id):
    return conn.execute(
        "SELECT p.*, s.name AS supplier_name FROM purchase_orders p"
        " JOIN suppliers s ON s.id = p.supplier_id"
        " WHERE p.sales_order_id = ? ORDER BY p.id", (order_id,)).fetchall()


def add_purchase_order(conn, order_id, data):
    line = conn.execute("SELECT id FROM sales_order_lines WHERE sales_order_id = ?"
                        " ORDER BY line_no LIMIT 1", (order_id,)).fetchone()
    conn.execute(
        "INSERT INTO purchase_orders (sales_order_id, sales_order_line_id, supplier_id,"
        " po_date, supplier_due_date, product_name, model_no, quantity, unit, unit_price, note)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (order_id, line["id"] if line else None, data["supplier_id"], data["po_date"],
         data["supplier_due_date"], data["product_name"], data.get("model_no"),
         data["quantity"], data.get("unit") or "ヶ", data["unit_price"], data.get("note")))


def update_purchase_order(conn, po_id, data):
    conn.execute(
        "UPDATE purchase_orders SET supplier_id = ?, po_date = ?, supplier_due_date = ?,"
        " product_name = ?, model_no = ?, quantity = ?, unit = ?, unit_price = ?, note = ?,"
        " updated_at = datetime('now','localtime') WHERE id = ?",
        (data["supplier_id"], data["po_date"], data["supplier_due_date"], data["product_name"],
         data.get("model_no"), data["quantity"], data.get("unit") or "ヶ",
         data["unit_price"], data.get("note"), po_id))


def delete_purchase_order(conn, po_id):
    conn.execute("DELETE FROM purchase_orders WHERE id = ?", (po_id,))


# ------------------------------------------------------------------ 納品
def save_delivery(conn, order_id, delivery_date):
    conn.execute(
        "INSERT INTO deliveries (sales_order_id, delivery_date) VALUES (?,?)"
        " ON CONFLICT(sales_order_id) DO UPDATE SET delivery_date = excluded.delivery_date,"
        " updated_at = datetime('now','localtime')", (order_id, delivery_date))


def delivery_note_orders(conn, customer_id, order_ids=None, date_from=None, date_to=None):
    """納品書に載せる案件（納品日が入力済みの案件）。

    order_ids 指定でその案件のみ（案件単位発行）。date_from/date_to 指定で納品日を期間で絞る
    （一覧の客先別集計から発行するときに、表示中の期間と一致させるため）。
    """
    sql = ORDER_BASE_SQL + (" WHERE so.customer_id = ? AND so.status <> 'cancelled'"
                            " AND EXISTS (SELECT 1 FROM deliveries d"
                            " WHERE d.sales_order_id = so.id)")
    params = [customer_id]
    if order_ids:
        sql += " AND so.id IN (" + ",".join("?" * len(order_ids)) + ")"
        params += list(order_ids)
    else:
        if date_from:
            sql += (" AND (SELECT d.delivery_date FROM deliveries d"
                    " WHERE d.sales_order_id = so.id) >= ?")
            params.append(date_from)
        if date_to:
            sql += (" AND (SELECT d.delivery_date FROM deliveries d"
                    " WHERE d.sales_order_id = so.id) <= ?")
            params.append(date_to)
    return conn.execute(sql + " ORDER BY so.order_no", params).fetchall()


# ------------------------------------------------------------------ 請求
def billable_lines(conn, customer_id, period_start, period_end):
    """請求期間内に納品済みかつ未請求の受注明細（画面設計書 4.4 の抽出条件）。"""
    return conn.execute(
        """
        SELECT l.id AS line_id, l.product_name, l.model_no, l.quantity, l.unit,
               l.unit_price, l.note, l.quantity * l.unit_price AS amount,
               so.id AS order_id, so.order_no, so.order_date, d.delivery_date
          FROM sales_order_lines l
          JOIN sales_orders so ON so.id = l.sales_order_id
          JOIN deliveries d    ON d.sales_order_id = so.id
         WHERE so.customer_id = ?
           AND so.status NOT IN ('cancelled', 'invoiced', 'paid')
           AND d.delivery_date BETWEEN ? AND ?
           AND NOT EXISTS (
                 SELECT 1 FROM invoice_lines il JOIN invoices i ON i.id = il.invoice_id
                  WHERE il.sales_order_line_id = l.id AND i.status <> 'cancelled')
         ORDER BY so.order_no, l.line_no
        """, (customer_id, period_start, period_end)).fetchall()


def create_invoice(conn, customer_id, period_start, period_end, issue_date, lines, tax_rate=10):
    """請求を確定する。lines は billable_lines() の行（画面で選択されたもの）。"""
    subtotal = sum(l["amount"] for l in lines)
    subtotal, tax, total = domain.calc_totals(subtotal, tax_rate)
    existing = [r["invoice_no"] for r in conn.execute("SELECT invoice_no FROM invoices")]
    invoice_no = domain.next_invoice_no(domain.parse_date(period_end), existing)
    invoice_id = conn.execute(
        "INSERT INTO invoices (invoice_no, customer_id, period_start, period_end, issue_date,"
        " subtotal, tax, total) VALUES (?,?,?,?,?,?,?,?)",
        (invoice_no, customer_id, period_start, period_end, issue_date,
         subtotal, tax, total)).lastrowid
    for l in lines:
        conn.execute("INSERT INTO invoice_lines (invoice_id, sales_order_line_id, amount)"
                     " VALUES (?,?,?)", (invoice_id, l["line_id"], l["amount"]))
        set_status(conn, l["order_id"], "invoiced")
    return invoice_id


def list_invoices(conn):
    return conn.execute("SELECT i.*, c.name AS customer_name FROM invoices i"
                        " JOIN customers c ON c.id = i.customer_id"
                        " ORDER BY i.id DESC").fetchall()


def get_invoice(conn, invoice_id):
    return conn.execute(
        "SELECT i.*, c.name AS customer_name, c.honorific, c.postal_code, c.address"
        " FROM invoices i JOIN customers c ON c.id = i.customer_id WHERE i.id = ?",
        (invoice_id,)).fetchone()


def get_invoice_lines(conn, invoice_id):
    return conn.execute(
        """
        SELECT il.amount, l.product_name, l.model_no, l.quantity, l.unit, l.unit_price, l.note,
               so.order_no, so.order_date, d.delivery_date
          FROM invoice_lines il
          JOIN sales_order_lines l ON l.id = il.sales_order_line_id
          JOIN sales_orders so     ON so.id = l.sales_order_id
     LEFT JOIN deliveries d        ON d.sales_order_id = so.id
         WHERE il.invoice_id = ? ORDER BY so.order_no, l.line_no
        """, (invoice_id,)).fetchall()


def mark_invoice_paid(conn, invoice_id):
    conn.execute("UPDATE invoices SET status = 'paid',"
                 " updated_at = datetime('now','localtime') WHERE id = ?", (invoice_id,))
    for row in conn.execute(
            "SELECT DISTINCT l.sales_order_id AS oid FROM invoice_lines il"
            " JOIN sales_order_lines l ON l.id = il.sales_order_line_id"
            " WHERE il.invoice_id = ?", (invoice_id,)).fetchall():
        set_status(conn, row["oid"], "paid")


def cancel_invoice(conn, invoice_id):
    """請求取消。対象案件を納品済へ戻し、再請求できるようにする（DB設計書 3.5）。"""
    conn.execute("UPDATE invoices SET status = 'cancelled',"
                 " updated_at = datetime('now','localtime') WHERE id = ?", (invoice_id,))
    for row in conn.execute(
            "SELECT DISTINCT l.sales_order_id AS oid FROM invoice_lines il"
            " JOIN sales_order_lines l ON l.id = il.sales_order_line_id"
            " WHERE il.invoice_id = ?", (invoice_id,)).fetchall():
        set_status(conn, row["oid"], "delivered")
