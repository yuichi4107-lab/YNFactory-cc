# -*- coding: utf-8 -*-
"""金額・請求期間・ステータスなど、DBに依存しない業務ルール。

DB設計書 3章（採番・請求期間の自動算出・金額計算・ステータス遷移）に対応する。
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

MONTH_END = 99  # customers.closing_day の「月末」を表す値

STATUS_LABELS = {
    "ordered": "受注済",
    "po_issued": "発注済",
    "delivered": "納品済",
    "invoiced": "請求済",
    "paid": "入金済",
    "cancelled": "取消",
}

INVOICE_STATUS_LABELS = {
    "issued": "発行済",
    "paid": "入金済",
    "cancelled": "取消",
}

# 金額・数量の編集をロックするステータス（要件定義書 3.1）
LOCKED_STATUSES = ("invoiced", "paid")


def month_end(year: int, month: int) -> int:
    """その年月の末日を返す。"""
    return calendar.monthrange(year, month)[1]


def closing_date(year: int, month: int, closing_day: int) -> date:
    """締め日を実在する日付へ丸めて返す。

    closing_day=99 は月末。31日締めの4月のように存在しない日は月末へ丸める。
    """
    last = month_end(year, month)
    day = last if closing_day == MONTH_END else min(closing_day, last)
    return date(year, month, day)


def billing_period(year: int, month: int, closing_day: int) -> tuple[date, date]:
    """締め対象の年月と締め日から請求期間（開始日, 終了日）を算出する。

    期間終了日 = 対象月の締め日、期間開始日 = 前月の締め日の翌日。
    例: 20日締めの2026年7月分 → 2026-06-21 〜 2026-07-20
    """
    end = closing_date(year, month, closing_day)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    start = closing_date(prev_year, prev_month, closing_day) + timedelta(days=1)
    return start, end


def payment_due_date(period_end: date) -> date:
    """支払期限＝請求期間終了日の翌月末（初期版は固定ルール）。"""
    year, month = (period_end.year + 1, 1) if period_end.month == 12 else (period_end.year, period_end.month + 1)
    return date(year, month, month_end(year, month))


def line_amount(quantity: int, unit_price: int) -> int:
    """明細小計 = 数量 × 単価（税抜）。"""
    return int(quantity) * int(unit_price)


def calc_tax(subtotal: int, tax_rate: int = 10) -> int:
    """消費税。税抜合計に対して請求書単位で1回だけ計算し、1円未満は切り捨てる。"""
    return subtotal * int(tax_rate) // 100


def calc_totals(subtotal: int, tax_rate: int = 10) -> tuple[int, int, int]:
    """(税抜合計, 消費税, ご請求額) を返す。"""
    tax = calc_tax(subtotal, tax_rate)
    return subtotal, tax, subtotal + tax


def next_invoice_no(period_end: date, existing_nos: list[str]) -> str:
    """請求No. を採番する。形式: INV-YYYYMM-NNN（YYYYMM は period_end の年月）。"""
    prefix = f"INV-{period_end.year:04d}{period_end.month:02d}-"
    used = [int(no[len(prefix):]) for no in existing_nos if no.startswith(prefix) and no[len(prefix):].isdigit()]
    return f"{prefix}{(max(used) + 1 if used else 1):03d}"


def status_after_purchase_order(current: str) -> str:
    """発注登録後のステータス。納品済以降は後退させない。"""
    return "po_issued" if current == "ordered" else current


def status_after_delivery(current: str) -> str:
    """納品登録後のステータス。請求済以降は後退させない。"""
    return current if current in ("invoiced", "paid", "cancelled") else "delivered"


def can_edit_amounts(status: str) -> bool:
    """金額・数量を編集できるステータスか。"""
    return status not in LOCKED_STATUSES and status != "cancelled"


def can_cancel(status: str) -> bool:
    """受注キャンセルが可能か（請求済以降は不可）。"""
    return status not in LOCKED_STATUSES and status != "cancelled"


def format_jp_date(value) -> str:
    """帳票用の日付表記（2026年7月10日）。"""
    d = parse_date(value)
    return "" if d is None else f"{d.year}年{d.month}月{d.day}日"


def parse_date(value) -> date | None:
    """'YYYY-MM-DD' 文字列または date を date へ変換する。空値は None。"""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
