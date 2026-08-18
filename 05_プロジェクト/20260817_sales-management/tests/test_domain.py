# -*- coding: utf-8 -*-
"""業務ルール（請求期間・金額・採番・ステータス）のテスト。"""
from datetime import date

import pytest

from app import domain


@pytest.mark.parametrize("year, month, closing_day, expected", [
    # 20日締めの2026年7月分 → 6/21〜7/20（要件定義書 4.5 の例）
    (2026, 7, 20, (date(2026, 6, 21), date(2026, 7, 20))),
    # 月末締めの2026年7月分 → 7/1〜7/31
    (2026, 7, 99, (date(2026, 7, 1), date(2026, 7, 31))),
    # 31日締めの4月は月末へ丸める（3/31翌日=4/1 〜 4/30）
    (2026, 4, 31, (date(2026, 4, 1), date(2026, 4, 30))),
    # 年またぎ: 25日締めの1月分 → 前年12/26〜1/25
    (2026, 1, 25, (date(2025, 12, 26), date(2026, 1, 25))),
    # うるう年の2月末
    (2028, 2, 99, (date(2028, 2, 1), date(2028, 2, 29))),
    # 30日締めの3月は、前月(2月)が存在しないため月末丸め → 3/1〜3/30
    (2026, 3, 30, (date(2026, 3, 1), date(2026, 3, 30))),
])
def test_billing_period(year, month, closing_day, expected):
    assert domain.billing_period(year, month, closing_day) == expected


def test_payment_due_date_is_month_end_of_next_month():
    assert domain.payment_due_date(date(2026, 7, 31)) == date(2026, 8, 31)
    assert domain.payment_due_date(date(2026, 12, 20)) == date(2027, 1, 31)


def test_line_amount_and_totals():
    assert domain.line_amount(2, 10000) == 20000
    assert domain.calc_totals(20000) == (20000, 2000, 22000)


@pytest.mark.parametrize("subtotal, expected_tax", [
    (20000, 2000),
    (999, 99),      # 99.9 → 切り捨て
    (1, 0),         # 0.1 → 切り捨て
    (12345, 1234),  # 1234.5 → 切り捨て
])
def test_tax_is_truncated(subtotal, expected_tax):
    assert domain.calc_tax(subtotal) == expected_tax


def test_tax_rate_is_configurable():
    assert domain.calc_tax(20000, 8) == 1600


def test_next_invoice_no():
    assert domain.next_invoice_no(date(2026, 7, 31), []) == "INV-202607-001"
    assert domain.next_invoice_no(date(2026, 7, 31), ["INV-202607-001"]) == "INV-202607-002"
    # 別月の採番は影響しない
    assert domain.next_invoice_no(date(2026, 8, 31), ["INV-202607-009"]) == "INV-202608-001"
    # 連番は最大値+1（欠番があっても重複しない）
    assert domain.next_invoice_no(
        date(2026, 7, 31), ["INV-202607-001", "INV-202607-003"]) == "INV-202607-004"


def test_status_transitions():
    assert domain.status_after_purchase_order("ordered") == "po_issued"
    # 納品済以降は発注追加で後退させない
    assert domain.status_after_delivery("po_issued") == "delivered"
    assert domain.status_after_purchase_order("delivered") == "delivered"
    assert domain.status_after_delivery("invoiced") == "invoiced"


def test_edit_lock():
    assert domain.can_edit_amounts("delivered") is True
    assert domain.can_edit_amounts("invoiced") is False
    assert domain.can_edit_amounts("paid") is False
    assert domain.can_cancel("invoiced") is False
    assert domain.can_cancel("po_issued") is True


def test_format_jp_date():
    assert domain.format_jp_date("2026-07-10") == "2026年7月10日"
    assert domain.format_jp_date(None) == ""
