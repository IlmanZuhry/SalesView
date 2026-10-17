
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

from extract import extract_data
from transform import transform_data

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

BATCH_SIZE = 5000


def clean_value(value):
    """Mengubah nilai pandas/numpy menjadi nilai Python yang kompatibel."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    return value


def run_etl():
    started_at = datetime.now(timezone.utc)
    start_time = time.perf_counter()
    status = "failed"
    rows_loaded = 0
    error_message = None

    try:
        # 1. Extract
        print("\n=== EXTRACT ===")
        raw_df = extract_data()

        # 2. Transform
        print("\n=== TRANSFORM ===")
        clean_df = transform_data(raw_df)

        # Siapkan data untuk PostgreSQL
        columns = [
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
            "Revenue",
        ]

        clean_df = clean_df[columns]

        rows = (
            tuple(clean_value(value) for value in row)
            for row in clean_df.itertuples(index=False, name=None)
        )

        # 3. Load ke PostgreSQL
        print("\n=== LOAD POSTGRESQL ===")

        pg_config = {
            "host": os.getenv("PGHOST", "localhost"),
            "port": int(os.getenv("PGPORT", "5432")),
            "dbname": os.getenv("PGDATABASE", "salesview_db"),
            "user": os.getenv("PGUSER", "postgres"),
            "password": os.getenv("PGPASSWORD"),
        }

        insert_sql = """
            INSERT INTO sales_transactions (
                invoice_no, stock_code, description, quantity,
                invoice_date, unit_price, customer_id, country, revenue
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        with psycopg.connect(**pg_config) as conn:
            with conn.cursor() as cur:
                # Full reload: hapus data lama hanya dalam transaksi ini.
                cur.execute("TRUNCATE TABLE sales_transactions RESTART IDENTITY")

                batch = []

                for row in rows:
                    batch.append(row)

                    if len(batch) >= BATCH_SIZE:
                        cur.executemany(insert_sql, batch)
                        rows_loaded += len(batch)
                        print(f"Data dimuat: {rows_loaded:,}")
                        batch.clear()

                if batch:
                    cur.executemany(insert_sql, batch)
                    rows_loaded += len(batch)

            # Perubahan dikomit saat koneksi ditutup normal.
            # Jika terjadi error, transaksi akan dibatalkan.

        status = "success"
        print(f"\nETL berhasil! Total data dimuat: {rows_loaded:,}")

    except Exception as exc:
        error_message = str(exc)
        print("\nETL gagal!")
        print(f"Detail: {error_message}")

    finally:
        duration_seconds = round(time.perf_counter() - start_time, 2)

        # 4. Catat hasil proses ke MongoDB
        log_document = {
            "event": "etl_run",
            "status": status,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_seconds,
            "rows_loaded": rows_loaded,
            "error": error_message,
        }

        try:
            mongo_uri = os.getenv(
                "MONGO_URI", "mongodb://localhost:27017/"
            )
            mongo_db = os.getenv("MONGO_DB", "salesview")

            with MongoClient(
                mongo_uri, serverSelectionTimeoutMS=5000
            ) as client:
                client.admin.command("ping")
                client[mongo_db]["etl_logs"].insert_one(log_document)

            print("Log ETL berhasil disimpan ke MongoDB.")
        except Exception as exc:
            print(f"Gagal menyimpan log MongoDB: {exc}")

        print(f"Status          : {status}")
        print(f"Durasi          : {duration_seconds} detik")
        print(f"Jumlah data     : {rows_loaded:,}")


if __name__ == "__main__":
    run_etl()
