from fastapi import HTTPException,status
from app.api.dependencies.database import DatabaseConnect
from loguru import logger

async def isPartyInSession(user,session_id):
    if user['user_type']!='party':
            raise HTTPException(status_code=403,detail='User not registered as party')
    party_role=user['user_role']
    party_id=user['user_id']
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    if session_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f'Session {session_id} does not exists')
    list_party=session_doc.get('parties')
    party_found=False
    for party in list_party:
        if party==party_id:
            party_found=True
            break
    if party_found==False:
        logger.info(f'{party_role} of id: {party_id} does not belong in {session_id}')
        raise HTTPException(status_code=403,detail=f'{party_role},id:{party_id} not in session:{session_id}')
    logger.info(f'{party_role} of id: {party_id} belongs in {session_id}')
    return session_doc