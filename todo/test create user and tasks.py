from pathlib import Path
from datetime import datetime

import boto3
import pymysql


# =========================
# 1) KONFIGURACJA DB (OVH MySQL)
# =========================
DB_HOST = "mysql-2ff27ce1-o891d5a71.database.cloud.ovh.net"
DB_PORT = 20184
DB_USER = "avnadmin"
DB_PASSWORD = "URscYQa5vP7boBS98q2p"
DB_NAME = "defaultdb"

# OVH Managed MySQL wymaga SSL
DB_SSL = {"ssl": {}}


# =========================
# 2) KONFIGURACJA OVH OBJECT STORAGE (S3)
# =========================
S3_ENDPOINT = "https://s3.waw.io.cloud.ovh.net"   # masz to u siebie
S3_BUCKET = "fomo-storage"                        # <-- wpisz swoją nazwę bucketa
S3_ACCESS_KEY = "be7556864e6c40c0bc8f9e4f25aba2e5"
S3_SECRET_KEY = "fd1d9197890b46d98b8c8cb71e5c83ea"


# =========================
# 3) WEJŚCIOWE PLIKI (lokalne)
# =========================
FILE_1 = Path(r"C:\Users\Konrad H\Downloads\gerfgwergfwger.jpg")
FILE_2 = Path(r"C:\Users\Konrad H\Downloads\17695159_297.pdf")

# Przypomnienie: 6 stycznia 2026 (ustawiam 09:00)
REMIND_AT = datetime(2026, 1, 6, 9, 0, 0)


def make_public_url(bucket: str, endpoint: str, object_key: str) -> str:
    # OVH S3: https://{bucket}.s3.waw.io.cloud.ovh.net/{object_key}
    host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{bucket}.{host}/{object_key}"


def main():
    # --- walidacja plików ---
    if not FILE_1.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {FILE_1}")
    if not FILE_2.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {FILE_2}")

    # --- connect: MySQL ---
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl=DB_SSL,
        connect_timeout=15,
        read_timeout=30,
        write_timeout=30,
        charset="utf8mb4",
        autocommit=False,
    )

    # --- connect: S3 ---
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        endpoint_url=S3_ENDPOINT,
    )

    try:
        with conn.cursor() as cur:
            # =========================
            # 1) TABELKI (demo) – jeśli nie istnieją
            # =========================
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                remind_at DATETIME NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                object_key VARCHAR(1024) NOT NULL,
                file_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # =========================
            # 2) USER
            # =========================
            user_email = "konrad.demo@fomo.local"
            cur.execute("INSERT INTO users (email) VALUES (%s)", (user_email,))
            user_id = cur.lastrowid
            print(f"✅ User utworzony: {user_email} (id={user_id})")

            # =========================
            # 3) 3 TASKI (3 statusy)
            # =========================
            tasks_data = [
                ("Zadanie 1 (przypomnienie 6.01.2026)", "todo", REMIND_AT),
                ("Zadanie 2 (ma PDF)", "doing", None),
                ("Zadanie 3", "done", None),
            ]

            task_ids = []
            for title, status, remind_at in tasks_data:
                cur.execute(
                    "INSERT INTO tasks (user_id, title, status, remind_at) VALUES (%s, %s, %s, %s)",
                    (user_id, title, status, remind_at),
                )
                task_ids.append(cur.lastrowid)

            print(f"✅ Dodano taski: {task_ids}")

            # =========================
            # 4) Upload 2 plików do 2 zadań + zapis linków w DB
            # =========================
            uploads = [
                (task_ids[0], FILE_1),  # jpg do task 1
                (task_ids[1], FILE_2),  # pdf do task 2
            ]

            for task_id, local_file in uploads:
                object_key = f"uploads/user_{user_id}/task_{task_id}/{local_file.name}"

                # upload
                s3.upload_file(str(local_file), S3_BUCKET, object_key)

                file_url = make_public_url(S3_BUCKET, S3_ENDPOINT, object_key)

                # zapis do DB
                cur.execute(
                    "INSERT INTO attachments (task_id, filename, object_key, file_url) VALUES (%s, %s, %s, %s)",
                    (task_id, local_file.name, object_key, file_url),
                )

                print(f"✅ Plik wrzucony + zapisany w DB: task_id={task_id}")
                print(f"   key={object_key}")
                print(f"   url={file_url}")

        conn.commit()
        print("🎉 GOTOWE: user + 3 taski + 2 załączniki (OSS) + linki w DB")

    except Exception as e:
        conn.rollback()
        print("❌ Błąd – rollback. Szczegóły:", repr(e))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
