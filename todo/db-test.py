import MySQLdb

conn = MySQLdb.connect(
    host="mysql-2ff27ce1-o891d5a71.database.cloud.ovh.net",
    port=20184,
    user="avnadmin",
    passwd="URscYQa5vP7boBS98q2p",
    db="defaultdb",
    ssl={"ssl-mode": "REQUIRED"},
)

cursor = conn.cursor()

# --- TABELA USER ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# --- TABELA TASK ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# --- DODAJ USERA ---
cursor.execute(
    "INSERT INTO users (email) VALUES (%s)",
    ("konrad@fomo.pl",)
)
user_id = cursor.lastrowid
print("✅ Dodano usera, ID:", user_id)

# --- DODAJ TASK ---
cursor.execute(
    "INSERT INTO tasks (user_id, title, status) VALUES (%s, %s, %s)",
    (user_id, "Pierwsze zadanie", "todo")
)

task_id = cursor.lastrowid
print("✅ Dodano task, ID:", task_id)

conn.commit()
cursor.close()
conn.close()
