from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "novatrade_secret_key"
DB = "novatrade.db"

# ── DATABASE SETUP ─────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS purchase_requisitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_number TEXT,
            material_code TEXT,
            material_desc TEXT,
            quantity INTEGER,
            department TEXT,
            plant TEXT,
            required_date TEXT,
            justification TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS rfqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfq_number TEXT,
            pr_number TEXT,
            material_code TEXT,
            quantity INTEGER,
            deadline TEXT,
            vendors TEXT,
            status TEXT DEFAULT 'Sent',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfq_number TEXT,
            vendor_code TEXT,
            vendor_name TEXT,
            unit_price REAL,
            lead_time INTEGER,
            payment_terms TEXT,
            total_value REAL,
            status TEXT DEFAULT 'Received'
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT,
            pr_number TEXT,
            rfq_number TEXT,
            vendor_code TEXT,
            vendor_name TEXT,
            material_code TEXT,
            material_desc TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_value REAL,
            plant TEXT,
            storage_location TEXT,
            status TEXT DEFAULT 'Released',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS goods_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gr_number TEXT,
            po_number TEXT,
            material_code TEXT,
            quantity_received INTEGER,
            plant TEXT,
            storage_location TEXT,
            movement_type TEXT DEFAULT '101',
            quality_status TEXT,
            posted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            vendor_invoice_ref TEXT,
            po_number TEXT,
            gr_number TEXT,
            vendor_code TEXT,
            vendor_name TEXT,
            amount REAL,
            po_value REAL,
            match_status TEXT DEFAULT 'Pending',
            status TEXT DEFAULT 'Pending',
            posted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_number TEXT,
            invoice_number TEXT,
            vendor_code TEXT,
            vendor_name TEXT,
            amount REAL,
            payment_method TEXT,
            payment_date TEXT,
            status TEXT DEFAULT 'Completed'
        );
    """)
    conn.commit()
    conn.close()

# ── HELPERS ────────────────────────────────────────────────────────────────
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today():
    return datetime.now().strftime("%Y-%m-%d")

def next_num(table, col, prefix):
    conn = get_db()
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return f"{prefix}{str(count + 1).zfill(7)}"

def get_latest(table):
    conn = get_db()
    row = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def get_all(table):
    conn = get_db()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

VENDORS = {
    "V001": {"name": "RawMat Suppliers India Ltd.", "city": "Kolkata"},
    "V002": {"name": "SteelWorks Co.",              "city": "Mumbai"},
    "V003": {"name": "MetalEdge India",             "city": "Chennai"},
}

QUOTE_PRICES = {
    "V001": {"price": 850,  "lead": 7,  "terms": "NET30"},
    "V002": {"price": 870,  "lead": 10, "terms": "NET45"},
    "V003": {"price": 890,  "lead": 12, "terms": "NET60"},
}

# ── DASHBOARD ──────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    conn = get_db()
    stats = {
        "pr_count":  conn.execute("SELECT COUNT(*) FROM purchase_requisitions").fetchone()[0],
        "po_count":  conn.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0],
        "gr_count":  conn.execute("SELECT COUNT(*) FROM goods_receipts").fetchone()[0],
        "inv_count": conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0],
        "pay_total": conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0],
    }
    recent_pr  = conn.execute("SELECT * FROM purchase_requisitions ORDER BY id DESC LIMIT 3").fetchall()
    recent_po  = conn.execute("SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()

    # figure out which steps are done for the flow diagram
    steps_done = {
        "pr":      stats["pr_count"] > 0,
        "rfq":     conn_count("rfqs") > 0,
        "compare": conn_count("quotations") > 0,
        "po":      stats["po_count"] > 0,
        "gr":      stats["gr_count"] > 0,
        "invoice": stats["inv_count"] > 0,
        "payment": conn_count("payments") > 0,
    }
    return render_template("dashboard.html", stats=stats,
                           recent_pr=recent_pr, recent_po=recent_po,
                           steps_done=steps_done)

def conn_count(table):
    conn = get_db()
    c = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return c

# ── STEP 1: PURCHASE REQUISITION ──────────────────────────────────────────
@app.route("/pr", methods=["GET", "POST"])
def purchase_requisition():
    if request.method == "POST":
        action = request.form.get("action")
        conn = get_db()

        if action == "submit":
            pr_num = next_num("purchase_requisitions", "pr_number", "PR")
            conn.execute("""
                INSERT INTO purchase_requisitions
                (pr_number, material_code, material_desc, quantity, department,
                 plant, required_date, justification, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (pr_num,
                  request.form["material_code"],
                  request.form["material_desc"],
                  request.form["quantity"],
                  request.form["department"],
                  request.form["plant"],
                  request.form["required_date"],
                  request.form["justification"],
                  "Pending", now()))
            conn.commit()
            flash(f"✅ {pr_num} submitted for approval.", "success")

        elif action == "approve":
            pr_id = request.form["pr_id"]
            conn.execute("UPDATE purchase_requisitions SET status='Approved' WHERE id=?", (pr_id,))
            conn.commit()
            flash("✅ Purchase Requisition Approved!", "success")

        conn.close()
        return redirect(url_for("purchase_requisition"))

    prs = get_all("purchase_requisitions")
    return render_template("pr.html", prs=prs, today=today())


