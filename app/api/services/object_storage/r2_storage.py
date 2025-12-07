import boto3
import io
from app.core.config import settings
from loguru import logger
from typing import BinaryIO, Dict, Any

class R2_Config:
    ACCESS_KEY = settings.R2_ACCESS_KEY_ID
    SECRET_ACCESS_KEY = settings.R2_SECRET_ACCESS_KEY
    ENDPOINT_S3 = settings.R2_ENDPOINT_S3
    BUCKET_NAME = settings.R2_BUCKET

    @classmethod
    def get_s3_client(cls):
        try:
            s3_client = boto3.client(
                service_name='s3',
                endpoint_url=cls.ENDPOINT_S3,
                aws_access_key_id=cls.ACCESS_KEY,
                aws_secret_access_key=cls.SECRET_ACCESS_KEY,
                region_name="auto",
            )
            logger.info("S3 client setup for R2 successfully")
            return s3_client
        except Exception as e:
            logger.error(f"Error:{e} while setting up S3 client for R2 storage")
            raise

s3_client = R2_Config.get_s3_client()


class R2Storage:
    @staticmethod
    async def upload_file(file_content: bytes, filepath: str) -> bool:
        try:
            s3_client.upload_fileobj(
                io.BytesIO(file_content),
                R2_Config.BUCKET_NAME,
                filepath
            )
            logger.info(f"File uploaded successfully to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error: {e} while uploading to R2 bucket at {filepath}")
            raise
    
    @staticmethod
    async def get_file(filepath: str) -> bytes:
        try:
            response = s3_client.get_object(
                Bucket=R2_Config.BUCKET_NAME,
                Key=filepath
            )
            file_content = response['Body'].read()
            logger.info(f"File downloaded successfully from {filepath}")
            return file_content
        except Exception as e:
            logger.error(f"Error: {e} while downloading from R2 bucket at {filepath}")
            raise
    
    @staticmethod
    async def list_files(prefix: str) -> list[str]:
        try:
            response = s3_client.list_objects_v2(
                Bucket=R2_Config.BUCKET_NAME,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.warning(f"No files found with prefix: {prefix}")
                return []
            
            file_keys = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Found {len(file_keys)} files with prefix: {prefix}")
            return file_keys
        except Exception as e:
            logger.error(f"Error: {e} while listing files with prefix: {prefix}")
            raise
    
    @staticmethod
    async def put_file(filepath: str, file_content: bytes, content_type: str = 'application/octet-stream') -> bool:
        try:
            s3_client.put_object(
                Bucket=R2_Config.BUCKET_NAME,
                Key=filepath,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"File put successfully to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error: {e} while putting file to R2 bucket at {filepath}")
            raise
