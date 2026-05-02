import os
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "dms-documents"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def init_minio():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as err:
        print(f"MinIO error: {err}")

# Optional helper to generate signed URL
def get_presigned_url(object_name, expiry_minutes=5):
    from datetime import timedelta
    try:
        url = minio_client.presigned_get_object(
            BUCKET_NAME, 
            object_name, 
            expires=timedelta(minutes=expiry_minutes)
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None
