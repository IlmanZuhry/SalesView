
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_DIR / "data" / "Online_Retail.xlsx"


def extract_data():
    """Membaca dataset Excel dan menampilkan informasi dasarnya."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {DATA_PATH}"
        )

    df = pd.read_excel(DATA_PATH)

    print("Dataset berhasil dibaca!")
    print(f"Jumlah baris   : {len(df):,}")
    print(f"Jumlah kolom   : {len(df.columns)}")
    print(f"Nama kolom     : {list(df.columns)}")
    print("\nLima baris pertama:")
    print(df.head())

    return df


if __name__ == "__main__":
    extract_data()
