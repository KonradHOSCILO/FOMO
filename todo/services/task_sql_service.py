import os
import pymysql
from datetime import datetime
from django.utils import timezone


from todo.services.oss import upload_fileobj, safe_object_key

def _conn():
    return pymysql.connect(
        host=os.environ["OVH_MYSQL_HOST"],
        port=int(os.environ["OVH_MYSQL_PORT"]),
        user=os.environ["OVH_MYSQL_USER"],
        password=os.environ["OVH_MYSQL_PASSWORD"],
        db=os.environ["OVH_MYSQL_DB"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl-mode": "REQUIRED"},
        autocommit=True,
    )

def get_tasks_sql(user_id: int):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, title, description, `group`, status, created_at, remind_at
                FROM tasks
                WHERE user_id=%s
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

def create_task_sql(*, user_id: int, title: str, description: str, group: str, status: str, upload=None) -> int:
    """
    Tworzy taska w OVH MySQL.
    Jeśli upload != None, wysyła plik do OVH S3 i zapisuje rekord w attachments.
    Zwraca task_id.
    """
    title = (title or "").strip()
    description = (description or "").strip() or None

    now = timezone.now()

    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (user_id, `group`, title, description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, group, title, description, status, now),
            )
            task_id = cur.lastrowid

            if upload:
                filename = getattr(upload, "name", "file")
                content_type = getattr(upload, "content_type", None)

                object_key = safe_object_key(user_id=user_id, task_id=task_id, filename=filename)

                file_url = upload_fileobj(fileobj=upload, object_key=object_key, content_type=content_type)

                cur.execute(
                    """
                    INSERT INTO attachments (task_id, filename, object_key, file_url, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (task_id, filename, object_key, file_url, now),
                )

        conn.commit()
        return task_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def update_task_sql(*, user_id: int, task_id: int, title: str, description: str, group: str, status: str) -> None:
    title = (title or "").strip()
    description = (description or "").strip() or None
    group = (group or "Ważne").strip()
    status = (status or "todo").strip()

    allowed = {"todo", "in_progress", "done"}
    if status not in allowed:
        status = "todo"

    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET title=%s, description=%s, `group`=%s, status=%s
                WHERE id=%s AND user_id=%s
                """,
                (title, description, group, status, task_id, user_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def delete_task_sql(*, user_id: int, task_id: int) -> None:
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tasks WHERE id=%s AND user_id=%s",
                (task_id, user_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
