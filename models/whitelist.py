from pydantic import BaseModel

class AddWhitelistPayload(BaseModel):
    organization: str
    username: str 

class RemoveWhitelistPayload(BaseModel):
    organization: str 
    username: str

class ListWhitelist(BaseModel):
    organization: str