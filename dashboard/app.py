
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from dotenv import load_dotenv

# Konfigurasi dasar
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

st.set_page_config(
    page_title="SalesView | Sales Analytics",
    page_icon="📊",
    layout="wide",
)

# Gaya dashboard
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background: #F0F5FA;
        border: 1px solid #D9E3EF;
        padding: 16px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_sales_data():
    """Mengambil data transaksi dari PostgreSQL."""
    config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "dbname": os.getenv("PGDATABASE", "salesview_db"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD"),
    }

    query = """
        SELECT
            invoice_no,
            stock_code,
            description,
            quantity,
            invoice_date,
            unit_price,
            customer_id,
            country,
            revenue
        FROM sales_transactions
        ORDER BY invoice_date
    """

    with psycopg.connect(**config) as conn:
        df = pd.read_sql_query(query, conn)

    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    return df


# Header
st.title("📊 SalesView")
st.caption("Sales Analytics Dashboard | Historical Online Retail Data")
st.divider()

# Ambil data
try:
    with st.spinner("Memuat data penjualan..."):
        df = load_sales_data()
except Exception as exc:
    st.error("Tidak dapat mengambil data dari PostgreSQL.")
    st.code(str(exc))
    st.stop()

if df.empty:
    st.warning("Belum ada transaksi. Jalankan proses ETL terlebih dahulu.")
    st.stop()

# Sidebar filter
st.sidebar.header("Filter Data")

min_date = df["invoice_date"].min().date()
max_date = df["invoice_date"].max().date()

date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

countries = sorted(df["country"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Negara",
    options=countries,
    default=countries,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = df[
        (df["invoice_date"].dt.date >= start_date)
        & (df["invoice_date"].dt.date <= end_date)
        & (df["country"].isin(selected_countries))
    ].copy()
else:
    filtered_df = df[
        df["country"].isin(selected_countries)
    ].copy()

if filtered_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# KPI
total_revenue = filtered_df["revenue"].sum()
total_invoices = filtered_df["invoice_no"].nunique()
total_customers = filtered_df["customer_id"].nunique()
total_units = filtered_df["quantity"].sum()

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Revenue", f"£{total_revenue:,.2f}")
k2.metric("Total Invoices", f"{total_invoices:,}")
k3.metric("Unique Customers", f"{total_customers:,}")
k4.metric("Units Sold", f"{total_units:,.0f}")

st.divider()

# Grafik tren pendapatan
st.subheader("Revenue Trend")

trend_df = (
    filtered_df.set_index("invoice_date")["revenue"]
    .resample("MS")
    .sum()
    .reset_index()
)

fig_trend = px.line(
    trend_df,
    x="invoice_date",
    y="revenue",
    markers=True,
    labels={
        "invoice_date": "Month",
        "revenue": "Revenue (£)",
    },
    template="plotly_white",
)

fig_trend.update_layout(
    margin=dict(l=10, r=10, t=20, b=10),
    hovermode="x unified",
)

st.plotly_chart(fig_trend, use_container_width=True)

# Analisis produk dan negara
left, right = st.columns(2)

with left:
    st.subheader("Top 10 Products by Revenue")

    product_df = (
        filtered_df.groupby("description", dropna=False)
        .agg(
            revenue=("revenue", "sum"),
            units_sold=("quantity", "sum"),
        )
        .reset_index()
    )

    product_df["description"] = (
        product_df["description"].fillna("Unknown")
    )

    product_df = product_df.nlargest(10, "revenue")
    product_df = product_df.sort_values("revenue", ascending=True)

    fig_product = px.bar(
        product_df,
        x="revenue",
        y="description",
        orientation="h",
        labels={
            "revenue": "Revenue (£)",
            "description": "Product",
        },
        template="plotly_white",
    )

    fig_product.update_layout(
        yaxis_title="",
        margin=dict(l=10, r=10, t=20, b=10),
    )

    st.plotly_chart(fig_product, use_container_width=True)

with right:
    st.subheader("Revenue by Country")

    country_df = (
        filtered_df.groupby("country", as_index=False)["revenue"]
        .sum()
        .nlargest(10, "revenue")
        .sort_values("revenue", ascending=True)
    )

    fig_country = px.bar(
        country_df,
        x="revenue",
        y="country",
        orientation="h",
        labels={
            "revenue": "Revenue (£)",
            "country": "Country",
        },
        template="plotly_white",
    )

    fig_country.update_layout(
        yaxis_title="",
        margin=dict(l=10, r=10, t=20, b=10),
    )

    st.plotly_chart(fig_country, use_container_width=True)

# Tabel data
with st.expander("Lihat Data Transaksi"):
    st.caption(f"Menampilkan {len(filtered_df):,} baris sesuai filter.")

    st.dataframe(
        filtered_df.sort_values(
            "invoice_date", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )

# Tombol refresh
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("Data diperbarui berdasarkan proses ETL terakhir.")
