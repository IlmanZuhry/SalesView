
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "salesview_db"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD"),
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sales_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(30) NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    customer_id BIGINT,
    country VARCHAR(100),
    revenue NUMERIC(14, 2) NOT NULL
);
"""

def setup_database():
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)

    print("Tabel sales_transactions berhasil disiapkan!")

if __name__ == "__main__":
    setup_database()
