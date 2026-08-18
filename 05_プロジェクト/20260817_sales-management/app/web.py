# -*- coding: utf-8 -*-
"""Flask アプリ本体（画面設計書 S-02〜S-06 と帳票プレビュー）。

社内LAN限定・認証なしで運用する前提（要件定義書 4.10）。
"""
from __future__ import annotations

import csv
import io
from datetime import date

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, url_for)

from . import db, domain, repo


def create_app(db_file=None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sales-management-local"   # LAN内・flash用途のみ
    app.config["DB_FILE"] = db_file

    def get_conn():
        conn = db.connect(app.config["DB_FILE"])
        db.init_db(conn)
        return conn

    # ------------------------------------------------------------ フィルタ
    @app.template_filter("yen")
    def yen(value):
        return "" if value is None else "{:,}".format(int(value))

    @app.template_filter("md")
    def md(value):
        d = domain.parse_date(value)
        return "" if d is None else "{:02d}/{:02d}".format(d.month, d.day)

    @app.template_filter("jpdate")
    def jpdate(value):
        return domain.format_jp_date(value)

    @app.template_filter("status_label")
    def status_label(value):
        return domain.STATUS_LABELS.get(value, value)

    @app.template_filter("invoice_status_label")
    def invoice_status_label(value):
        return domain.INVOICE_STATUS_LABELS.get(value, value)

    def closing_label(closing_day):
        return "月末" if closing_day == domain.MONTH_END else "{}日".format(closing_day)

    app.jinja_env.globals["closing_label"] = closing_label
    app.jinja_env.globals["today"] = lambda: date.today().isoformat()

    # ------------------------------------------------------------ 共通
    def current_filters():
        today = date.today()
        return {
            "date_field": request.args.get("date_field", "order_date"),
            "date_from": request.args.get("date_from", today.replace(day=1).isoformat()),
            "date_to": request.args.get("date_to",
                                        date(today.year, today.month,
                                             domain.month_end(today.year, today.month)).isoformat()),
            "customer_id": request.args.get("customer_id", type=int),
            "supplier_id": request.args.get("supplier_id", type=int),
            "status": request.args.get("status", ""),
            "keyword": request.args.get("keyword", ""),
            "sort": request.args.get("sort", "order_no"),
            "dir": request.args.get("dir", "desc"),
        }

    def form_int(name, default=None):
        raw = (request.form.get(name) or "").replace(",", "").strip()
        if raw == "":
            return default
        return int(raw)

    # ------------------------------------------------------------ S-02 案件一覧
    @app.route("/")
    def order_list():
        conn = get_conn()
        f = current_filters()
        rows = repo.search_orders(conn, f)
        return render_template("order_list.html", rows=rows, f=f,
                               total=repo.summarize(rows),
                               by_customer=repo.summarize_by_customer(rows),
                               customers=repo.list_customers(conn),
                               suppliers=repo.list_suppliers(conn),
                               statuses=domain.STATUS_LABELS)

    @app.route("/orders.csv")
    def order_list_csv():
        """絞り込み中の一覧＋期間合計を UTF-8 BOM 付きCSVで返す（Excelでそのまま開ける）。"""
        conn = get_conn()
        f = current_filters()
        rows = repo.search_orders(conn, f)
        total = repo.summarize(rows)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\r\n")
        w.writerow(["管理No.", "受注日", "客先", "品名", "型式・図番", "数量", "単位",
                    "受注額", "発注額", "粗利", "客先納期", "納品日", "状態"])
        for r in rows:
            w.writerow([r["order_no"], r["order_date"], r["customer_name"], r["product_name"],
                        r["model_no"] or "", r["quantity"], r["unit"] or "",
                        r["order_amount"], r["purchase_amount"],
                        r["order_amount"] - r["purchase_amount"], r["customer_due_date"],
                        r["delivery_date"] or "", domain.STATUS_LABELS.get(r["status"], "")])
        w.writerow([])
        w.writerow(["期間合計", "{}〜{}".format(f["date_from"], f["date_to"]), "", "", "", "", "",
                    total["order_amount"], total["purchase_amount"], total["profit"]])
        name = "案件一覧_{}-{}.csv".format(f["date_from"].replace("-", ""),
                                            f["date_to"].replace("-", ""))
        return Response(buf.getvalue().encode("utf-8-sig"),
                        mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition":
                                 "attachment; filename*=UTF-8''" + _quote(name)})

    # ------------------------------------------------------------ S-03 案件詳細
    @app.route("/orders/new")
    def order_new():
        conn = get_conn()
        return render_template("order_detail.html", order=None, lines=[], pos=[],
                               customers=repo.list_customers(conn),
                               suppliers=repo.list_suppliers(conn))

    @app.route("/orders", methods=["POST"])
    def order_create():
        conn = get_conn()
        header = {"order_date": request.form["order_date"],
                  "customer_due_date": request.form["customer_due_date"],
                  "customer_id": form_int("customer_id"),
                  "customer_contact": request.form.get("customer_contact"),
                  "customer_order_no": request.form.get("customer_order_no")}
        line = {"product_name": request.form["product_name"],
                "model_no": request.form.get("model_no"),
                "quantity": form_int("quantity", 1),
                "unit": request.form.get("unit"),
                "unit_price": form_int("unit_price", 0),
                "note": request.form.get("note")}
        with db.transaction(conn):
            order_id = repo.create_order(conn, header, line)
        flash("受注を登録しました（管理No. {}）".format(repo.get_order(conn, order_id)["order_no"]))
        return redirect(url_for("order_detail", order_id=order_id))

    @app.route("/orders/<int:order_id>")
    def order_detail(order_id):
        conn = get_conn()
        order = repo.get_order(conn, order_id)
        if order is None:
            abort(404)
        return render_template("order_detail.html", order=order,
                               lines=repo.get_order_lines(conn, order_id),
                               pos=repo.list_purchase_orders(conn, order_id),
                               customers=repo.list_customers(conn),
                               suppliers=repo.list_suppliers(conn),
                               editable=domain.can_edit_amounts(order["status"]),
                               cancellable=domain.can_cancel(order["status"]))

    @app.route("/orders/<int:order_id>", methods=["POST"])
    def order_update(order_id):
        conn = get_conn()
        order = repo.get_order(conn, order_id)
        if order is None:
            abort(404)
        if not domain.can_edit_amounts(order["status"]):
            flash("請求済以降の案件は編集できません。請求を取り消してから修正してください。", "error")
            return redirect(url_for("order_detail", order_id=order_id))
        header = {"order_date": request.form["order_date"],
                  "customer_due_date": request.form["customer_due_date"],
                  "customer_id": form_int("customer_id"),
                  "customer_contact": request.form.get("customer_contact"),
                  "customer_order_no": request.form.get("customer_order_no")}
        line = {"product_name": request.form["product_name"],
                "model_no": request.form.get("model_no"),
                "quantity": form_int("quantity", 1),
                "unit": request.form.get("unit"),
                "unit_price": form_int("unit_price", 0),
                "note": request.form.get("note")}
        with db.transaction(conn):
            repo.update_order(conn, order_id, header, line)
        flash("保存しました")
        return redirect(url_for("order_detail", order_id=order_id))

    @app.route("/orders/<int:order_id>/cancel", methods=["POST"])
    def order_cancel(order_id):
        conn = get_conn()
        order = repo.get_order(conn, order_id)
        if order is None:
            abort(404)
        if not domain.can_cancel(order["status"]):
            flash("請求済以降の案件は取り消せません。", "error")
        else:
            with db.transaction(conn):
                repo.set_status(conn, order_id, "cancelled")
            flash("受注を取り消しました")
        return redirect(url_for("order_detail", order_id=order_id))

    # ------------------------------------------------------------ 発注
    @app.route("/orders/<int:order_id>/purchase-orders", methods=["POST"])
    def purchase_order_add(order_id):
        conn = get_conn()
        order = repo.get_order(conn, order_id)
        if order is None:
            abort(404)
        data = _po_form(form_int)
        with db.transaction(conn):
            repo.add_purchase_order(conn, order_id, data)
            repo.set_status(conn, order_id, domain.status_after_purchase_order(order["status"]))
        if data["supplier_due_date"] > order["customer_due_date"]:
            flash("発注納期が客先納期より後です（保存はしています）", "warn")
        flash("発注を追加しました")
        return redirect(url_for("order_detail", order_id=order_id))

    @app.route("/purchase-orders/<int:po_id>", methods=["POST"])
    def purchase_order_update(po_id):
        conn = get_conn()
        row = conn.execute("SELECT sales_order_id FROM purchase_orders WHERE id = ?",
                           (po_id,)).fetchone()
        if row is None:
            abort(404)
        order_id = row["sales_order_id"]
        if request.form.get("action") == "delete":
            with db.transaction(conn):
                repo.delete_purchase_order(conn, po_id)
                if not repo.list_purchase_orders(conn, order_id):
                    order = repo.get_order(conn, order_id)
                    if order["status"] == "po_issued":
                        repo.set_status(conn, order_id, "ordered")
            flash("発注を削除しました")
        else:
            with db.transaction(conn):
                repo.update_purchase_order(conn, po_id, _po_form(form_int))
            flash("発注を保存しました")
        return redirect(url_for("order_detail", order_id=order_id))

    def _po_form(fi):
        return {"supplier_id": fi("supplier_id"),
                "po_date": request.form["po_date"],
                "supplier_due_date": request.form["supplier_due_date"],
                "product_name": request.form["product_name"],
                "model_no": request.form.get("model_no"),
                "quantity": fi("quantity", 1),
                "unit": request.form.get("unit"),
                "unit_price": fi("unit_price", 0),
                "note": request.form.get("note")}

    # ------------------------------------------------------------ 納品
    @app.route("/orders/<int:order_id>/delivery", methods=["POST"])
    def delivery_save(order_id):
        conn = get_conn()
        order = repo.get_order(conn, order_id)
        if order is None:
            abort(404)
        with db.transaction(conn):
            repo.save_delivery(conn, order_id, request.form["delivery_date"])
            repo.set_status(conn, order_id, domain.status_after_delivery(order["status"]))
        flash("納品を登録しました")
        return redirect(url_for("order_detail", order_id=order_id))

    @app.route("/delivery-note")
    def delivery_note():
        """納品書プレビュー。scope=order（案件単位）/ customer（客先まとめ）。"""
        conn = get_conn()
        scope = request.args.get("scope", "order")
        customer_id = request.args.get("customer_id", type=int)
        order_id = request.args.get("order_id", type=int)
        if scope == "order":
            order = repo.get_order(conn, order_id)
            if order is None:
                abort(404)
            customer_id = order["customer_id"]
            orders = repo.delivery_note_orders(conn, customer_id, [order_id])
        else:
            orders = repo.delivery_note_orders(
                conn, customer_id,
                date_from=request.args.get("date_from"),
                date_to=request.args.get("date_to"))
        if not orders:
            flash("納品日が登録された案件がありません", "error")
            return redirect(url_for("order_list"))
        items = []
        for o in orders:
            for l in repo.get_order_lines(conn, o["id"]):
                items.append({"order": o, "line": l,
                              "amount": domain.line_amount(l["quantity"], l["unit_price"])})
        return render_template("print_delivery_note.html",
                               customer=repo.get_customer(conn, customer_id),
                               company=repo.get_company(conn), items=items, scope=scope,
                               order_id=order_id,
                               total=sum(i["amount"] for i in items),
                               delivery_date=max(o["delivery_date"] for o in orders))

    # ------------------------------------------------------------ S-04 締め処理
    @app.route("/closing")
    def closing():
        conn = get_conn()
        customers = repo.list_customers(conn)
        customer_id = request.args.get("customer_id", type=int)
        bulk = request.args.get("customer_id") == "all"
        today = date.today()
        year = request.args.get("year", type=int) or today.year
        month = request.args.get("month", type=int) or today.month
        groups, period_start, period_end = [], request.args.get("period_start"), request.args.get("period_end")
        targets = customers if bulk else [c for c in customers if c["id"] == customer_id]
        for c in targets:
            if bulk or not (period_start and period_end):
                s, e = domain.billing_period(year, month, c["closing_day"])
                s, e = s.isoformat(), e.isoformat()
            else:
                s, e = period_start, period_end
            lines = repo.billable_lines(conn, c["id"], s, e)
            if bulk and not lines:
                continue
            groups.append({"customer": c, "period_start": s, "period_end": e, "lines": lines,
                           "subtotal": sum(l["amount"] for l in lines)})
        company = repo.get_company(conn)
        for g in groups:
            g["subtotal"], g["tax"], g["total"] = domain.calc_totals(g["subtotal"],
                                                                    company["tax_rate"])
        return render_template("closing.html", customers=customers, groups=groups,
                               customer_id=customer_id, bulk=bulk, year=year, month=month,
                               company=company)

    @app.route("/closing/confirm", methods=["POST"])
    def closing_confirm():
        conn = get_conn()
        company = repo.get_company(conn)
        customer_ids = request.form.getlist("customer_ids")
        selected = set(request.form.getlist("line_ids"))
        issue_date = request.form.get("issue_date") or date.today().isoformat()
        created = []
        with db.transaction(conn):
            for cid in customer_ids:
                cid = int(cid)
                s = request.form["period_start_{}".format(cid)]
                e = request.form["period_end_{}".format(cid)]
                lines = [l for l in repo.billable_lines(conn, cid, s, e)
                         if str(l["line_id"]) in selected]
                if not lines:
                    continue
                created.append(repo.create_invoice(conn, cid, s, e, issue_date, lines,
                                                   company["tax_rate"]))
        if not created:
            flash("請求対象が選択されていません", "error")
            return redirect(url_for("closing"))
        flash("請求書を{}件確定しました".format(len(created)))
        return redirect(url_for("invoice_print", ids=",".join(str(i) for i in created)))

    # ------------------------------------------------------------ S-05 請求一覧
    @app.route("/invoices")
    def invoice_list():
        conn = get_conn()
        return render_template("invoice_list.html", invoices=repo.list_invoices(conn))

    @app.route("/invoices/<int:invoice_id>/paid", methods=["POST"])
    def invoice_paid(invoice_id):
        conn = get_conn()
        with db.transaction(conn):
            repo.mark_invoice_paid(conn, invoice_id)
        flash("入金済にしました")
        return redirect(url_for("invoice_list"))

    @app.route("/invoices/<int:invoice_id>/cancel", methods=["POST"])
    def invoice_cancel(invoice_id):
        conn = get_conn()
        with db.transaction(conn):
            repo.cancel_invoice(conn, invoice_id)
        flash("請求を取り消しました（対象案件は納品済に戻り、再請求できます）")
        return redirect(url_for("invoice_list"))

    @app.route("/invoices/print")
    def invoice_print():
        """請求書プレビュー。ids=1,2,3 で客先ごとに改ページして連続印刷する。"""
        conn = get_conn()
        ids = [int(i) for i in (request.args.get("ids") or "").split(",") if i.strip().isdigit()]
        docs = []
        for invoice_id in ids:
            inv = repo.get_invoice(conn, invoice_id)
            if inv is None:
                continue
            docs.append({"invoice": inv, "lines": repo.get_invoice_lines(conn, invoice_id),
                         "due": domain.payment_due_date(domain.parse_date(inv["period_end"]))})
        if not docs:
            abort(404)
        return render_template("print_invoice.html", docs=docs, company=repo.get_company(conn))

    # ------------------------------------------------------------ S-06 マスタ
    @app.route("/masters")
    def masters():
        conn = get_conn()
        return render_template("masters.html", customers=repo.list_customers(conn),
                               suppliers=repo.list_suppliers(conn),
                               company=repo.get_company(conn),
                               tab=request.args.get("tab", "customers"))

    @app.route("/masters/customers", methods=["POST"])
    def customer_save():
        conn = get_conn()
        customer_id = request.form.get("id", type=int)
        if request.form.get("action") == "delete":
            with db.transaction(conn):
                repo.deactivate_customer(conn, customer_id)
            flash("客先を削除しました")
        else:
            data = {k: request.form.get(k) for k in repo.CUSTOMER_FIELDS}
            data["closing_day"] = form_int("closing_day", domain.MONTH_END)
            with db.transaction(conn):
                repo.save_customer(conn, data, customer_id)
            flash("客先を保存しました")
        return redirect(url_for("masters", tab="customers"))

    @app.route("/masters/suppliers", methods=["POST"])
    def supplier_save():
        conn = get_conn()
        supplier_id = request.form.get("id", type=int)
        if request.form.get("action") == "delete":
            with db.transaction(conn):
                repo.deactivate_supplier(conn, supplier_id)
            flash("仕入先を削除しました")
        else:
            data = {k: request.form.get(k) for k in repo.SUPPLIER_FIELDS}
            with db.transaction(conn):
                repo.save_supplier(conn, data, supplier_id)
            flash("仕入先を保存しました")
        return redirect(url_for("masters", tab="suppliers"))

    @app.route("/masters/company", methods=["POST"])
    def company_save():
        conn = get_conn()
        data = {k: request.form.get(k) for k in repo.COMPANY_FIELDS}
        data["tax_rate"] = form_int("tax_rate", 10)
        with db.transaction(conn):
            repo.save_company(conn, data)
        flash("自社情報を保存しました")
        return redirect(url_for("masters", tab="company"))

    return app


def _quote(name: str) -> str:
    from urllib.parse import quote
    return quote(name)
