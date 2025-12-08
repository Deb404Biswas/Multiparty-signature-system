from fastapi import FastAPI,HTTPException,Request
from app.api.dependencies.database import DatabaseConnect
from app.services.object_storage.r2_storage import R2Storage
from app.core.Config.config import settings
from app.api.Router import router
from loguru import logger
from contextlib import asynccontextmanager
from app.core.logging.logger import logger
from slowapi import _rate_limit_exceeded_handler,Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the FastAPI server...")
    await DatabaseConnect.fetch_mongo_connection()
    await R2Storage.fetch_r2_connection()
    yield
    logger.info("Shutting down FastAPI server, closing R2 bucket client, MongoDB client...")
    await DatabaseConnect.close_mongo_connection()
    await R2Storage.close_r2_client()
    
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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger.info("Connecting to routers...")
app.include_router(router.router)

@app.get('/healthy')
@limiter.limit("2/second")
async def health_check(request:Request):
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
@limiter.limit("2/second")
async def version_check(request:Request):
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