# ── STEP 2: RFQ ───────────────────────────────────────────────────────────
@app.route("/rfq", methods=["GET", "POST"])
def rfq():
    if request.method == "POST":
        pr = get_db().execute(
            "SELECT * FROM purchase_requisitions WHERE status='Approved' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not pr:
            flash("⚠️ No approved PR found. Approve a PR first.", "warning")
            return redirect(url_for("rfq"))

        rfq_num = next_num("rfqs", "rfq_number", "RFQ")
        vendors_selected = request.form.getlist("vendors")
        conn = get_db()
        conn.execute("""
            INSERT INTO rfqs (rfq_number, pr_number, material_code, quantity,
                              deadline, vendors, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (rfq_num, pr["pr_number"], pr["material_code"], pr["quantity"],
              request.form["deadline"], ",".join(vendors_selected),
              "Sent", now()))

        # Auto-add quotations from selected vendors
        for v in vendors_selected:
            q = QUOTE_PRICES[v]
            total = q["price"] * int(pr["quantity"])
            conn.execute("""
                INSERT INTO quotations
                (rfq_number, vendor_code, vendor_name, unit_price,
                 lead_time, payment_terms, total_value, status)
                VALUES (?,?,?,?,?,?,?,?)
            """, (rfq_num, v, VENDORS[v]["name"],
                  q["price"], q["lead"], q["terms"], total, "Received"))

        conn.commit()
        conn.close()
        flash(f"✅ {rfq_num} dispatched to {len(vendors_selected)} vendors.", "success")
        return redirect(url_for("rfq"))

    approved_pr = get_db().execute(
        "SELECT * FROM purchase_requisitions WHERE status='Approved' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    rfqs = get_all("rfqs")
    return render_template("rfq.html", approved_pr=approved_pr,
                           vendors=VENDORS, rfqs=rfqs, today=today())


# ── STEP 3: PRICE COMPARISON ──────────────────────────────────────────────
@app.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "POST":
        selected_vendor = request.form["selected_vendor"]
        rfq_number = request.form["rfq_number"]
        conn = get_db()
        # mark selected
        conn.execute("UPDATE quotations SET status='Selected' WHERE rfq_number=? AND vendor_code=?",
                     (rfq_number, selected_vendor))
        # reject others
        conn.execute("UPDATE quotations SET status='Rejected' WHERE rfq_number=? AND vendor_code!=?",
                     (rfq_number, selected_vendor))
        conn.commit()
        conn.close()
        flash(f"✅ {selected_vendor} selected. Others rejected.", "success")
        return redirect(url_for("compare"))

    latest_rfq = get_db().execute("SELECT * FROM rfqs ORDER BY id DESC LIMIT 1").fetchone()
    quotes = []
    if latest_rfq:
        quotes = get_db().execute(
            "SELECT * FROM quotations WHERE rfq_number=? ORDER BY unit_price ASC",
            (latest_rfq["rfq_number"],)
        ).fetchall()

    return render_template("compare.html", latest_rfq=latest_rfq, quotes=quotes)


# ── STEP 4: PURCHASE ORDER ────────────────────────────────────────────────
@app.route("/po", methods=["GET", "POST"])
def purchase_order():
    if request.method == "POST":
        # get selected quote
        conn = get_db()
        selected = conn.execute(
            "SELECT * FROM quotations WHERE status='Selected' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        pr = conn.execute(
            "SELECT * FROM purchase_requisitions WHERE status='Approved' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        rfq = conn.execute("SELECT * FROM rfqs ORDER BY id DESC LIMIT 1").fetchone()

        if not selected:
            flash("⚠️ No vendor selected yet. Complete Price Comparison first.", "warning")
            return redirect(url_for("purchase_order"))

        po_num = next_num("purchase_orders", "po_number", "PO")
        total = selected["unit_price"] * int(pr["quantity"])

        conn.execute("""
            INSERT INTO purchase_orders
            (po_number, pr_number, rfq_number, vendor_code, vendor_name,
             material_code, material_desc, quantity, unit_price, total_value,
             plant, storage_location, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (po_num, pr["pr_number"], rfq["rfq_number"],
              selected["vendor_code"], selected["vendor_name"],
              pr["material_code"], pr["material_desc"],
              pr["quantity"], selected["unit_price"], total,
              pr["plant"], "SL01", "Released", now()))
        conn.commit()
        conn.close()
        flash(f"✅ {po_num} released to {selected['vendor_name']}.", "success")
        return redirect(url_for("purchase_order"))

    pos = get_all("purchase_orders")
    selected_quote = get_db().execute(
        "SELECT * FROM quotations WHERE status='Selected' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    pr = get_db().execute(
        "SELECT * FROM purchase_requisitions WHERE status='Approved' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return render_template("po.html", pos=pos,
                           selected_quote=selected_quote, pr=pr)


# ── STEP 5: GOODS RECEIPT ─────────────────────────────────────────────────
@app.route("/gr", methods=["GET", "POST"])
def goods_receipt():
    if request.method == "POST":
        latest_po = get_db().execute(
            "SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not latest_po:
            flash("⚠️ No Purchase Order found.", "warning")
            return redirect(url_for("goods_receipt"))

        gr_num = next_num("goods_receipts", "gr_number", "GR")
        conn = get_db()
        conn.execute("""
            INSERT INTO goods_receipts
            (gr_number, po_number, material_code, quantity_received,
             plant, storage_location, movement_type, quality_status, posted_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (gr_num, latest_po["po_number"], latest_po["material_code"],
              request.form["quantity_received"],
              latest_po["plant"], latest_po["storage_location"],
              "101", request.form["quality_status"], now()))
        conn.commit()
        conn.close()
        flash(f"✅ {gr_num} posted. Stock updated in {latest_po['storage_location']}.", "success")
        return redirect(url_for("goods_receipt"))

    grs = get_all("goods_receipts")
    latest_po = get_db().execute(
        "SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return render_template("gr.html", grs=grs, latest_po=latest_po)


# ── STEP 6: INVOICE VERIFICATION ─────────────────────────────────────────
@app.route("/invoice", methods=["GET", "POST"])
def invoice():
    if request.method == "POST":
        conn = get_db()
        latest_po = conn.execute(
            "SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 1"
        ).fetchone()
        latest_gr = conn.execute(
            "SELECT * FROM goods_receipts ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if not latest_po or not latest_gr:
            flash("⚠️ Complete PO and GR steps first.", "warning")
            return redirect(url_for("invoice"))

        inv_num = next_num("invoices", "invoice_number", "INV")
        entered_amount = float(request.form["amount"])
        po_value = latest_po["total_value"]

        # 3-way match logic
        match_status = "Passed" if abs(entered_amount - po_value) < 1 else "Failed"
        status = "Approved" if match_status == "Passed" else "On Hold"

        conn.execute("""
            INSERT INTO invoices
            (invoice_number, vendor_invoice_ref, po_number, gr_number,
             vendor_code, vendor_name, amount, po_value,
             match_status, status, posted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (inv_num, request.form["vendor_invoice_ref"],
              latest_po["po_number"], latest_gr["gr_number"],
              latest_po["vendor_code"], latest_po["vendor_name"],
              entered_amount, po_value,
              match_status, status, now()))
        conn.commit()
        conn.close()

        if match_status == "Passed":
            flash(f"✅ {inv_num} — 3-Way Match PASSED. Invoice Approved.", "success")
        else:
            flash(f"❌ {inv_num} — 3-Way Match FAILED. Invoice On Hold.", "danger")
        return redirect(url_for("invoice"))

    invoices = get_all("invoices")
    latest_po = get_db().execute(
        "SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 1"
    ).fetchone()
    latest_gr = get_db().execute(
        "SELECT * FROM goods_receipts ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return render_template("invoice.html", invoices=invoices,
                           latest_po=latest_po, latest_gr=latest_gr)


# ── STEP 7: PAYMENT ───────────────────────────────────────────────────────
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if request.method == "POST":
        conn = get_db()
        latest_inv = conn.execute(
            "SELECT * FROM invoices WHERE match_status='Passed' ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if not latest_inv:
            flash("⚠️ No approved invoice found. Complete Invoice Verification first.", "warning")
            return redirect(url_for("payment"))

        pay_num = next_num("payments", "payment_number", "PAY")
        conn.execute("""
            INSERT INTO payments
            (payment_number, invoice_number, vendor_code, vendor_name,
             amount, payment_method, payment_date, status)
            VALUES (?,?,?,?,?,?,?,?)
        """, (pay_num, latest_inv["invoice_number"],
              latest_inv["vendor_code"], latest_inv["vendor_name"],
              latest_inv["amount"], request.form["payment_method"],
              today(), "Completed"))
        conn.execute(
            "UPDATE invoices SET status='Paid' WHERE id=?", (latest_inv["id"],)
        )
        conn.commit()
        conn.close()
        flash(f"✅ {pay_num} — ₹{latest_inv['amount']:,.0f} paid to {latest_inv['vendor_name']}.", "success")
        return redirect(url_for("payment"))

    payments = get_all("payments")
    latest_inv = get_db().execute(
        "SELECT * FROM invoices WHERE match_status='Passed' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return render_template("payment.html", payments=payments, latest_inv=latest_inv)


# ── VENDOR MASTER ─────────────────────────────────────────────────────────
@app.route("/vendors")
def vendors():
    return render_template("vendors.html", vendors=VENDORS, prices=QUOTE_PRICES)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)