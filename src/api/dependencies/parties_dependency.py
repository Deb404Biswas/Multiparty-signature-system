from fastapi import HTTPException
from src.api.dependencies.database import DatabaseConnect

async def isPartyInSession(user,session_id):
    if user['user_type']!='party':
            raise HTTPException(status_code=403,detail='error:User not registered as party')
    party_role=user['user_role']
    party_id=user['user_id']
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    list_parties=session_doc.get('parties')
    party_found=False
    for party in list_parties:
        if party.party_id==party_id:
            party_found=True
            break
    if party_found==False:
        raise HTTPException(status_code=403,detail=f'error: {party_role},id:{party_id} not in session:{session_id}')
    return session_doc