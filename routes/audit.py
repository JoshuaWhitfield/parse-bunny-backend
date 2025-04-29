from fastapi import APIRouter, HTTPException, File, UploadFile
from backend.models.audit import SafeBlockedFilesAudit
from backend.utils.mongo import db
from datetime import datetime
from backend.utils.mongo import db
import gridfs

# Attach GridFS to a separate collection (optional)
fs_audit_lists = gridfs.GridFS(db, collection="audit_lists")


router = APIRouter()


@router.post("/audit/submit")
async def submit_audit(payload: SafeBlockedFilesAudit):
    """
    Submit a new audit record for safe/blocked file analysis.
    """
    try:
        audit_record = payload.dict()
        audit_record["created_at"] = datetime.utcnow()

        db.audit_logs.insert_one(audit_record)

        return {"status": "success", "message": "Audit log saved successfully."}
    except Exception as e:
        print(f"[audit][x] Failed to submit audit: {e}")
        raise HTTPException(status_code=500, detail="Failed to save audit log.")

@router.get("/audit/by-org")
async def get_audits_by_org(organization: str):
    """
    Fetch all audit logs belonging to a specific organization.
    """
    try:
        logs = list(db.audit_logs.find({"organization": organization}).sort("created_at", -1))

        for log in logs:
            log["_id"] = str(log["_id"])  # make JSON serializable

        return {"logs": logs}
    except Exception as e:
        print(f"[audit][x] Failed to fetch audits: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs.")

@router.post("/audit/upload-safe-list")
async def upload_safe_list(file: UploadFile = File(...)):
    file_id = fs_audit_lists.put(await file.read(), filename=file.filename)
    return {"file_id": str(file_id)}

@router.post("/audit/upload-blocked-list")
async def upload_blocked_list(file: UploadFile = File(...)):
    file_id = fs_audit_lists.put(await file.read(), filename=file.filename)
    return {"file_id": str(file_id)}
