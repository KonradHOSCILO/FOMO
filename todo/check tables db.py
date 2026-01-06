from datetime import datetime
import pymysql


def fmt_value(v):
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return v


def print_rows(label: str, rows: list[dict], limit: int = 50):
    print(f"\n=== {label} (count={len(rows)}) ===")
    for i, row in enumerate(rows[:limit], start=1):
        print(f"\n[{i}]")
        for k, v in row.items():
            print(f"  {k}: {fmt_value(v)}")
    if len(rows) > limit:
        print(f"\n... ucięte, pokazano {limit} z {len(rows)} rekordów")


conn = pymysql.connect(
    host="mysql-2ff27ce1-o891d5a71.database.cloud.ovh.net",
    port=20184,
    user="avnadmin",
    password="URscYQa5vP7boBS98q2p",
    database="defaultdb",
    ssl={"ssl": {}},
    charset="utf8mb4",
)

with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    print("=== TABELKI ===")
    for t in tables:
        print("-", next(iter(t.values())))

    cur.execute("SELECT COUNT(*) AS cnt FROM users;")
    print("\nusers:", cur.fetchone()["cnt"])

    cur.execute("SELECT COUNT(*) AS cnt FROM tasks;")
    print("tasks:", cur.fetchone()["cnt"])

    cur.execute("SELECT COUNT(*) AS cnt FROM attachments;")
    print("attachments:", cur.fetchone()["cnt"])

    cur.execute("SELECT * FROM users ORDER BY id DESC;")
    print_rows("USERS", cur.fetchall())

    cur.execute("SELECT * FROM tasks ORDER BY id DESC;")
    print_rows("TASKS", cur.fetchall())

    cur.execute("SELECT * FROM attachments ORDER BY id DESC;")
    print_rows("ATTACHMENTS", cur.fetchall())

    cur.execute("""
        SELECT
            u.id AS user_id, u.email, u.created_at,
            t.id AS task_id, t.title, t.status, t.remind_at, t.created_at AS task_created_at,
            a.id AS attachment_id, a.filename, a.object_key, a.file_url, a.created_at AS attachment_created_at
        FROM users u
        LEFT JOIN tasks t ON t.user_id = u.id
        LEFT JOIN attachments a ON a.task_id = t.id
        ORDER BY u.id DESC, t.id DESC, a.id DESC;
    """)
    print_rows("JOIN: users -> tasks -> attachments", cur.fetchall(), limit=200)

conn.close()
