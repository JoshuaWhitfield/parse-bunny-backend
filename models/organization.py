from pydantic import BaseModel
from typing import Optional

class OrganizationSignup(BaseModel):
    organization_name: str
    email: str
    master_user_key: str


class ShortKeyPayload(BaseModel):
    user_key: str
    fernet_short_key: str

class AddUserPayload(BaseModel):
    organization_name: str
    username: str
    password: str


class OrgLookupRequest(BaseModel):
    organization: str
    cli_user_key: Optional[str] = None
    username: str

class OrganizationLookup(BaseModel):
    email: str

class ListOrgByEmail(BaseModel):
    email: str