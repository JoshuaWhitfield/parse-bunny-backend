from fastapi import APIRouter, HTTPException, Query
from backend.models.whitelist import AddWhitelistPayload, RemoveWhitelistPayload, ListWhitelist
from backend.utils.mongo import db

router = APIRouter()

@router.post("/whitelist/add")
async def add_to_whitelist(payload: AddWhitelistPayload):
    org = db.organizations.find_one({"organization_name": payload.organization})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    username = payload.username.strip().lower()

    existing = db.whitelists.find_one({
        "organization": payload.organization
    })

    if not existing:
        db.whitelists.insert_one({
            "organization": payload.organization,
            "master_user_key": org.get("master_user_key"),
            "whitelist": [
                {"username": username, "allowed": True}
            ]
        })
    else:
        whitelist = existing.get("whitelist", [])
        if any(user["username"].lower() == username for user in whitelist):
            raise HTTPException(status_code=400, detail="User already whitelisted")

        db.whitelists.update_one(
            {"organization": payload.organization},
            {"$push": {"whitelist": {"username": username, "allowed": True}}}
        )

    return {"success": True, "message": "User added to whitelist"}

@router.post("/whitelist/remove")
async def remove_from_whitelist(payload: RemoveWhitelistPayload):
    existing = db.whitelists.find_one({
        "organization": payload.organization
    })

    if not existing:
        raise HTTPException(status_code=404, detail="Organization not found or no whitelist exists")

    db.whitelists.update_one(
        {"organization": payload.organization},
        {"$pull": {"whitelist": {"username": payload.username}}}
    )

    return {"success": True, "message": "User removed from whitelist"}

@router.get("/whitelist/list")
async def list_whitelist(organization: str = Query(...)):
    existing = db.whitelists.find_one({"organization": organization})
    if not existing:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"whitelist": existing.get("whitelist", [])}
