
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_DIR / "data" / "Online_Retail.xlsx"


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Membersihkan data dan menyiapkan data untuk analisis penjualan."""

    initial_rows = len(df)

    # Hapus baris duplikat
    df = df.drop_duplicates().copy()

    # Hapus baris tanpa informasi penting untuk transaksi
    required_columns = [
        "InvoiceNo",
        "StockCode",
        "InvoiceDate",
        "Quantity",
        "UnitPrice",
    ]
    df = df.dropna(subset=required_columns).copy()

    # Pastikan tipe data sesuai
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"], errors="coerce"
    )
    df["Quantity"] = pd.to_numeric(
        df["Quantity"], errors="coerce"
    )
    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"], errors="coerce"
    )

    # Hapus nilai yang gagal dikonversi
    df = df.dropna(
        subset=["InvoiceDate", "Quantity", "UnitPrice"]
    ).copy()

    # Keluarkan invoice pembatalan (biasanya diawali huruf C)
    df = df[
        ~df["InvoiceNo"].str.upper().str.startswith("C")
    ].copy()

    # Ambil transaksi penjualan dengan kuantitas dan harga positif
    df = df[
        (df["Quantity"] > 0) &
        (df["UnitPrice"] > 0)
    ].copy()

    # Bersihkan teks, tetapi pertahankan nilai kosong sebagai None
    df["Description"] = df["Description"].astype("string").str.strip()
    df["Description"] = df["Description"].replace("", pd.NA)

    # CustomerID sering kosong; jangan menghapus transaksi hanya karena ini
    df["CustomerID"] = pd.to_numeric(
        df["CustomerID"], errors="coerce"
    ).astype("Int64")

    df["Country"] = df["Country"].astype("string").str.strip()

    # Tambahkan nilai pendapatan per baris
    df["Revenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    # Pastikan hasil perhitungan valid
    df = df[df["Revenue"] > 0].copy()

    # Buat indeks baru
    df = df.reset_index(drop=True)

    print("Transformasi selesai!")
    print(f"Baris awal             : {initial_rows:,}")
    print(f"Baris setelah dibersihkan: {len(df):,}")
    print(f"Baris yang dikeluarkan : {initial_rows - len(df):,}")
    print(f"Total revenue          : {df['Revenue'].sum():,.2f}")
    print(f"CustomerID kosong      : {df['CustomerID'].isna().sum():,}")
    print(f"Description kosong     : {df['Description'].isna().sum():,}")

    return df


if __name__ == "__main__":
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATA_PATH}")

    raw_df = pd.read_excel(DATA_PATH)
    clean_df = transform_data(raw_df)
