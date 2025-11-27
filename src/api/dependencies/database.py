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
    session_collection=multiparty_sign_system_db['Sessions']
except Exception as e:
    raise HTTPException(status_code=500,detail=f'mongo server connection error: {e}')

class DatabaseConnect:
    @staticmethod
    async def party_collection_insert_many(doc):
        await party_collection.insert_many(doc)
    @staticmethod
    async def party_collection_find_one(id,session_id):
        return await party_collection.find_one({
            'party_id':id,
            'session_id':session_id
        })
    @staticmethod
    async def session_collection_insert_one(doc):
        await session_collection.insert_one(doc)
    @staticmethod
    async def session_collection_find_one(session_id):
        return await session_collection.find_one({'session_id':session_id})
    @staticmethod
    async def session_collection_update_one(update_data,session_id):
        await session_collection.update_one(
            {"session_id": session_id},
            update_data
        )