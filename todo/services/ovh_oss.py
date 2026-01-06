import os
import boto3

def make_public_url(bucket: str, endpoint: str, object_key: str) -> str:
    host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{bucket}.{host}/{object_key}"

def upload_fileobj(uploaded_file, object_key: str) -> str:
    endpoint = os.getenv("S3_ENDPOINT")
    bucket = os.getenv("S3_BUCKET")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint,
    )

    uploaded_file.seek(0)
    s3.upload_fileobj(uploaded_file, bucket, object_key)

    return make_public_url(bucket, endpoint, object_key)
