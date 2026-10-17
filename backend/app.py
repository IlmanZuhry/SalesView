
from pathlib import Path

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory

# Lokasi folder proyek
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Membaca konfigurasi database dari .env
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)


def get_db_connection():
    """Membuat koneksi ke PostgreSQL."""
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "salesview_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        row_factory=dict_row,
    )


# Menampilkan halaman utama frontend
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# Melayani file CSS dan JavaScript
@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# Memeriksa koneksi aplikasi dan database
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


# Mengambil ringkasan penjualan
@app.route("/api/summary")
def summary():
    query = """
        SELECT
            COALESCE(SUM(revenue), 0) AS total_revenue,
            COUNT(DISTINCT invoice_no) AS total_invoices,
            COUNT(DISTINCT customer_id) AS total_customers,
            COALESCE(SUM(quantity), 0) AS units_sold
        FROM sales_transactions
    """

    try:
        with get_db_connection() as conn:
            result = conn.execute(query).fetchone()

        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception:
        app.logger.exception("Gagal mengambil ringkasan penjualan")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil ringkasan penjualan."
        }), 500


# Mengambil tren pendapatan bulanan
@app.route("/api/revenue-monthly")
def revenue_monthly():
    query = """
        SELECT
            TO_CHAR(
                DATE_TRUNC('month', invoice_date),
                'YYYY-MM'
            ) AS month,
            COALESCE(SUM(revenue), 0) AS revenue
        FROM sales_transactions
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY DATE_TRUNC('month', invoice_date)
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        return jsonify({"status": "success", "data": rows})
    except Exception:
        app.logger.exception("Gagal mengambil tren pendapatan")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil tren pendapatan."
        }), 500


# Mengambil 10 produk dengan pendapatan tertinggi
@app.route("/api/top-products")
def top_products():
    query = """
        SELECT
            COALESCE(description, stock_code) AS product,
            SUM(revenue) AS revenue
        FROM sales_transactions
        GROUP BY COALESCE(description, stock_code)
        ORDER BY revenue DESC
        LIMIT 10
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        return jsonify({"status": "success", "data": rows})
    except Exception:
        app.logger.exception("Gagal mengambil produk teratas")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil produk teratas."
        }), 500


# Mengambil 10 negara dengan pendapatan tertinggi
@app.route("/api/top-countries")
def top_countries():
    query = """
        SELECT
            country,
            SUM(revenue) AS revenue
        FROM sales_transactions
        GROUP BY country
        ORDER BY revenue DESC
        LIMIT 10
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        return jsonify({"status": "success", "data": rows})
    except Exception:
        app.logger.exception("Gagal mengambil negara teratas")
        return jsonify({
            "status": "error",
            "message": "Gagal mengambil negara teratas."
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
