from fastapi import HTTPException,Depends
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from app.api.dependencies.database import DatabaseConnect
from app.core.config.config import settings
from loguru import logger
from passlib.context import CryptContext
from typing import Annotated
from datetime import datetime
from datetime import timedelta,timezone
from jose import jwt

pwd_context=CryptContext(schemes=['argon2'],deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='v1/users/auth/login-access')

SECRET_KEY=settings.JWT_SECRET_KEY
ALGORITHM=settings.JWT_ALGORITHM

async def user_authentication(user_password,user_id):
    logger.info(f"user_id:{user_id}, user_password:{user_password}")
    user_auth=await DatabaseConnect.user_collection_find_one(user_id)
    logger.info(f"user-auth:{user_auth}")
    if not user_auth:
        logger.info(f"user_id: {user_id} not found in the database")
        raise HTTPException(status_code=401,detail=f'User with id {id} not found')
    if not pwd_context.verify(user_password,user_auth['user_password']):
        logger.info(f"User id:{user_id} found but password : {user_password} is incorrect.")
        raise HTTPException(status_code=403,detail=f'Incorrect password')
    return user_auth

def create_access_token(user_type,user_role,user_id,expires_delta):
    encode = {
        'user_type':user_type,
        'user_role':user_role,
        'user_id':user_id
    }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    user_type=payload.get('user_type')
    user_role=payload.get('user_role')
    user_id=payload.get('user_id')
    if user_role is None or user_type is None or user_id is None:
        logger.info(f'Could not validate {user_type}-->{user_role}, id:{user_id} obtained after JWT decoding.')
        raise HTTPException(status_code=401,detail='Could not validate user')
    return {
        'user_role':user_role,
        'user_id':user_id,
        'user_type':user_type
    }
