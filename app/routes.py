from fastapi import APIRouter
from app.api.endpoints.admin import admin
from app.api.endpoints.auth import auth
from app.api.endpoints.parties import parties
from loguru import logger

router=APIRouter()
logger.info("Connecting to endpoints")
router.include_router(admin.router)
router.include_router(parties.router)
router.include_router(auth.router)