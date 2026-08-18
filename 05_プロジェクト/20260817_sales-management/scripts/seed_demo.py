# -*- coding: utf-8 -*-
"""動作確認用のデモデータを投入する（要件定義書 4.5 の計算例と同じ案件を作る）。

    python scripts/seed_demo.py            # 既定のDBへ投入
    SALES_DB_PATH=demo.db python scripts/seed_demo.py

自社情報はプレースホルダのため、実運用前にマスタ画面で実値へ差し替えること。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, repo  # noqa: E402


def main() -> None:
    conn = db.connect()
    db.init_db(conn)
    if repo.list_customers(conn):
        print("既にデータがあります。投入を中止しました。")
        return

    with db.transaction(conn):
        daigo = repo.save_customer(conn, {
            "name": "ダイゴテック", "honorific": "御中", "postal_code": "460-0001",
            "address": "愛知県名古屋市中区栄1-1-1", "phone": "052-000-0000",
            "default_contact": "山田", "closing_day": 99, "note": ""})
        yamamoto = repo.save_customer(conn, {
            "name": "山本精機", "honorific": "御中", "postal_code": "486-0000",
            "address": "愛知県春日井市1-2-3", "phone": "0568-00-0000",
            "default_contact": "佐藤", "closing_day": 20, "note": "20日締め"})
        yuichi = repo.save_supplier(conn, {
            "name": "ゆーいち工業", "postal_code": "470-0000",
            "address": "愛知県豊田市1-1", "phone": "0565-00-0000", "note": ""})
        repo.save_company(conn, {
            "company_name": "株式会社◯◯◯◯", "postal_code": "460-0003",
            "address": "愛知県名古屋市中区錦2-2-2", "phone": "052-222-2222",
            "invoice_reg_no": "T1234567890123",
            "bank_info": "◯◯銀行 ◯◯支店 普通 1234567 カ)◯◯◯◯", "tax_rate": 10})

        order1 = repo.create_order(
            conn,
            {"order_date": "2026-07-10", "customer_due_date": "2026-07-31",
             "customer_id": daigo, "customer_contact": "山田", "customer_order_no": "D-2026-118"},
            {"product_name": "シャフト", "model_no": "A0010", "quantity": 2, "unit": "ヶ",
             "unit_price": 10000, "note": "表面処理注意"})
        repo.add_purchase_order(conn, order1, {
            "supplier_id": yuichi, "po_date": "2026-07-11", "supplier_due_date": "2026-07-29",
            "product_name": "シャフト", "model_no": "A0010", "quantity": 2, "unit": "ヶ",
            "unit_price": 8000, "note": ""})
        repo.save_delivery(conn, order1, "2026-07-29")
        repo.set_status(conn, order1, "delivered")

        order2 = repo.create_order(
            conn,
            {"order_date": "2026-07-15", "customer_due_date": "2026-07-31",
             "customer_id": daigo, "customer_contact": "山田", "customer_order_no": "D-2026-125"},
            {"product_name": "ブラケット", "model_no": "B0221", "quantity": 5, "unit": "ヶ",
             "unit_price": 11000, "note": ""})
        repo.add_purchase_order(conn, order2, {
            "supplier_id": yuichi, "po_date": "2026-07-16", "supplier_due_date": "2026-07-28",
            "product_name": "ブラケット", "model_no": "B0221", "quantity": 5, "unit": "ヶ",
            "unit_price": 8000, "note": ""})
        repo.save_delivery(conn, order2, "2026-07-30")
        repo.set_status(conn, order2, "delivered")

        order3 = repo.create_order(
            conn,
            {"order_date": "2026-07-20", "customer_due_date": "2026-08-10",
             "customer_id": yamamoto, "customer_contact": "佐藤", "customer_order_no": "Y-778"},
            {"product_name": "カラー", "model_no": "C0032", "quantity": 8, "unit": "ヶ",
             "unit_price": 4000, "note": ""})
        repo.add_purchase_order(conn, order3, {
            "supplier_id": yuichi, "po_date": "2026-07-21", "supplier_due_date": "2026-08-05",
            "product_name": "カラー", "model_no": "C0032", "quantity": 8, "unit": "ヶ",
            "unit_price": 3000, "note": ""})
        repo.set_status(conn, order3, "po_issued")

    print("デモデータを投入しました:", db.db_path())


if __name__ == "__main__":
    main()
