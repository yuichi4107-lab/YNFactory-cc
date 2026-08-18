# -*- coding: utf-8 -*-
"""受注〜発注〜納品〜請求のデータ操作テスト。"""
import sqlite3

import pytest

from app import db as db_module
from app import repo


def make_order(conn, customer_id, order_no_date="2026-07-10", due="2026-07-31",
               product="シャフト", qty=2, price=10000):
    with db_module.transaction(conn):
        return repo.create_order(
            conn,
            {"order_date": order_no_date, "customer_due_date": due, "customer_id": customer_id,
             "customer_contact": "山田", "customer_order_no": "PO-1"},
            {"product_name": product, "model_no": "A0010", "quantity": qty,
             "unit": "ヶ", "unit_price": price, "note": "表面処理注意"})


def add_po(conn, order_id, supplier_id, qty=2, price=8000):
    with db_module.transaction(conn):
        repo.add_purchase_order(conn, order_id, {
            "supplier_id": supplier_id, "po_date": "2026-07-11",
            "supplier_due_date": "2026-07-29", "product_name": "シャフト", "model_no": "A0010",
            "quantity": qty, "unit": "ヶ", "unit_price": price, "note": ""})


def test_order_no_starts_at_10100_and_increments(conn, masters):
    first = repo.get_order(conn, make_order(conn, masters["customer_id"]))
    second = repo.get_order(conn, make_order(conn, masters["customer_id"]))
    assert first["order_no"] == 10100
    assert second["order_no"] == 10101


def test_order_no_is_not_reused_after_cancel(conn, masters):
    order_id = make_order(conn, masters["customer_id"])
    with db_module.transaction(conn):
        repo.set_status(conn, order_id, "cancelled")
    assert repo.get_order(conn, make_order(conn, masters["customer_id"]))["order_no"] == 10101


def test_amounts_and_profit(conn, masters):
    order_id = make_order(conn, masters["customer_id"])          # 2 × 10,000 = 20,000
    add_po(conn, order_id, masters["supplier_id"])               # 2 ×  8,000 = 16,000
    order = repo.get_order(conn, order_id)
    assert order["order_amount"] == 20000
    assert order["purchase_amount"] == 16000
    assert order["order_amount"] - order["purchase_amount"] == 4000


def test_purchase_order_inherits_sales_order_line(conn, masters):
    order_id = make_order(conn, masters["customer_id"])
    add_po(conn, order_id, masters["supplier_id"])
    line_id = repo.get_order_lines(conn, order_id)[0]["id"]
    assert repo.list_purchase_orders(conn, order_id)[0]["sales_order_line_id"] == line_id


def test_invoice_flow_marks_orders_invoiced_and_prevents_double_billing(conn, masters):
    cid = masters["customer_id"]
    order_id = make_order(conn, cid)
    with db_module.transaction(conn):
        repo.save_delivery(conn, order_id, "2026-07-29")
        repo.set_status(conn, order_id, "delivered")

    lines = repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")
    assert len(lines) == 1 and lines[0]["amount"] == 20000

    with db_module.transaction(conn):
        invoice_id = repo.create_invoice(conn, cid, "2026-07-01", "2026-07-31",
                                         "2026-07-31", lines)
    invoice = repo.get_invoice(conn, invoice_id)
    assert (invoice["subtotal"], invoice["tax"], invoice["total"]) == (20000, 2000, 22000)
    assert invoice["invoice_no"] == "INV-202607-001"
    assert repo.get_order(conn, order_id)["status"] == "invoiced"
    # 二重請求されない
    assert repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31") == []


