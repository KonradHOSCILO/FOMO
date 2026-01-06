import os
import pymysql

def get_conn():
    return pymysql.connect(
        host=os.getenv("OVH_DB_HOST"),
        port=int(os.getenv("OVH_DB_PORT", "20184")),
        user=os.getenv("OVH_DB_USER"),
        password=os.getenv("OVH_DB_PASSWORD"),
        database=os.getenv("OVH_DB_NAME", "defaultdb"),
        ssl={"ssl-mode": os.getenv("OVH_DB_SSL_MODE", "REQUIRED")},
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=15,
        read_timeout=30,
        write_timeout=30,
        cursorclass=pymysql.cursors.DictCursor,
    )
