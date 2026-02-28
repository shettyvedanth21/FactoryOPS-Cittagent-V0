from minio import Minio
from minio.error import S3Error
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {e}")
    
    def upload_file(
        self,
        data: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=s3_key,
                data=data,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded file to s3://{self.bucket}/{s3_key}")
            return s3_key
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def get_presigned_url(self, s3_key: str, expires_hours: int = 1) -> str:
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=s3_key,
                expires=expires_hours * 3600
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def delete_object(self, s3_key: str):
        try:
            self.client.remove_object(self.bucket, s3_key)
            logger.info(f"Deleted s3://{self.bucket}/{s3_key}")
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def get_object(self, s3_key: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, s3_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error getting file: {e}")
            raise


minio_client = MinioClient()
