from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status
import time
import json
from loguru import logger

try:
    from app.core.config.config import settings
    APP_VERSION = settings.VERSION
except:
    APP_VERSION = "v1"

class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {"/openapi.json", "/docs", "/redoc"} or "/auth/" in request.url.path:
            return response
        content_type = response.headers.get("content-type", "")
        logger.debug(f'content-type:{content_type}, status:{response.status_code}')

        if "application/json" in content_type and response.status_code < 300:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            try:
                data = json.loads(response_body.decode())
                logger.debug(f"Data decoded: {data}")
            except json.JSONDecodeError:
                logger.error("Getting JSON decode error")
                return response
            
            message = data.pop('message', 'Operation successful')
            
            wrapped_response = {
                "success": True,
                "data": data,
                "error": None,
                "message": message,
                "metadata": {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                    "version": APP_VERSION
                }
            }
            
            logger.debug(f"wrapped response:{wrapped_response}")
            
            return JSONResponse(
                content=wrapped_response,
                status_code=response.status_code
            )
        logger.debug(f"response not wrapped - content_type: {content_type}")
        return response
