from io import BytesIO
from datetime import timedelta
from typing import Optional
import logging
import uuid

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self):
        self._client: Optional[Minio] = None
    
    def get_client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
        return self._client
    
    async def upload_report(
        self,
        report_id: str,
        content: bytes,
        format: str,
        tenant_id: str = "default"
    ) -> str:
        client = self.get_client()
        
        bucket_name = settings.MINIO_BUCKET
        s3_key = f"reports/{tenant_id}/{report_id}.{format}"
        
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            
            if isinstance(content, bytes):
                content = BytesIO(content)
            
            content.seek(0)
            size = content.getbuffer().nbytes
            
            client.put_object(bucket_name, s3_key, content, length=size)
            
            logger.info(f"Uploaded report {report_id} to {s3_key}")
            return s3_key
        except S3Error as e:
            logger.error(f"Error uploading to MinIO: {e}")
            raise
    
    async def generate_download_url(
        self,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        client = self.get_client()
        
        try:
            url = client.presigned_get_object(
                settings.MINIO_BUCKET,
                s3_key,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating download URL: {e}")
            raise
    
    async def delete_report(self, s3_key: str) -> None:
        client = self.get_client()
        
        try:
            client.remove_object(settings.MINIO_BUCKET, s3_key)
            logger.info(f"Deleted report at {s3_key}")
        except S3Error as e:
            logger.error(f"Error deleting from MinIO: {e}")
            raise


minio_client = MinioClient()
