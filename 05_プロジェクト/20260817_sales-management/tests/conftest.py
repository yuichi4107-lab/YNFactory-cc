# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db as db_module  # noqa: E402
from app import repo  # noqa: E402
from app.web import create_app  # noqa: E402


@pytest.fixture()
def db_file(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture()
def conn(db_file):
    c = db_module.connect(db_file)
    db_module.init_db(c)
    yield c
    c.close()


@pytest.fixture()
def masters(conn):
    """客先・仕入先・自社情報の最小セット。"""
    with db_module.transaction(conn):
        customer_id = repo.save_customer(conn, {
            "name": "ダイゴテック", "honorific": "御中", "postal_code": "460-0001",
            "address": "名古屋市中区1-1", "phone": "052-000-0000",
            "default_contact": "山田", "closing_day": 99, "note": ""})
        customer2_id = repo.save_customer(conn, {
            "name": "山本精機", "honorific": "御中", "closing_day": 20})
        supplier_id = repo.save_supplier(conn, {"name": "ゆーいち工業"})
        repo.save_company(conn, {
            "company_name": "株式会社テスト", "postal_code": "460-0002", "address": "名古屋市中区2-2",
            "phone": "052-111-1111", "invoice_reg_no": "T1234567890123",
            "bank_info": "◯◯銀行 ◯◯支店 普通 1234567", "tax_rate": 10})
    return {"customer_id": customer_id, "customer2_id": customer2_id, "supplier_id": supplier_id}


@pytest.fixture()
def app(db_file):
    application = create_app(db_file)
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
