# -*- coding: utf-8 -*-
"""画面（S-02〜S-06）と帳票プレビューのテスト。"""
from app import db as db_module
from app import repo


def html(response):
    return response.data.decode("utf-8")


def seed(client, app):
    """客先・仕入先・自社情報を画面経由で登録する。"""
    client.post("/masters/customers", data={
        "name": "ダイゴテック", "honorific": "御中", "postal_code": "460-0001",
        "address": "名古屋市中区1-1", "phone": "052-000-0000", "default_contact": "山田",
        "closing_day": "99", "note": ""})
    client.post("/masters/suppliers", data={"name": "ゆーいち工業"})
    client.post("/masters/company", data={
        "company_name": "株式会社テスト", "postal_code": "460-0002", "address": "名古屋市中区2-2",
        "phone": "052-111-1111", "invoice_reg_no": "T1234567890123",
        "bank_info": "◯◯銀行 普通 1234567", "tax_rate": "10"})
    conn = db_module.connect(app.config["DB_FILE"])
    customer = repo.list_customers(conn)[0]
    supplier = repo.list_suppliers(conn)[0]
    conn.close()
    return customer["id"], supplier["id"]


def create_order(client, customer_id, product="シャフト", qty=2, price=10000):
    return client.post("/orders", data={
        "order_date": "2026-07-10", "customer_due_date": "2026-07-31",
        "customer_id": str(customer_id), "customer_contact": "山田", "customer_order_no": "PO-1",
        "product_name": product, "model_no": "A0010", "quantity": str(qty), "unit": "ヶ",
        "unit_price": str(price), "note": "表面処理注意"}, follow_redirects=True)


def test_order_list_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "案件一覧" in html(res)


def test_create_order_shows_order_no(client, app):
    customer_id, _ = seed(client, app)
    res = create_order(client, customer_id)
    assert res.status_code == 200
    assert "管理No. 10100" in html(res)


def test_full_flow_order_to_invoice(client, app):
    customer_id, supplier_id = seed(client, app)
    create_order(client, customer_id)
    conn = db_module.connect(app.config["DB_FILE"])
    order = repo.list_invoices(conn) and None
    order_id = repo.search_orders(conn, {})[0]["id"]
    conn.close()

    # 発注 → 発注済
    client.post("/orders/{}/purchase-orders".format(order_id), data={
        "supplier_id": str(supplier_id), "po_date": "2026-07-11",
        "supplier_due_date": "2026-07-29", "product_name": "シャフト", "model_no": "A0010",
        "quantity": "2", "unit": "ヶ", "unit_price": "8000", "note": ""}, follow_redirects=True)
    conn = db_module.connect(app.config["DB_FILE"])
    assert repo.get_order(conn, order_id)["status"] == "po_issued"
    conn.close()

    # 納品 → 納品済
    client.post("/orders/{}/delivery".format(order_id),
                data={"delivery_date": "2026-07-29"}, follow_redirects=True)
    conn = db_module.connect(app.config["DB_FILE"])
    assert repo.get_order(conn, order_id)["status"] == "delivered"
    conn.close()

    # 納品書プレビュー
    res = client.get("/delivery-note?scope=order&order_id={}".format(order_id))
    body = html(res)
    assert "納品書" in body and "20,000" in body and "ダイゴテック" in body

    # 締め処理 → 請求対象が出る
    res = client.get("/closing?customer_id={}&year=2026&month=7".format(customer_id))
    body = html(res)
    assert "10100" in body and "22,000" in body

    conn = db_module.connect(app.config["DB_FILE"])
    line_id = repo.get_order_lines(conn, order_id)[0]["id"]
    conn.close()
    res = client.post("/closing/confirm", data={
        "customer_ids": str(customer_id), "line_ids": str(line_id),
        "period_start_{}".format(customer_id): "2026-07-01",
        "period_end_{}".format(customer_id): "2026-07-31",
        "issue_date": "2026-07-31"}, follow_redirects=True)
    body = html(res)
    assert "請求書" in body and "INV-202607-001" in body
    assert "T1234567890123" in body            # 適格請求書の登録番号
    assert "2026年8月31日" in body              # 支払期限＝翌月末
    assert "¥22,000" in body

    conn = db_module.connect(app.config["DB_FILE"])
    assert repo.get_order(conn, order_id)["status"] == "invoiced"
    conn.close()


