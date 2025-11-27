from fastapi import APIRouter,HTTPException
from src.api.dependencies.database import DatabaseConnect
from typing import List
from pydantic import BaseModel
from starlette import status
from src.api.services.pdf_generation.pdf_generation import doc_generator
import uuid

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

@router.post("/create-new-parties",status_code=status.HTTP_201_CREATED)
async def initiate_party_inclusion(parties: Parties):
    if len(parties.list_parties)!=parties.no_of_parties:
        raise HTTPException(status_code=400,detail=f'{parties.no_of_parties} entries needed,{len(parties.list_parties)} provided')
    session_id = str(uuid.uuid4())
    docs=[]
    submit_conformation_dict={}
    sign_filepath_dict={}
    response_msg=[]
    for party in parties.list_parties:
        party_doc = {
            "role": party.role,
            "party_id": party.party_id,
            "session_id": session_id
        }
        docs.append(party_doc)
        submit_conformation_dict[f'{party.role}_{party.party_id}']=False
        sign_filepath_dict[f'{party.role}_{party.party_id}']=None
        response_msg.append(f'{party.role} having id:{party.party_id} is initiated in session:{session_id}.Make note of session id')

    session_doc={
        "session_id":session_id,
        "parties_submit_status":submit_conformation_dict,
        "parties_sign_filepath":sign_filepath_dict
    }
    await DatabaseConnect.session_collection_insert_one(session_doc)
    await DatabaseConnect.party_collection_insert_many(docs)
    return response_msg

@router.put('/lock-update', status_code=status.HTTP_200_OK)
async def lock_update(session_id):
    parties_notSubmitted=[]
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    if session_doc is None:
        raise HTTPException(status_code=404,detail=f'{session_id} does not exists in the record.')
    parties_submit_status=session_doc.get('parties_submit_status',{})
    for party,party_submit_status in parties_submit_status.items():
        if parties_submit_status[party]==False:
            parties_notSubmitted.append(party)
    if parties_notSubmitted:
        return f'{parties_notSubmitted} parties left to submit in session {session_id}'
    doc_generator.pdf_generator(session_id)
    return f"PDF generated. Use session_id: {session_id} to download file."