from fastapi import FastAPI
from src.api.routers import admin,parties,auth
from loguru import logger

logger.remove()
logger.add(
    "app.log",
    format="{time:MMMM D, YYYY - HH:mm:ss} {level} ----- {message}"
)
logger.info("Starting the FastApi server...")
app=FastAPI()
logger.info("Connecting to routers...")
app.include_router(admin.router)
app.include_router(parties.router)
app.include_router(auth.router)