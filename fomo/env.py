from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent

env_path = BASE_DIR / ".env"
print("ENV PATH:", env_path)
print("EXISTS:", env_path.exists())

load_dotenv(env_path)

keys = [
    "OVH_MYSQL_HOST",
    "OVH_MYSQL_PORT",
    "OVH_MYSQL_USER",
    "OVH_MYSQL_PASSWORD",
    "OVH_MYSQL_DB",
    "S3_ENDPOINT",
    "S3_BUCKET",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
]

for key in keys:
    print(f"{key} = {os.getenv(key)}")