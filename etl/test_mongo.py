
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
db_name = os.getenv("MONGO_DB", "salesview")

try:
    with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
        # Pastikan server MongoDB dapat diakses
        client.admin.command("ping")

        db = client[db_name]
        logs = db["etl_logs"]

        # Simpan satu log pengujian
        result = logs.insert_one({
            "event": "connection_test",
            "status": "success",
            "message": "Koneksi Python ke MongoDB berhasil",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        print("Koneksi MongoDB berhasil!")
        print(f"Database   : {db_name}")
        print(f"Collection : etl_logs")
        print(f"Log ID     : {result.inserted_id}")

except Exception as e:
    print("Koneksi MongoDB gagal.")
    print(f"Detail: {e}")
