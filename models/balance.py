from pydantic import BaseModel, field_validator
from datetime import timezone, datetime
class TxLog(BaseModel):
    command: str
    organization: str
    cli_user_key: str
    unit_type: str
    rate_per_unit: int
    units: int
    total_cost: int
    dividend: int
    timestamp: datetime

    @field_validator("timestamp", mode="before")
    def enforce_utc(cls, v):
        dt = v if isinstance(v, datetime) else datetime.fromisoformat(v)
        return dt.astimezone(timezone.utc)

