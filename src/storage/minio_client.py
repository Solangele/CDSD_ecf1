import io
from minio import Minio
import structlog

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import minio_config

logger = structlog.get_logger()

class MinIOStorage:
    def __init__(self):
        self.client = Minio(
            endpoint=minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=minio_config.secure
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [minio_config.bucket_images, minio_config.bucket_exports, minio_config.bucket_backups]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info("bucket_created", bucket=bucket)

    def upload_file(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            logger.info("file_uploaded", bucket=bucket_name, object=object_name)
            return f"minio://{bucket_name}/{object_name}"
        except Exception as e:
            logger.error("upload_failed", error=str(e))
            return ""

    def get_file(self, bucket_name: str, object_name: str) -> bytes:
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error("download_failed", error=str(e))
            return b""

    def get_stats(self):
        stats = {}
        for b in [minio_config.bucket_images, minio_config.bucket_exports]:
            objs = list(self.client.list_objects(b))
            stats[b] = {"count": len(objs)}
        return stats

if __name__ == "__main__":
    storage = MinIOStorage()
    storage.upload_file(minio_config.bucket_exports, "test_simple.txt", b"Hello World")
    print("Test MinIO OK - Stats:", storage.get_stats())