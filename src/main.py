from fastapi import FastAPI
from src.api.routers import admin,parties

app=FastAPI()

app.include_router(admin.router)
app.include_router(parties.router)