def test_cancel_invoice_returns_order_to_delivered_and_allows_rebilling(conn, masters):
    cid = masters["customer_id"]
    order_id = make_order(conn, cid)
    with db_module.transaction(conn):
        repo.save_delivery(conn, order_id, "2026-07-29")
        repo.set_status(conn, order_id, "delivered")
    lines = repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")
    with db_module.transaction(conn):
        invoice_id = repo.create_invoice(conn, cid, "2026-07-01", "2026-07-31", "2026-07-31", lines)
    with db_module.transaction(conn):
        repo.cancel_invoice(conn, invoice_id)
    assert repo.get_order(conn, order_id)["status"] == "delivered"
    assert len(repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")) == 1


def test_mark_paid_updates_orders(conn, masters):
    cid = masters["customer_id"]
    order_id = make_order(conn, cid)
    with db_module.transaction(conn):
        repo.save_delivery(conn, order_id, "2026-07-29")
        repo.set_status(conn, order_id, "delivered")
    lines = repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")
    with db_module.transaction(conn):
        invoice_id = repo.create_invoice(conn, cid, "2026-07-01", "2026-07-31", "2026-07-31", lines)
    with db_module.transaction(conn):
        repo.mark_invoice_paid(conn, invoice_id)
    assert repo.get_order(conn, order_id)["status"] == "paid"
    assert repo.get_invoice(conn, invoice_id)["status"] == "paid"


def test_billable_lines_respects_period_and_delivery(conn, masters):
    cid = masters["customer_id"]
    delivered_in = make_order(conn, cid)
    delivered_out = make_order(conn, cid)
    not_delivered = make_order(conn, cid)
    with db_module.transaction(conn):
        repo.save_delivery(conn, delivered_in, "2026-07-29")
        repo.set_status(conn, delivered_in, "delivered")
        repo.save_delivery(conn, delivered_out, "2026-08-03")
        repo.set_status(conn, delivered_out, "delivered")
    lines = repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")
    order_ids = {l["order_id"] for l in lines}
    assert order_ids == {delivered_in}
    assert not_delivered not in order_ids


def test_delivery_is_unique_per_order(conn, masters):
    order_id = make_order(conn, masters["customer_id"])
    with db_module.transaction(conn):
        repo.save_delivery(conn, order_id, "2026-07-29")
        repo.save_delivery(conn, order_id, "2026-07-30")   # 上書き（1受注=1納品）
    assert repo.get_order(conn, order_id)["delivery_date"] == "2026-07-30"


def test_summaries_exclude_cancelled(conn, masters):
    cid = masters["customer_id"]
    kept = make_order(conn, cid)
    dropped = make_order(conn, cid)
    add_po(conn, kept, masters["supplier_id"])
    with db_module.transaction(conn):
        repo.set_status(conn, dropped, "cancelled")
    rows = repo.search_orders(conn, {"date_from": "2026-07-01", "date_to": "2026-07-31"})
    total = repo.summarize(rows)
    assert total["count"] == 1 and total["order_amount"] == 20000 and total["profit"] == 4000
    by_customer = repo.summarize_by_customer(rows)
    assert len(by_customer) == 1 and by_customer[0]["count"] == 1


def test_search_filters(conn, masters):
    cid, cid2 = masters["customer_id"], masters["customer2_id"]
    a = make_order(conn, cid, product="シャフト")
    make_order(conn, cid2, product="ブラケット")
    add_po(conn, a, masters["supplier_id"])
    base = {"date_from": "2026-07-01", "date_to": "2026-07-31"}
    assert len(repo.search_orders(conn, base)) == 2
    assert len(repo.search_orders(conn, dict(base, customer_id=cid))) == 1
    assert len(repo.search_orders(conn, dict(base, keyword="ブラケ"))) == 1
    assert len(repo.search_orders(conn, dict(base, supplier_id=masters["supplier_id"]))) == 1
    assert len(repo.search_orders(conn, dict(base, status="ordered"))) == 2
    # 期間外は出ない
    assert repo.search_orders(conn, {"date_from": "2026-08-01", "date_to": "2026-08-31"}) == []


def test_quantity_must_be_positive(conn, masters):
    with pytest.raises(sqlite3.IntegrityError):
        make_order(conn, masters["customer_id"], qty=0)


def test_backup_creates_readable_copy(conn, masters, tmp_path):
    make_order(conn, masters["customer_id"])
    dest = db_module.backup_to(conn, tmp_path / "backup.db")
    copy = db_module.connect(dest)
    assert copy.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0] == 1
    copy.close()