def test_locked_order_cannot_be_edited(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id)
    conn = db_module.connect(app.config["DB_FILE"])
    order_id = repo.search_orders(conn, {})[0]["id"]
    with db_module.transaction(conn):
        repo.set_status(conn, order_id, "invoiced")
    conn.close()
    res = client.post("/orders/{}".format(order_id), data={
        "order_date": "2026-07-10", "customer_due_date": "2026-07-31",
        "customer_id": str(customer_id), "product_name": "改ざん", "quantity": "9",
        "unit_price": "1"}, follow_redirects=True)
    assert "請求済以降の案件は編集できません" in html(res)
    conn = db_module.connect(app.config["DB_FILE"])
    assert repo.get_order_lines(conn, order_id)[0]["product_name"] == "シャフト"
    conn.close()


def test_csv_download_has_bom_and_totals(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id)
    res = client.get("/orders.csv?date_from=2026-07-01&date_to=2026-07-31")
    assert res.status_code == 200
    assert res.data.startswith(b"\xef\xbb\xbf")          # Excelでそのまま開けるUTF-8 BOM
    text = res.data.decode("utf-8-sig")
    assert "管理No." in text and "10100" in text and "期間合計" in text


def test_bulk_closing_covers_all_customers(client, app):
    customer_id, _ = seed(client, app)
    client.post("/masters/customers", data={"name": "山本精機", "honorific": "御中",
                                            "closing_day": "99"})
    conn = db_module.connect(app.config["DB_FILE"])
    other = [c for c in repo.list_customers(conn) if c["name"] == "山本精機"][0]["id"]
    conn.close()
    create_order(client, customer_id)
    create_order(client, other, product="ブラケット", qty=1, price=32000)
    conn = db_module.connect(app.config["DB_FILE"])
    for row in repo.search_orders(conn, {}):
        with db_module.transaction(conn):
            repo.save_delivery(conn, row["id"], "2026-07-29")
            repo.set_status(conn, row["id"], "delivered")
    conn.close()
    res = client.get("/closing?customer_id=all&year=2026&month=7")
    body = html(res)
    assert "ダイゴテック" in body and "山本精機" in body


def test_invoice_cancel_from_list(client, app):
    customer_id, _ = seed(client, app)
    create_order(client, customer_id)
    conn = db_module.connect(app.config["DB_FILE"])
    order_id = repo.search_orders(conn, {})[0]["id"]
    with db_module.transaction(conn):
        repo.save_delivery(conn, order_id, "2026-07-29")
        repo.set_status(conn, order_id, "delivered")
    lines = repo.billable_lines(conn, customer_id, "2026-07-01", "2026-07-31")
    with db_module.transaction(conn):
        invoice_id = repo.create_invoice(conn, customer_id, "2026-07-01", "2026-07-31",
                                         "2026-07-31", lines)
    conn.close()
    res = client.post("/invoices/{}/cancel".format(invoice_id), follow_redirects=True)
    assert "請求を取り消しました" in html(res)
    conn = db_module.connect(app.config["DB_FILE"])
    assert repo.get_order(conn, order_id)["status"] == "delivered"
    conn.close()


def test_masters_screen_lists_registered_data(client, app):
    seed(client, app)
    assert "ダイゴテック" in html(client.get("/masters?tab=customers"))
    assert "ゆーいち工業" in html(client.get("/masters?tab=suppliers"))
    assert "T1234567890123" in html(client.get("/masters?tab=company"))
