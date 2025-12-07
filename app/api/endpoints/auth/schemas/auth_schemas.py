from pydantic import BaseModel
from typing import Literal
class UserReq(BaseModel):
    user_type: Literal['party', 'admin']
    user_role: str
    user_id: str
    user_password: str
class Token(BaseModel):
    access_token: str
    token_type: str