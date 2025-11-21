import os
from dotenv import load_dotenv,find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
try:
    load_dotenv(find_dotenv())
    mongo_password = os.environ.get("MONGO_PASS")
    connection_string = f"mongodb+srv://Debdwaipayan:{mongo_password}@internship.3kcwior.mongodb.net/?tls=true&tlsAllowInvalidCertificates=true&appName=Internship"
    client =AsyncIOMotorClient(connection_string)
    multiparty_sign_system_db=client['multiparty-sign-system']
    party_collection=multiparty_sign_system_db['Parties']
    sign_collection=multiparty_sign_system_db['Signatures']
except Exception as e:
    raise HTTPException(status_code=500,detail=f'mongo server connection error: {e}')

class DatabaseConnect:
    @staticmethod
    async def party_collection_insert_many(doc):
        await party_collection.insert_many(doc)
    async def sign_collection_insert_one(doc):
        await sign_collection.insert_one(doc)