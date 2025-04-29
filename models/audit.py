from pydantic import BaseModel, Field
from typing import List

class SafeBlockedFilesAudit(BaseModel):
    organization: str = Field(...)
    cli_user_key: str = Field(...)
    timestamp: str = Field(...)
    safe_files: List[str] = Field(default_factory=list)
    blocked_files: List[str] = Field(default_factory=list)
    safe_files_count: int = Field(...)
    blocked_files_count: int = Field(...)
    cli_version: str = Field(..., example="parse-bunny-beta-v0.1.0")
