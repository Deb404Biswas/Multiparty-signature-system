import os
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())
class ConfigClass:
    MONGO_PASS=os.environ.get('MONGO_PASS')
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY')
    JWT_ALGORITHM=os.environ.get('JWT_ALGORITHM')
    R2_TOKEN_VALUE=os.environ.get('R2_TOKEN_VALUE')
    R2_ACCESS_KEY_ID=os.environ.get('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY=os.environ.get('R2_SECRET_ACCESS_KEY')
    R2_ENDPOINT_S3=os.environ.get('R2_ENDPOINT_S3')
    R2_BUCKET=os.environ.get('R2_BUCKET')
