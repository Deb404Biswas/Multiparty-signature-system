from fastapi import FastAPI
from src.api.routers import admin,parties,auth
from src.api.dependencies.database import client
from loguru import logger
from contextlib import asynccontextmanager

logger.add(
    "app.log",
    format="{time:MMMM D, YYYY - HH:mm:ss} {level} ----- {message}"
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the FastAPI server...")
    try:
        await client.admin.command("ping")
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"MongoDB ping failed: {e}")
    yield
    logger.info("Shutting down FastAPI server, closing MongoDB client...")
    client.close()
    logger.info("MongoDB client closed.")
    
app=FastAPI(
    title='Multiparty Signature System',
    lifespan=lifespan
)
logger.info("Connecting to routers...")
app.include_router(admin.router)
app.include_router(parties.router)
app.include_router(auth.router)