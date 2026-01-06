import os
import pymysql


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


STATUS_LABELS = {
    "todo": "Do zrobienia",
    "in_progress": "W trakcie",
    "done": "Zrobione",
}


def list_tasks_with_attachments(*, user_id: int, group: str | None = None):
    """
    Zwraca listę tasków jako dicty:
    {
      id, title, description, group, status, created_at,
      status_label,
      attachments: [ {id, filename, file_url, object_key, created_at}, ... ]
    }
    """
    conn = _conn()
    try:
        with conn.cursor() as cur:
            if group:
                cur.execute(
                    """
                    SELECT
                      t.id, t.user_id, t.title, t.description, t.`group`, t.status, t.created_at,
                      a.id AS att_id, a.filename AS att_filename, a.file_url AS att_file_url,
                      a.object_key AS att_object_key, a.created_at AS att_created_at
                    FROM tasks t
                    LEFT JOIN attachments a ON a.task_id = t.id
                    WHERE t.user_id = %s AND t.`group` = %s
                    ORDER BY t.created_at DESC, t.id DESC, a.created_at DESC
                    """,
                    (user_id, group),
                )
            else:
                cur.execute(
                    """
                    SELECT
                      t.id, t.user_id, t.title, t.description, t.`group`, t.status, t.created_at,
                      a.id AS att_id, a.filename AS att_filename, a.file_url AS att_file_url,
                      a.object_key AS att_object_key, a.created_at AS att_created_at
                    FROM tasks t
                    LEFT JOIN attachments a ON a.task_id = t.id
                    WHERE t.user_id = %s
                    ORDER BY t.created_at DESC, t.id DESC, a.created_at DESC
                    """,
                    (user_id,),
                )

            rows = cur.fetchall()

        tasks_by_id = {}
        for r in rows:
            tid = r["id"]
            if tid not in tasks_by_id:
                tasks_by_id[tid] = {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "title": r["title"],
                    "description": r["description"],
                    "group": r["group"],
                    "status": r["status"],
                    "status_label": STATUS_LABELS.get(r["status"], r["status"]),
                    "created_at": r["created_at"],
                    "attachments": [],
                }

            if r.get("att_id"):
                tasks_by_id[tid]["attachments"].append(
                    {
                        "id": r["att_id"],
                        "filename": r["att_filename"],
                        "file_url": r["att_file_url"],
                        "object_key": r["att_object_key"],
                        "created_at": r["att_created_at"],
                    }
                )

        return list(tasks_by_id.values())
    finally:
        conn.close()
