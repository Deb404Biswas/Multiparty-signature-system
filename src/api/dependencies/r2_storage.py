import boto3
from dotenv import load_dotenv,find_dotenv
import os
from loguru import logger

class R2_Config:
    load_dotenv(find_dotenv())
    ACCESS_KEY=os.environ.get('R2_ACCESS_KEY_ID')
    SECRET_ACCESS_KEY=os.environ.get('R2_SECRET_ACCESS_KEY')
    ENDPOINT_S3=os.environ.get('R2_ENDPOINT_S3')
    BUCKET_NAME=os.environ.get('R2_BUCKET')
    @classmethod
    def get_s3_client(cls):
        try: 
            s3_client=boto3.client(
                service_name='s3',
                endpoint_url = cls.ENDPOINT_S3,
                aws_access_key_id = cls.ACCESS_KEY,
                aws_secret_access_key = cls.SECRET_ACCESS_KEY,
                region_name="auto",
            )
            logger.info("S3 client setup for R2 successfully")
            return s3_client
        except Exception as e:
            logger.error(f"Error:{e} while setting up S3 client for R2 storage")
            return False
s3_client=R2_Config.get_s3_client()