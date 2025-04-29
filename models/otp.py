from pydantic import BaseModel

class OTPSubmit(BaseModel):
    snapshot_name: str
    short_key: str

class OtpSubmitRequest(BaseModel):
    organization: str
    cli_user_key: str
    backup_name: str
    short_key: str
    allowed: bool
