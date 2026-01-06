import os
import pymysql

def _conn():
    host = os.environ["OVH_MYSQL_HOST"]
    port = int(os.environ.get("OVH_MYSQL_PORT", "20184"))
    user = os.environ["OVH_MYSQL_USER"]
    password = os.environ["OVH_MYSQL_PASSWORD"]
    db = os.environ["OVH_MYSQL_DB"]

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        ssl={"ssl-mode": "REQUIRED"},
    )


def ensure_ovh_user(django_user_id: int, email: str, password_hash: str):
    """
    Zakładam, że w OVH masz tabelę `users` gdzie id jest INT.
    Chcemy żeby OVH users.id == Django user.id (żeby FK działał prosto).
    """
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id=%s LIMIT 1", (django_user_id,))
            row = cur.fetchone()
            if row:
                return

            cur.execute(
                """
                INSERT INTO users (id, mail, password_hash, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (django_user_id, email, password_hash),
            )
    finally:
        conn.close()
