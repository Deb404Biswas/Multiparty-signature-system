from fastapi import FastAPI,HTTPException
from app.api.dependencies.database import client
from app.api.services.object_storage.r2_storage import s3_client,R2_Config
from app.core.config import settings
from app import routes
from loguru import logger
from contextlib import asynccontextmanager

logger.add(
    'app/core/logging/app.log',
    format="{time:MMMM D, YYYY - HH:mm:ss} {level} ----- {message}",
    rotation="6 hours",
    retention="24 hours"
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the FastAPI server...")
    try:
        await client.admin.command("ping")
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"MongoDB ping failed: {e}")
    try:
        s3_client.head_bucket(Bucket=R2_Config.BUCKET_NAME)
        logger.info(f"R2 bucket '{R2_Config.BUCKET_NAME}' connection verified.")
    except Exception as e:
        logger.error(f"R2 bucket connection failed: {e}")
    yield
    logger.info("Shutting down FastAPI server, closing MongoDB client...")
    client.close()
    logger.info("MongoDB client closed.")
    s3_client.close()
    logger.info("R2 S3 client closed.")
    
APP_MODE=settings.APP_MODE
docs_url=None if APP_MODE == "production" else "/docs"
redoc_url=None if APP_MODE == "production" else "/redoc" 
openapi_url=None if APP_MODE == "production" else "/openapi.json"

logger.debug(f'docs_url={docs_url}, redoc_url={redoc_url}, openapi_url={openapi_url}, APP_MODE={APP_MODE}')

app=FastAPI(
    title='Multiparty Signature System',
    lifespan=lifespan,
    docs_url=docs_url, redoc_url=redoc_url, openapi_url=openapi_url
)
logger.info("Connecting to routers...")
app.include_router(routes.router)

@app.get('/healthy')
async def health_check():
    try:
        logger.info("Health check completed successfully")
        return {
            'status':200,
            'message':'Health check completed successfully.'
        }
    except:
        logger.error("Health check failed.")
        raise HTTPException(status_code=500,detail='Undocumented error occurred at health check')
@app.get('/version-check')
async def version_check():
    try:    
        version=settings.VERSION
        logger.info("Version check successfull")
        return {
            'status':200,
            'version':version,
            'message':'Version check successfull.'
        }
    except:
        logger.error("Version check failed")
        raise HTTPException(status_code=500, detail='Undocumented error at version check')