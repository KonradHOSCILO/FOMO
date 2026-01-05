import boto3

s3 = boto3.client(
    "s3",
    aws_access_key_id="be7556864e6c40c0bc8f9e4f25aba2e5",
    aws_secret_access_key="fd1d9197890b46d98b8c8cb71e5c83ea",
    endpoint_url="https://s3.waw.io.cloud.ovh.net"
)

BUCKET = "fomo-storage"

# test upload
with open("test.txt", "w") as f:
    f.write("Hello from OVH Object Storage!")

s3.upload_file("test.txt", BUCKET, "test.txt")
print("✅ Upload działa")

# lista plików
response = s3.list_objects_v2(Bucket=BUCKET)
print("📂 Pliki w bucket:")
for obj in response.get("Contents", []):
    print("-", obj["Key"])
