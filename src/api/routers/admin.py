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
    
isUpdateLocked=False
submit_conformation_list={}
session_id=1

@router.post("/create-new-parties",status_code=status.HTTP_201_CREATED)
async def initiate_party_inclusion(parties: Parties):
    if len(parties.list_parties)!=parties.no_of_parties:
        raise HTTPException(status_code=400,detail=f'{parties.no_of_parties} entries needed,{len(parties.list_parties)} provided')
    
    docs = [party.model_dump() for party in parties.list_parties]
    global submit_conformation_list
    global session_id
    session_id=session_id+1
    for i,party in enumerate(parties.list_parties):
        temp_dict=docs[i]
        temp_dict['session_id']=session_id
        docs[i]=temp_dict
        submit_conformation_list[f'{party.role}']=False
    print(docs)
    print(submit_conformation_list)
    await DatabaseConnect.party_collection_insert_many(docs)
    return f"{parties.no_of_parties} parties added to the record in session {session_id}"

@router.put('/lock-update', status_code=status.HTTP_200_OK)
async def lock_update(session_id:int):
    parties_notSubmitted=[]
    global submit_conformation_list
    print(submit_conformation_list)
    for party in submit_conformation_list:
        if submit_conformation_list[party]==False:
            parties_notSubmitted.append(party)
    print(parties_notSubmitted)
    if parties_notSubmitted is not None:
        return f'{parties_notSubmitted} are left to confirm and submit their signatures.'
    global isUpdateLocked
    isUpdateLocked=True
    doc_generator.pdf_generator(session_id)
    return "No further update allowed by parties. PDF generation in process."