# -*- coding: utf-8 -*-
"""帳票の発行単位・期間指定・改ページのテスト（帳票設計書 2章・3章）。"""
from app import db as db_module
from app import repo
from test_web import create_order, html, seed


def deliver_all(app, delivery_date="2026-07-29"):
    conn = db_module.connect(app.config["DB_FILE"])
    for row in repo.search_orders(conn, {}):
        if row["delivery_date"] is None:
            with db_module.transaction(conn):
                repo.save_delivery(conn, row["id"], delivery_date)
                repo.set_status(conn, row["id"], "delivered")
    conn.close()


def test_delivery_note_customer_scope_merges_orders_into_one_sheet(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id, product="シャフト", qty=2, price=10000)
    create_order(client, customer_id, product="ブラケット", qty=1, price=55000)
    deliver_all(app)
    body = html(client.get("/delivery-note?scope=customer&customer_id={}".format(customer_id)))
    assert body.count('class="sheet"') == 1        # 1枚にまとめる
    assert "シャフト" in body and "ブラケット" in body
    assert "75,000" in body                        # 合計 = 20,000 + 55,000


def test_delivery_note_customer_scope_respects_period(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id, product="シャフト")
    deliver_all(app, "2026-07-29")
    create_order(client, customer_id, product="ブラケット", qty=1, price=55000)
    deliver_all(app, "2026-08-03")
    body = html(client.get("/delivery-note?scope=customer&customer_id={}"
                           "&date_from=2026-07-01&date_to=2026-07-31".format(customer_id)))
    assert "シャフト" in body and "ブラケット" not in body


def test_delivery_note_order_scope_is_single_order(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id, product="シャフト")
    create_order(client, customer_id, product="ブラケット")
    deliver_all(app)
    conn = db_module.connect(app.config["DB_FILE"])
    order_id = [r["id"] for r in repo.search_orders(conn, {})
                if r["product_name"] == "シャフト"][0]
    conn.close()
    body = html(client.get("/delivery-note?scope=order&order_id={}".format(order_id)))
    assert "シャフト" in body and "ブラケット" not in body


def test_delivery_note_paginates_over_10_lines(client, app):
    customer_id, _ = seed(client, app)
    for i in range(11):
        create_order(client, customer_id, product="品目{}".format(i), qty=1, price=1000)
    deliver_all(app)
    body = html(client.get("/delivery-note?scope=customer&customer_id={}".format(customer_id)))
    assert body.count('class="sheet"') == 2        # 10行/頁で改頁
    assert body.count("合計") == 1                  # 合計は最終頁のみ


def test_invoice_print_paginates_over_15_lines_and_bulk_pages_per_customer(client, app):
    customer_id, _ = seed(client, app)
    client.post("/masters/customers", data={"name": "山本精機", "honorific": "御中",
                                            "closing_day": "99"})
    conn = db_module.connect(app.config["DB_FILE"])
    other = [c for c in repo.list_customers(conn) if c["name"] == "山本精機"][0]["id"]
    conn.close()
    for i in range(16):
        create_order(client, customer_id, product="品目{}".format(i), qty=1, price=1000)
    create_order(client, other, product="ブラケット", qty=1, price=32000)
    deliver_all(app)

    conn = db_module.connect(app.config["DB_FILE"])
    invoice_ids = []
    for cid in (customer_id, other):
        lines = repo.billable_lines(conn, cid, "2026-07-01", "2026-07-31")
        with db_module.transaction(conn):
            invoice_ids.append(repo.create_invoice(conn, cid, "2026-07-01", "2026-07-31",
                                                   "2026-07-31", lines))
    conn.close()

    body = html(client.get("/invoices/print?ids={}".format(
        ",".join(str(i) for i in invoice_ids))))
    # 16行の客先は2頁 + もう1客先が1頁 = 3頁、客先ごとに改ページされる
    assert body.count('class="sheet"') == 3
    assert "INV-202607-001" in body and "INV-202607-002" in body
    assert body.count("ご請求額") == 2              # 合計欄は客先ごとに最終頁のみ


def test_invoice_print_shows_qualified_invoice_requirements(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id)
    deliver_all(app)
    conn = db_module.connect(app.config["DB_FILE"])
    lines = repo.billable_lines(conn, customer_id, "2026-07-01", "2026-07-31")
    with db_module.transaction(conn):
        invoice_id = repo.create_invoice(conn, customer_id, "2026-07-01", "2026-07-31",
                                         "2026-07-31", lines)
    conn.close()
    body = html(client.get("/invoices/print?ids={}".format(invoice_id)))
    assert "株式会社テスト" in body                       # ① 発行者名
    assert "T1234567890123" in body                      # ① 登録番号
    assert "07/29" in body                               # ② 取引年月日（納品日）
    assert "シャフト" in body and "A0010" in body         # ③ 取引内容
    assert "10%対象" in body and "20,000" in body         # ④ 税率ごとの対価
    assert "消費税（10%）" in body and "2,000" in body     # ⑤ 税率ごとの消費税額
    assert "ダイゴテック 御中" in body                    # ⑥ 交付先
