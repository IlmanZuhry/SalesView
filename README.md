# SalesView — Dasbor Analitik Penjualan

SalesView adalah aplikasi web analitik penjualan yang dirancang untuk mengolah, menyimpan, dan menyajikan data transaksi penjualan melalui dasbor interaktif. Proyek ini menerapkan arsitektur **Hybrid Database** dengan menggabungkan PostgreSQL sebagai basis data relasional dan MongoDB sebagai penyimpanan log proses ETL.

Aplikasi menggunakan dataset historis **Online Retail** untuk menampilkan ringkasan penjualan, tren pendapatan, produk teratas, serta distribusi pendapatan berdasarkan negara.

## Fitur Utama

- **Dasbor Analitik:** Menampilkan ringkasan metrik penjualan dalam bentuk kartu statistik dan grafik.
- **Filter Data:** Memfilter data berdasarkan negara dan rentang tanggal transaksi.
- **Pengurutan Data:** Mengurutkan hasil analisis berdasarkan pendapatan, tanggal transaksi, atau jumlah barang terjual.
- **Visualisasi Penjualan:** Menampilkan tren pendapatan bulanan, produk teratas, dan pendapatan berdasarkan negara.
- **Pembaruan Otomatis:** Memperbarui tampilan dasbor secara berkala setiap 30 detik.
- **ETL Pipeline:** Melakukan ekstraksi, transformasi, dan pemuatan data transaksi ke PostgreSQL.
- **Pencatatan Log ETL:** Menyimpan status, durasi, dan jumlah baris yang diproses ke MongoDB.

> **Catatan:** Pembaruan dasbor dilakukan secara berkala dari database. Data yang digunakan berasal dari dataset historis, bukan transaksi penjualan langsung.

## Arsitektur Sistem

SalesView menggunakan dua jenis basis data dengan fungsi yang berbeda.

| Komponen | Fungsi |
|---|---|
| Python ETL | Mengekstrak dan membersihkan data transaksi sebelum dimuat ke database. |
| PostgreSQL | Menyimpan data transaksi penjualan yang telah diproses. |
| MongoDB | Menyimpan log pengujian koneksi dan eksekusi ETL. |
| Flask | Menyediakan backend dan REST API untuk mengambil data dari PostgreSQL. |
| HTML, CSS, JavaScript | Membangun antarmuka dasbor interaktif. |
| Chart.js | Memvisualisasikan data analitik dalam bentuk grafik. |

Alur pemrosesan data:

```text
Dataset Online Retail
        |
        v
   ETL Pipeline
        |
        v
    PostgreSQL
        |
        v
    Flask REST API
        |
        v
  Dashboard SalesView

ETL Pipeline ------> MongoDB
                     ETL Logs
```

## Teknologi yang Digunakan

- Python
- Flask
- PostgreSQL
- MongoDB
- Pandas
- HTML5
- CSS3
- JavaScript
- Chart.js
- python-dotenv
- psycopg

## Struktur Proyek

```text
SalesView/
├── backend/
│   └── app.py
├── dashboard/
│   └── app.py
├── data/
│   └── Online_Retail.xlsx
├── etl/
│   ├── run_etl.py
│   └── test_mongo.py
├── frontend/
│   ├── assets/
│   │   └── Logo_SV.png
│   ├── index.html
│   ├── style.css
│   └── dashboard.js
├── .env
├── .gitignore
├── requirement.txt
└── README.md
```

Struktur di atas merupakan gambaran proyek. Nama file dan folder dapat disesuaikan dengan struktur aktual repository.

## Persyaratan Sistem

Pastikan perangkat telah memiliki:

- Python dan pip
- PostgreSQL
- MongoDB
- Git
- Browser web modern

## Instalasi dan Konfigurasi

### 1. Clone Repository

```bash
git clone https://github.com/IlmanZuhry/SalesView.git
cd SalesView
```

### 2. Buat Virtual Environment

```bash
python -m venv .venv
```

Aktifkan virtual environment di Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Jika menggunakan Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 3. Instal Dependensi

Pastikan file dependensi bernama `requirement.txt`, kemudian jalankan:

```bash
pip install -r requirement.txt
```

### 4. Siapkan Database

Buat database PostgreSQL bernama `salesview_db`. Pastikan layanan PostgreSQL dan MongoDB berjalan.

Buat file `.env` di direktori utama proyek dengan konfigurasi berikut:

```env
PGHOST=localhost
PGPORT=5432
PGDATABASE=salesview_db
PGUSER=postgres
PGPASSWORD=your_postgresql_password

MONGO_URI=mongodb://localhost:27017/
MONGO_DB=salesview
```

Ganti `your_postgresql_password` dengan kata sandi PostgreSQL milik sendiri. Jangan mengunggah file `.env` atau kredensial database ke GitHub.

### 5. Siapkan Dataset dan Jalankan ETL

Tempatkan dataset Online Retail pada lokasi yang sesuai dengan konfigurasi ETL proyek, lalu jalankan:

```bash
python etl/run_etl.py
```

Proses ETL akan mengekstrak, membersihkan, dan memuat data transaksi ke PostgreSQL serta mencatat hasil eksekusinya ke MongoDB.

**Perhatian:** Skrip ETL saat ini melakukan pengosongan tabel transaksi sebelum memuat ulang data. Jangan menjalankannya kembali jika terdapat data yang ingin dipertahankan tanpa memahami dampaknya.

### 6. Jalankan Backend

Dari direktori utama proyek, jalankan:

```bash
python backend/app.py
```

Buka alamat berikut di browser:

http://127.0.0.1:5000/

## Endpoint API

| Endpoint | Fungsi |
|---|---|
| `/api/health` | Memeriksa koneksi backend ke PostgreSQL. |
| `/api/countries` | Mengambil daftar negara yang tersedia. |
| `/api/summary` | Mengambil ringkasan metrik penjualan. |
| `/api/revenue-monthly` | Mengambil data pendapatan bulanan. |
| `/api/top-products` | Mengambil daftar produk teratas. |
| `/api/top-countries` | Mengambil daftar negara berdasarkan hasil penjualan. |

Endpoint analitik mendukung parameter filter yang relevan, seperti `country`, `start_date`, `end_date`, dan `sort`.

Contoh:

```text
/api/summary?start_date=2011-01-01&end_date=2011-03-31
```

## Hasil Pemrosesan Data

Berdasarkan proses ETL yang telah dijalankan:

- Baris data berhasil dimuat: **524.874**
- Durasi pemrosesan: sekitar **53,35 detik**
- Total pendapatan dalam dataset yang telah dibersihkan: **£10.642.110,80**

Angka tersebut merupakan hasil pemrosesan dataset historis dan dapat berubah apabila proses ETL atau dataset diperbarui.

## Keamanan dan Pengelolaan Data

- File `.env` tidak boleh diunggah ke repository publik.
- Dataset sumber yang dikecualikan oleh `.gitignore` perlu disiapkan secara terpisah ketika melakukan instalasi.
- Kredensial database harus disimpan melalui environment variables.
- Pastikan konfigurasi dan dependensi proyek sesuai dengan versi yang digunakan.

## Tujuan Proyek

Proyek ini dikembangkan untuk menerapkan integrasi basis data relasional dan NoSQL, proses ETL, pengembangan REST API, serta visualisasi data penjualan dalam satu aplikasi analitik berbasis web.

## Repository

GitHub: https://github.com/IlmanZuhry/SalesView
