from fastapi import APIRouter, HTTPException
from backend.models.otp import OtpSubmitRequest
from backend.utils.mongo import db

router = APIRouter()

@router.get("/otp/status")
async def otp_status(snapshot_name: str):
    """Check if the short key for the snapshot is available."""
    entry = db.keys.find_one({"backup_name": snapshot_name})
    return {"available": bool(entry)}

@router.post("/otp/submit")
async def submit_otp_key(payload: OtpSubmitRequest):
    if not payload.allowed:
        raise HTTPException(status_code=400, detail="OTP submission must be explicitly allowed")

    # Find backup_key doc
    doc = db.backup_keys.find_one({
        "organization": payload.organization,
        "cli_user_key": payload.cli_user_key,
        "backup_name": payload.backup_name
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Backup key not found")

    # Update with short_key
    db.backup_keys.update_one(
        {
            "organization": payload.organization,
            "cli_user_key": payload.cli_user_key,
            "backup_name": payload.backup_name
        },
        {
            "$set": {
                "short_key": payload.short_key,
                "allowed": True
            }
        }
    )

    return {"message": "Short key submitted and allowed"}
