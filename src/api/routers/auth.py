from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from pydantic import BaseModel
from src.api.dependencies.database import DatabaseConnect
from loguru import logger
from passlib.context import CryptContext
from starlette import status
from typing import Annotated
import datetime
from datetime import timedelta,timezone
from jose import jwt
import os
from dotenv import load_dotenv,find_dotenv

logger.add(
    "app.log",
    format="{time:MMMM D, YYYY - HH:mm:ss} {level} ----- {message}"
)
router=APIRouter(
    prefix='/users/v1/auth',
    tags=['Auth']
)
pwd_context=CryptContext(schemes=['argon2'],deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/users/v1/auth/login-access')

load_dotenv(find_dotenv())
SECRET_KEY=os.environ.get('JWT_SECRET_KEY')
ALGORITHM=os.environ.get('JWT_ALGORITHM')

class UserReq(BaseModel):
    user_type: str
    user_role: str
    user_id: str
    user_password: str
class Token(BaseModel):
    access_token: str
    token_type: str
    
async def user_authentication(user_password,user_id):
    user_auth=await DatabaseConnect.user_collection_find_one(user_id)
    if not user_auth:
        raise HTTPException(status_code=401,detail=f'error:User with id {id} not found')
    if not pwd_context.verify(user_password,user_auth['user_password']):
        raise HTTPException(status_code=403,detail=f'error:Incorrect password')
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
        raise HTTPException(status_code=401,detail='error:Could not validate user')
    return {
        'user_role':user_role,
        'user_id':user_id,
        'user_type':user_type
    }

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_new_user(user_req: UserReq):
    user_type=user_req.user_type
    user_id=user_req.user_id
    user_password=user_req.user_password
    if await DatabaseConnect.user_collection_find_one(user_id):
        logger.info(f"The user:{user_type} with id:{user_id} already present in the database record. Unique id is required.")
        raise HTTPException(status_code=403,detail=f'error: User:{user_type} ID:{user_id} already present')
    doc={
        'user_type':user_type,
        'user_role':user_req.user_role,
        'user_id': user_id,
        'user_password':pwd_context.hash(user_password)
    }
    await DatabaseConnect.user_collection_insert_one(doc)
    return {
        'status':201,
        'message':'New user created!',
        'user_type': {user_type},
        'user_id':{user_id}
    }
    
@router.post("/login-access",response_model=Token)
async def login_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    user=await user_authentication(form_data.username,form_data.password,form_data.client_id)
    if not user:
        logger.info(f"The user:{form_data.username} having id:{form_data.client_id} is not pressent in users database")
        raise HTTPException(status_code=404,detail=f'Not authenticated')
    token=create_access_token(user["user_type"],user["user_role"],user["user_id"],timedelta(minutes=20))
    return{
        'access_token':token,
        'token_type':'bearer'
    }