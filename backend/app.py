
from pathlib import Path
from datetime import date, timedelta
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

SORT_OPTIONS = {"revenue", "date", "quantity", "country"}


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "salesview_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        row_factory=dict_row,
    )


def get_filters():
    country = request.args.get("country", "all").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort", "revenue").strip().lower()

    if sort_by not in SORT_OPTIONS:
        raise ValueError("Pilihan sort tidak valid.")

    if start_date:
        date.fromisoformat(start_date)

    if end_date:
        date.fromisoformat(end_date)

    if start_date and end_date and start_date > end_date:
        raise ValueError("Tanggal awal tidak boleh melewati tanggal akhir.")

    conditions = []
    params = []

    if country and country.lower() != "all":
        conditions.append("country = %s")
        params.append(country)

    if start_date:
        conditions.append("invoice_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("invoice_date < %s::date + INTERVAL '1 day'")
        params.append(end_date)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    return where_clause, params, sort_by


def fetch_all(query, params):
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchall()


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/health")
def health():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")

        return jsonify({
            "status": "success",
            "message": "Flask dan PostgreSQL terhubung."
        })
    except Exception:
        app.logger.exception("Pemeriksaan koneksi database gagal")
        return jsonify({
            "status": "error",
            "message": "Koneksi database gagal."
        }), 500


@app.route("/api/countries")
def countries():
    try:
        rows = fetch_all(
            """
            SELECT DISTINCT country
            FROM sales_transactions
            WHERE country IS NOT NULL
            ORDER BY country DESC
            """,
            [],
        )
        return jsonify({
            "status": "success",
            "data": [row["country"] for row in rows]
        })
    except Exception:
        app.logger.exception("Gagal mengambil daftar negara")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil daftar negara."
        }), 500


@app.route("/api/summary")
def summary():
    try:
        where, params, _ = get_filters()

        query = f"""
            SELECT
                COALESCE(SUM(revenue), 0) AS total_revenue,
                COUNT(DISTINCT invoice_no) AS total_invoices,
                COUNT(DISTINCT customer_id) AS total_customers,
                COALESCE(SUM(quantity), 0) AS units_sold
            FROM sales_transactions
            {where}
        """

        rows = fetch_all(query, params)

        return jsonify({"status": "success", "data": rows[0]})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Gagal mengambil ringkasan penjualan")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil ringkasan penjualan."
        }), 500


@app.route("/api/revenue-monthly")
def revenue_monthly():
    try:
        where, params, sort_by = get_filters()

        # Tren bulanan secara default tetap kronologis.
        order_by = {
            "revenue": "revenue DESC, month DESC",
            "date": "month DESC",
            "quantity": "quantity DESC, month DESC",
            "country": "month DESC",
        }[sort_by]

        query = f"""
            SELECT
                TO_CHAR(DATE_TRUNC('month', invoice_date), 'YYYY-MM') AS month,
                COALESCE(SUM(revenue), 0) AS revenue,
                COALESCE(SUM(quantity), 0) AS quantity
            FROM sales_transactions
            {where}
            GROUP BY DATE_TRUNC('month', invoice_date)
            ORDER BY {order_by}
        """

        rows = fetch_all(query, params)
        return jsonify({"status": "success", "data": rows})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Gagal mengambil tren pendapatan")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil tren pendapatan."
        }), 500


@app.route("/api/top-products")
def top_products():
    try:
        where, params, sort_by = get_filters()

        order_by = {
            "revenue": "revenue DESC",
            "date": "latest_date DESC",
            "quantity": "quantity DESC",
            "country": "product DESC",
        }[sort_by]

        query = f"""
            SELECT
                COALESCE(description, stock_code) AS product,
                COALESCE(SUM(revenue), 0) AS revenue,
                COALESCE(SUM(quantity), 0) AS quantity,
                MAX(invoice_date) AS latest_date
            FROM sales_transactions
            {where}
            GROUP BY COALESCE(description, stock_code)
            ORDER BY {order_by}
            LIMIT 10
        """

        rows = fetch_all(query, params)
        return jsonify({"status": "success", "data": rows})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Gagal mengambil produk teratas")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil produk teratas."
        }), 500


@app.route("/api/top-countries")
def top_countries():
    try:
        where, params, sort_by = get_filters()

        order_by = {
            "revenue": "revenue DESC",
            "date": "latest_date DESC",
            "quantity": "quantity DESC",
            "country": "country DESC",
        }[sort_by]

        query = f"""
            SELECT
                country,
                COALESCE(SUM(revenue), 0) AS revenue,
                COALESCE(SUM(quantity), 0) AS quantity,
                MAX(invoice_date) AS latest_date
            FROM sales_transactions
            {where}
            GROUP BY country
            ORDER BY {order_by}
            LIMIT 10
        """

        rows = fetch_all(query, params)
        return jsonify({"status": "success", "data": rows})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Gagal mengambil negara teratas")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil negara teratas."
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
