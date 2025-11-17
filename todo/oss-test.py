import os
from dotenv import load_dotenv
import oss2


load_dotenv()


access_key = os.getenv("ALIBABA_ACCESS_KEY_ID")
access_secret = os.getenv("ALIBABA_ACCESS_KEY_SECRET")
endpoint = os.getenv("OSS_ENDPOINT")
bucket_name = os.getenv("OSS_BUCKET_NAME")

auth = oss2.Auth(access_key, access_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

# Test uploadu
bucket.put_object("test.txt", "Hello OSS!")

# Test pobrania podpisanego URL
url = bucket.sign_url('GET', 'test.txt', 60)
print("Signed URL:", url)
