# routes/backups.py

from fastapi import APIRouter, HTTPException, Query
from backend.models.backups import BackupPayload, PullRequest, BackupTreeRequest, BackupListRequest
from backend.utils.mongo import db
from backend.utils.secure_backup import normalize_file_entry
import base64
import gzip
import json 
from cryptography.fernet import Fernet 
import base64, gzip, json
from backend.utils.grid_fs import fs 
import hashlib
import traceback

router = APIRouter()

@router.get("/backups/check-org")
async def check_organization(org: str = Query(...)):
    if not db["organizations"].find_one({"organization_name": org}):
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"exists": True}

@router.get("/backups/check-user")
async def check_user_key(organization_name: str = Query(...), user_key: str = Query(...)):
    match = db["organizations"].find_one({
        "organization_name": organization_name,
        "cli_user_list": {
            "$elemMatch": {
                "user_key": user_key
            }
        }
    })
    if not match:
        raise HTTPException(status_code=404, detail="User key not found")
    return {"exists": True}

from bson.objectid import ObjectId

@router.post("/backups/push")
async def push_backup(payload: BackupPayload):
    # Initialize GridFS

    # Upload encrypted_data to GridFS
    backup_id = fs.put(
        base64.b64decode(payload.encrypted_data),
        filename=payload.backup_name,
        metadata={
            "organization": payload.organization,
            "cli_user_key": payload.cli_user_key,
            "backup_name": payload.backup_name
        }
    )

    # Save long_key separately
    db.backup_keys.update_one(
        {
            "organization": payload.organization,
            "cli_user_key": payload.cli_user_key,
            "backup_name": payload.backup_name
        },
        {
            "$set": {
                "long_key": payload.long_key,
                "backup_id": str(backup_id)
            }
        },
        upsert=True
    )

    return {"message": "Backup pushed successfully."}

@router.post("/backups/pull")
async def pull_backup(payload: PullRequest):
    # Get backup metadata
    key_doc = db.backup_keys.find_one({
        "organization": payload.organization,
        "cli_user_key": payload.cli_user_key,
        "backup_name": payload.backup_name
    })

    if not key_doc:
        raise HTTPException(status_code=404, detail="Backup key not found")

    backup_id = key_doc.get("backup_id")
    long_key = key_doc.get("long_key")

    if not backup_id or not long_key:
        raise HTTPException(status_code=404, detail="Backup metadata missing")

    # Download backup file
    try:
        backup_file = fs.get(ObjectId(backup_id))
        encrypted_data_bytes = backup_file.read()
    except Exception:
        raise HTTPException(status_code=404, detail="Backup file not found")

    encrypted_data_b64 = base64.b64encode(encrypted_data_bytes).decode()

    return {
        "encrypted_data": encrypted_data_b64,
        "long_key": long_key
    }

@router.post("/backups/list")
async def list_backups(payload: BackupListRequest):
    try:
        collection = db["backup_keys"]

        # Find backup keys matching organization and user key
        backups = collection.find({
            "organization": payload.organization,
            "cli_user_key": payload.cli_user_key
        })

        backup_names = [doc["backup_name"] for doc in backups]

        return { "backups": backup_names }
    except Exception as e:
        print(f"[backups list][x]", e)
        raise HTTPException(status_code=500, detail="Failed to list backups.")


@router.post("/backups/tree")
async def get_backup_tree(payload: BackupTreeRequest):
    print(f"\n[backups tree decrypt][debug] Received request for backup: {payload.backup_name}")

    # Step 1: Load keys
    key_doc = db.backup_keys.find_one({
        "organization": payload.organization,
        "cli_user_key": payload.cli_user_key,
        "backup_name": payload.backup_name
    })

    if not key_doc:
        raise HTTPException(status_code=404, detail="Backup metadata not found")

    short_key = key_doc.get("short_key")
    long_key_b64 = key_doc.get("long_key")

    if not short_key:
        return {"otp_required": True}

    # Step 2: Load encrypted blob
    backup_file = fs.find_one({
        "filename": payload.backup_name,
        "metadata.organization": payload.organization,
        "metadata.cli_user_key": payload.cli_user_key
    })

    if not backup_file:
        raise HTTPException(status_code=404, detail="Backup file not found")

    encrypted_data_b64 = backup_file.read()
    print(f"[backups tree decrypt][debug] Encrypted blob size: {len(encrypted_data_b64)} bytes")

    try:
        # Step 3: Prepare keys
        print("[backups tree decrypt][debug] Decompressing long key...")
        compressed_long_key = base64.b64decode(long_key_b64)
        long_key = gzip.decompress(compressed_long_key).decode()

        print("[backups tree decrypt][debug] Building Fernet decryptor...")
        fernet = Fernet(long_key.encode())

        # Step 4: Decrypt
        print("[backups tree decrypt][debug] Decrypting backup blob...")
        decrypted_compressed = fernet.decrypt(encrypted_data_b64)

        # Step 5: Decompress
        print("[backups tree decrypt][debug] Decompressing backup...")
        decompressed_data = gzip.decompress(decrypted_compressed)

        # Step 6: Parse JSON
        print("[backups tree decrypt][debug] Parsing JSON...")
        raw_tree = json.loads(decompressed_data)

        print("[backups tree decrypt][debug] Normalizing files...")
        normalized_tree = normalize_backup_tree(raw_tree)

        print("[backups tree decrypt][✓] Backup tree successfully recovered and normalized")
        return {"tree": normalized_tree}

    except Exception as e:
        import traceback
        print("[backups tree decrypt][x] Full decrypt/decompress/parse failed:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process backup: {type(e).__name__} - {str(e)}")

@router.get("/backups/check-allowed")
async def check_backup_allowed(organization: str, cli_user_key: str, backup_name: str):
    doc = db.backup_keys.find_one({
        "organization": organization,
        "cli_user_key": cli_user_key,
        "backup_name": backup_name
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Backup key not found")

    return {"allowed": doc.get("allowed", False)}
