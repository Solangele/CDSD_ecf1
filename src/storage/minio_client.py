import io
import json
from datetime import datetime, timedelta
from typing import Optional
from minio import Minio
from minio.error import S3Error
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
    
    def _ensure_buckets(self) -> None:
        buckets = [
            minio_config.bucket_images,
            minio_config.bucket_exports,
            minio_config.bucket_backups
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info("bucket_created", bucket=bucket)
            except S3Error as e:
                logger.error("bucket_creation_failed", bucket=bucket, error=str(e))
    
# IMAGES
    
    def upload_image(
        self,
        image_data: bytes,
        object_name: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
       
        try:
            self.client.put_object(
                bucket_name=minio_config.bucket_images,
                object_name=object_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type=content_type
            )
            
            uri = f"minio://{minio_config.bucket_images}/{object_name}"
            logger.info("image_uploaded", 
                       object_name=object_name, 
                       size_kb=len(image_data) // 1024)
            return uri
            
        except S3Error as e:
            logger.error("image_upload_failed", object_name=object_name, error=str(e))
            return None
    
    def get_image(self, object_name: str) -> Optional[bytes]:
        try:
            response = self.client.get_object(
                bucket_name=minio_config.bucket_images,
                object_name=object_name
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error("image_download_failed", object_name=object_name, error=str(e))
            return None
    
    def delete_image(self, object_name: str) -> bool:
        try:
            self.client.remove_object(minio_config.bucket_images, object_name)
            logger.info("image_deleted", object_name=object_name)
            return True
        except S3Error as e:
            logger.error("image_delete_failed", object_name=object_name, error=str(e))
            return False
    
    def list_images(self, prefix: str = "") -> list[dict]:
        try:
            objects = self.client.list_objects(
                bucket_name=minio_config.bucket_images,
                prefix=prefix,
                recursive=True
            )
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "modified": obj.last_modified
                }
                for obj in objects
            ]
        except S3Error as e:
            logger.error("list_images_failed", error=str(e))
            return []
        


# EXPORTS
    
    def upload_export(
        self,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:

        try:
            self.client.put_object(
                bucket_name=minio_config.bucket_exports,
                object_name=filename,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            
            uri = f"minio://{minio_config.bucket_exports}/{filename}"
            logger.info("export_uploaded", filename=filename, size_kb=len(data) // 1024)
            return uri
            
        except S3Error as e:
            logger.error("export_upload_failed", filename=filename, error=str(e))
            return None
    
    def upload_csv(self, csv_content: str, filename: str) -> Optional[str]:
        """Upload un fichier CSV."""
        return self.upload_export(
            csv_content.encode("utf-8"),
            filename,
            "text/csv"
        )
    
    def upload_json(self, data: dict, filename: str) -> Optional[str]:
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        return self.upload_export(json_bytes, filename, "application/json")
    
    def get_export(self, filename: str) -> Optional[bytes]:
        try:
            response = self.client.get_object(minio_config.bucket_exports, filename)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error:
            return None
    
    def list_exports(self) -> list[dict]:
        try:
            objects = self.client.list_objects(
                minio_config.bucket_exports,
                recursive=True
            )
            return [
                {"name": obj.object_name, "size": obj.size, "modified": obj.last_modified}
                for obj in objects
            ]
        except S3Error:
            return []
        
# BACKUPS 
    
    def create_backup(self, data: dict, prefix: str = "backup") -> Optional[str]:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        
        try:
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
            
            self.client.put_object(
                bucket_name=minio_config.bucket_backups,
                object_name=filename,
                data=io.BytesIO(json_bytes),
                length=len(json_bytes),
                content_type="application/json"
            )
            
            uri = f"minio://{minio_config.bucket_backups}/{filename}"
            logger.info("backup_created", filename=filename)
            return uri
            
        except S3Error as e:
            logger.error("backup_failed", error=str(e))
            return None
    
    def list_backups(self) -> list[dict]:
        try:
            objects = self.client.list_objects(minio_config.bucket_backups, recursive=True)
            return [
                {"name": obj.object_name, "size": obj.size, "modified": obj.last_modified}
                for obj in objects
            ]
        except S3Error:
            return []


    
    def copy_to_bucket(
        self,
        source_bucket: str,
        source_object: str,
        dest_bucket: str,
        dest_object: str = None
    ) -> bool:
        from minio.commonconfig import CopySource
        
        dest_object = dest_object or source_object
        
        try:
            self.client.copy_object(
                dest_bucket,
                dest_object,
                CopySource(source_bucket, source_object)
            )
            return True
        except S3Error as e:
            logger.error("copy_failed", error=str(e))
            return False
    

# URLS PRÉSIGNÉES
    def get_presigned_url(
        self,
        object_name: str,
        bucket: str = None,
        expires_hours: int = 24
    ) -> Optional[str]:

        bucket = bucket or minio_config.bucket_images
        
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except S3Error as e:
            logger.error("presigned_url_failed", object_name=object_name, error=str(e))
            return None
    

# STATISTIQUE
    def get_stats(self) -> dict:
        stats = {}
        
        for bucket_name in [minio_config.bucket_images, 
                           minio_config.bucket_exports, 
                           minio_config.bucket_backups]:
            try:
                objects = list(self.client.list_objects(bucket_name, recursive=True))
                stats[bucket_name] = {
                    "count": len(objects),
                    "total_size_mb": sum(o.size for o in objects) / (1024 * 1024)
                }
            except S3Error:
                stats[bucket_name] = {"count": 0, "total_size_mb": 0}
        
        return stats
    


# Test
if __name__ == "__main__":
    print("Test du client MinIO...")
    
    storage = MinIOStorage()
    
    # Test upload
    test_data = b"Hello MinIO!"
    uri = storage.upload_export(test_data, "test.txt", "text/plain")
    print(f"Upload test: {uri}")
    
    # Test stats
    stats = storage.get_stats()
    print(f"Stats: {stats}")
    
    print("Tests terminés!")