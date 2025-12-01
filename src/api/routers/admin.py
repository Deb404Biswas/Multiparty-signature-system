from fastapi import APIRouter,HTTPException,Depends
from src.api.dependencies.database import DatabaseConnect
from src.api.routers.auth import get_current_user
from typing import List
from pydantic import BaseModel
from starlette import status
from src.api.services.pdf_generation.pdf_generation import doc_generator
import uuid
from typing import Annotated
from loguru import logger



router=APIRouter(
    prefix='/admin/v1',
    tags=['Admin']
)
class Individual_party(BaseModel):
    role:str
    party_id:str
    
class Parties(BaseModel):
    no_of_parties: int
    list_parties: List[Individual_party]
    
current_user=Annotated[dict, Depends(get_current_user)]

@router.post("/create-new-parties",status_code=status.HTTP_201_CREATED)
async def initiate_party_inclusion(parties: Parties,user:current_user):
    if user['user_type']!='admin':
        logger.error(f'{user["user_type"]} with id:{user["user_id"]} is not an admin')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='error:Not an admin')
    if len(parties.list_parties)!=parties.no_of_parties:
        raise HTTPException(status_code=400,detail=f'{parties.no_of_parties} entries needed,{len(parties.list_parties)} provided')
    session_id = str(uuid.uuid4())
    logger.info(f'session id: {session_id}')
    submit_conformation_dict={}
    sign_filepath_dict={}
    list_party=[]
    for party in parties.list_parties:
        logger.debug(f"{party}")
        list_party.append(f'{party.party_id}')
        logger.debug(f"{list_party}")
        if not await DatabaseConnect.user_collection_find_one_RoleAndId(party.role,party.party_id):
            raise HTTPException(status_code=403,detail=f'error:{party.role},id:{party.party_id} is not a registered user')
        
        submit_conformation_dict[f'{party.role}_{party.party_id}']=False
        sign_filepath_dict[f'{party.role}_{party.party_id}']=None
    session_doc={
        "session_id":session_id,
        'parties': list_party,
        'isUpdateLocked':False,
        "parties_submit_status":submit_conformation_dict,
        "parties_sign_filepath":sign_filepath_dict
    }
    await DatabaseConnect.session_collection_insert_one(session_doc)
    return {'status':200,
            'parties':list_party,
            'session_id':session_id,
            'msg':'Parties included sucessfully. Make note of session id'}

@router.put('/lock-update', status_code=status.HTTP_200_OK)
async def lock_update(session_id,user:current_user):
    if user['user_type']!='admin':
        logger.error(f'{user["user_type"]} with id:{user["user_id"]} is not an admin')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='error:Not an admin')
    parties_notSubmitted=[]
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    if session_doc is None:
        raise HTTPException(status_code=404,detail=f'{session_id} does not exists in the record.')
    parties_submit_status=session_doc.get('parties_submit_status',{})
    for party,party_submit_status in parties_submit_status.items():
        if parties_submit_status[party]==False:
            parties_notSubmitted.append(party)
    if parties_notSubmitted:
        return {
            'message':"Parties left to submit their signature",
            'Not Submitted':parties_notSubmitted,
            'session_id':session_id
            }
    update_data = {
            "$set": {
                "isUpdateLocked":True
            }}
    logger.info(f"Update locked by admin for session : {session_id}")
    await DatabaseConnect.session_collection_update_one(update_data,session_id)
    doc_generator.pdf_generator(session_id)
    return {
        'message':'PDF generated successfully.',
        'session_id':session_id
    }