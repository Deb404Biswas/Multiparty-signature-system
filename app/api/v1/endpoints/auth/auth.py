from fastapi import APIRouter,HTTPException,Depends,Request
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from app.api.dependencies.database import DatabaseConnect
from loguru import logger
from starlette import status
from typing import Annotated
from datetime import datetime
from datetime import timedelta
from app.api.v1.endpoints.auth.helper.auth_helper import *
from app.api.v1.endpoints.auth.schemas.auth_schemas import *
from slowapi import Limiter
from slowapi.util import get_remote_address

router=APIRouter(
    prefix='/users/auth',
    tags=['Auth']
)
limiter = Limiter(key_func=get_remote_address)

try:
    @router.post("/register",status_code=status.HTTP_201_CREATED)
    @limiter.limit('5/minute')
    async def create_new_user(request:Request,user_req: UserReq):
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
            'user_type':user_type,
            'user_id':user_id
        }
except Exception as e:
    logger.error(f"Error:{e}. While executing '/register' endpoint.")
    raise HTTPException(status_code=500,detail='Undocumented error at server side.')
  
try:  
    @router.post("/login-access",response_model=Token)
    @limiter.limit('5/minute')
    async def login_access_token(request:Request,form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
        logger.info(f"user_id:{form_data.client_id},password:{form_data.password},user_role:{form_data.username}")
        user=await user_authentication(form_data.password,form_data.client_id)
        if not user:
            logger.info(f"The user:{form_data.username} having id:{form_data.client_id} is not pressent in users database")
            raise HTTPException(status_code=404,detail=f'Not authenticated')
        token=create_access_token(user["user_type"],user["user_role"],user["user_id"],timedelta(minutes=20))
        return{
            'access_token':token,
            'token_type':'bearer'
        }
except Exception as e:
    logger.error(f"Error:{e}. While executing '/login-access' endpoint")