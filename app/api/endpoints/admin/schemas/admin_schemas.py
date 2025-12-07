from pydantic import BaseModel
from typing import List

class Individual_party(BaseModel):
    role:str
    party_id:str
    
class Parties(BaseModel):
    no_of_parties: int
    list_parties: List[Individual_party]