import os
import uuid
import re
import boto3
from botocore.client import Config

S3_ENDPOINT = os.environ["S3_ENDPOINT"]
S3_BUCKET = os.environ["S3_BUCKET"]

def safe_object_key(*, user_id: int, task_id: int, filename: str) -> str:
    name = filename or "file"
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    token = uuid.uuid4().hex[:10]
    return f"uploads/user_{user_id}/task_{task_id}/{token}_{name}"

def _client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
    )

def make_bucket_public_read() -> None:
    """
    Jednorazowo – ustawia bucket ACL na public-read.
    """
    s3 = _client()
    s3.put_bucket_acl(Bucket=S3_BUCKET, ACL="public-read")

def upload_fileobj(*, fileobj, object_key: str, content_type: str | None = None) -> str:
    s3 = _client()

    extra = {
        "ACL": "public-read",
    }
    if content_type:
        extra["ContentType"] = content_type

    s3.upload_fileobj(fileobj, S3_BUCKET, object_key, ExtraArgs=extra)

    return f"https://{S3_BUCKET}.s3.waw.io.cloud.ovh.net/{object_key}"
