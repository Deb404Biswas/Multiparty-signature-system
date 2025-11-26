from fastapi import APIRouter,HTTPException
from src.api.dependencies.database import DatabaseConnect
from typing import List
from pydantic import BaseModel
from starlette import status
from src.api.services.pdf_generation.pdf_generation import doc_generator

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
    
    docs = [party.model_dump() for party in parties.list_parties]
    submit_conformation_dict={}
    sign_filepath_dict={}
    global session_id
    session_id=session_id+1
    for i,party in enumerate(parties.list_parties):
        temp_dict=docs[i]
        temp_dict['session_id']=session_id
        docs[i]=temp_dict
        submit_conformation_dict[f'{party.role}']=False
        sign_filepath_dict[f'{party.role}']=None
        
    print(docs)
    await DatabaseConnect.party_collection_insert_many(docs)
    session_doc={
        "session_id":session_id,
        "parties_submit_status":submit_conformation_dict,
        "parties_sign_filepath":sign_filepath_dict
    }
    await DatabaseConnect.session_collection_insert_one(session_doc)
    return f"{parties.no_of_parties} parties added to the record in session {session_id}"

@router.put('/lock-update', status_code=status.HTTP_200_OK)
async def lock_update(session_id:int):
    parties_notSubmitted=[]
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    parties_submit_status=session_doc.get('parties_submit_status',{})
    for party,party_submit_status in parties_submit_status.items():
        if parties_submit_status[party]==False:
            parties_notSubmitted.append(party)
    if parties_notSubmitted:
        return f'Parties left to submit is session {session_id}'
    doc_generator.pdf_generator(session_id)
    return "No further update allowed by parties. PDF generation in process."