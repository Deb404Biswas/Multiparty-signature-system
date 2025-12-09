from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import JSONResponse
from app.api.dependencies.database import DatabaseConnect
from app.services.object_storage.r2_storage import R2Storage
from app.core.config.config import settings
from app.api.v1.router import router
from contextlib import asynccontextmanager
from app.core.logging.logger import logger
from slowapi import _rate_limit_exceeded_handler,Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.middleware.response_wrapper import ResponseWrapperMiddleware
import time

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

logger.info("Adding middleware to app.")
app.add_middleware(ResponseWrapperMiddleware)

def create_error_response(status_code: int, error_code: str, detail_message: str):
    try:
        from app.core.config.config import settings
        APP_VERSION = settings.VERSION
    except:
        APP_VERSION = "v1"

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": status_code,
                "details": detail_message
            },
            "message": detail_message,
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "version": APP_VERSION
            }
        }
    )
    
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    http_exc = HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded: {exc.detail}"
    )
    return await http_exception_handler(request, http_exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR"
    }
    
    error_code = code_map.get(exc.status_code, "API_ERROR")
    
    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        detail_message=exc.detail
    )

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