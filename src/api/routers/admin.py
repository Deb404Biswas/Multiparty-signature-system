from fastapi import APIRouter,HTTPException
from src.api.dependencies.database import DatabaseConnect
from typing import List
from pydantic import BaseModel
from starlette import status
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

@router.post("/create-new-parties",status_code=status.HTTP_201_CREATED)
async def initiate_party_inclusion(parties: Parties):
    if len(parties.list_parties)!=parties.no_of_parties:
        raise HTTPException(status_code=400,detail=f'{parties.no_of_parties} entries needed,{len(parties.list_parties)} provided')
    
    docs = [party.model_dump() for party in parties.list_parties]
    global submit_conformation_list
    for party in parties.list_parties:
        submit_conformation_list[party.role]=False
    await DatabaseConnect.party_collection_insert_many(docs)
    return f"{parties.no_of_parties} parties added to the record"

@router.put('/lock_update', status_code=status.HTTP_200_OK)
async def lock_update():
    global isUpdateLocked
    isUpdateLocked=True
    return "No further update allowed by parties. PDF generation in process."