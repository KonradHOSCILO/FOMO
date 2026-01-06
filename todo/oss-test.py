import pymysql
import logging
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

@contextmanager
def db_cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()

def exec_sql(cur, sql: str):
    one_line = " ".join(line.strip() for line in sql.strip().splitlines() if line.strip())
    logging.info("SQL -> %s", (one_line[:180] + ("..." if len(one_line) > 180 else "")))
    cur.execute(sql)

def exec_many(cur, statements):
    for s in statements:
        exec_sql(cur, s)

def main():
    conn = pymysql.connect(
        host="mysql-2ff27ce1-o891d5a71.database.cloud.ovh.net",
        port=20184,
        user="avnadmin",
        password="URscYQa5vP7boBS98q2p",
        database="defaultdb",
        ssl={"ssl": {}},
        charset="utf8mb4",
        autocommit=False,
    )

    logging.info("Połączono z MySQL (%s:%s) db=%s", conn.host, conn.port, conn.db)

    statements = [
        "SET FOREIGN_KEY_CHECKS = 0;",
        "DROP TABLE IF EXISTS attachments;",
        "DROP TABLE IF EXISTS tasks;",
        "DROP TABLE IF EXISTS task_groups;",
        "DROP TABLE IF EXISTS users;",
        "SET FOREIGN_KEY_CHECKS = 1;",

        """
        CREATE TABLE users (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          mail VARCHAR(255) NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_users_mail (mail)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,

        """
        CREATE TABLE task_groups (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          user_id BIGINT UNSIGNED NOT NULL,
          name VARCHAR(80) NOT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_group_user_name (user_id, name),
          KEY idx_group_user (user_id),
          CONSTRAINT fk_groups_user
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE CASCADE
            ON UPDATE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,

        """
        CREATE TABLE tasks (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          user_id BIGINT UNSIGNED NOT NULL,
          group_id BIGINT UNSIGNED NULL,

          title VARCHAR(255) NOT NULL,
          description TEXT NULL,

          status ENUM('todo','in_progress','done','archived') NOT NULL DEFAULT 'todo',

          -- data/czas przypomnienia (jednorazowo)
          remind_at DATETIME NULL,

          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

          PRIMARY KEY (id),
          KEY idx_tasks_user (user_id),
          KEY idx_tasks_group (group_id),
          KEY idx_tasks_remind (remind_at),

          CONSTRAINT fk_tasks_user
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE CASCADE
            ON UPDATE RESTRICT,
          CONSTRAINT fk_tasks_group
            FOREIGN KEY (group_id) REFERENCES task_groups(id)
            ON DELETE SET NULL
            ON UPDATE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,


        """
        CREATE TABLE attachments (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          task_id BIGINT UNSIGNED NOT NULL,

          filename VARCHAR(255) NOT NULL,
          object_key VARCHAR(1024) NOT NULL,
          file_url TEXT NULL,

          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

          PRIMARY KEY (id),
          KEY idx_att_task (task_id),

          CONSTRAINT fk_att_task
            FOREIGN KEY (task_id) REFERENCES tasks(id)
            ON DELETE CASCADE
            ON UPDATE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
    ]

    try:
        with db_cursor(conn) as cur:
            logging.info("Start: reset schematu (DROP + CREATE)")
            exec_many(cur, statements)

        conn.commit()
        logging.info("OK: commit wykonany")

        with db_cursor(conn) as cur:
            exec_sql(cur, "SHOW TABLES;")
            tables = [row[0] for row in cur.fetchall()]
            logging.info("Tabele w bazie: %s", tables)

    except Exception as e:
        logging.exception("Błąd! Rollback. Powód: %s", e)
        conn.rollback()
        raise
    finally:
        conn.close()
        logging.info("Połączenie zamknięte")

if __name__ == "__main__":
    main()
