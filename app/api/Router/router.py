from fastapi import APIRouter
from app.api.v1.endpoints.admin import admin
from app.api.v1.endpoints.auth import auth
from app.api.v1.endpoints.parties import parties
from loguru import logger

router=APIRouter(
    prefix='/v1'
)
logger.info("Connecting to endpoints")
router.include_router(admin.router)
router.include_router(parties.router)
router.include_router(auth.router)