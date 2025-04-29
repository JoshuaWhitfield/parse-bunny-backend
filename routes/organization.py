from fastapi import APIRouter, HTTPException, Query
from backend.models.organization import OrganizationSignup, ShortKeyPayload, AddUserPayload, OrganizationLookup, OrgLookupRequest, ListOrgByEmail
from backend.utils.mongo import db
import hashlib
from datetime import datetime

router = APIRouter()

@router.post("/org/signup")
async def signup_org(payload: OrganizationSignup):
    # Ensure master_user_key is included in the payload
    if not payload.master_user_key:
        raise HTTPException(status_code=400, detail="master_user_key required")

    new_org = {
        "organization_name": payload.organization_name,
        "data_created": datetime.utcnow(),
        "email": payload.email,
        "master_user_key": payload.master_user_key,
        "balance": 0,
        "cli_user_list": []
    }

    result = db.organizations.insert_one(new_org)
    return {
        "message": "Organization created",
        "id": str(result.inserted_id)
    }

@router.get("/backups/check-org")
async def check_organization(organization_name: str = Query(...)):
    org = db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"exists": True}

@router.get("/org/lookup-key")
async def lookup_short_key(username: str = Query(...), organization: str = Query(...)):
    org = db.organizations.find_one({"organization_name": organization})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    user = next((u for u in org["cli_user_list"] if u["username"] == username), None)
    if not user or "fernet_short_key" not in user:
        raise HTTPException(status_code=404, detail="fernet_short_key not found")

    return {"fernet_short_key": user["fernet_short_key"]}


@router.patch("/org/update-key")
async def update_short_key(payload: ShortKeyPayload):
    result = db.organizations.update_one(
        {"cli_user_list.user_key": payload.user_key},
        {"$set": {"cli_user_list.$.fernet_short_key": payload.fernet_short_key}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User key not found")

    return {"message": "Short key updated successfully"}



@router.post("/org/lookup")
async def lookup_and_update_org_user(payload: OrgLookupRequest):
    """
    1. Lookup if organization exists.
    2. Lookup if username exists within it.
    3. If cli_user_key provided, update user's user_key field.
    """
    print("RUNNING ======================")
    org = db.organizations.find_one({"organization_name": payload.organization})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    whitelist_doc = db.whitelists.find_one({"organization": payload.organization})
    if not whitelist_doc:
        raise HTTPException(status_code=404, detail="Whitelist not found for organization")

    user_list = whitelist_doc.get("whitelist", [])

    user = next((u for u in user_list if u["username"] == payload.username), None)

    if user:
        if payload.cli_user_key:
            # Update the correct user's user_key field
            db.organizations.update_one(
                {"organization_name": payload.organization, "cli_user_list.username": payload.username},
                {"$set": {"cli_user_list.$.user_key": payload.cli_user_key}}
            )
            return {
                "organization_exists": True,
                "user_exists": True,
                "cli_user_key_updated": True
            }
        else:
            return {
                "organization_exists": True,
                "user_exists": True,
                "cli_user_key_updated": False
            }
    else:

        return {
            "organization_exists": True,
            "user_exists": False
        }
    
@router.post("/org/add_user")
async def add_user_to_existing_org(payload: AddUserPayload):
    org = db.organizations.find_one({"organization_name": payload.organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    password_md5 = hashlib.md5(payload.password.encode()).hexdigest()
    user_key = hashlib.md5(payload.username.encode()).hexdigest()

    result = db.organizations.update_one(
        {"organization_name": payload.organization_name},
        {"$push": {
            "cli_user_list": {
                "username": payload.username,
                "password": password_md5,
                "user_key": user_key,
            }
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add user")

    return {"message": "User added to organization"}

@router.post("/org/by-email")
async def get_org_by_email(payload: OrganizationLookup):
    record = db.organizations.find_one({"email": payload.email})  # direct field lookup

    if not record:
        raise HTTPException(status_code=404, detail="Organization not found for provided email")
    
    return {
        "organization": record.get("organization_name"),
        "master_user_key": record.get("master_user_key"),
        "balance": record.get("balance", 0),
        "cli_user_list": record.get("cli_user_list", []),
        "master_email": record.get("email")
    }

@router.post("/org/list-by-email")
async def list_organizations_for_email(payload: ListOrgByEmail):
    """
    List all organizations where this email is the master_user email.
    """
    if not payload.email:
        raise HTTPException(status_code=400, detail="Email required")

    orgs = db.organizations.find({"email": payload.email})
    names = [o["organization_name"] for o in orgs]

    print(names)

    return {"organizations": names}


@router.get("/org/list-by-email-check")
async def list_organizations_for_email(email: str = Query(..., description="Email of the master user")):
    """
    List all organizations where this email is the master_user email.
    """
    if not email or not isinstance(email, str):
        raise HTTPException(status_code=400, detail="Valid email required.")

    try:
        # 🔥 Look up user first
        user = db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User with this email not found.")

        master_user_key = user.get("user_key")
        if not master_user_key:
            raise HTTPException(status_code=404, detail="Master user key not found for user.")

        # 🔥 Then find all orgs tied to that master_user_key
        orgs_cursor = db.organizations.find({"master_user_key": master_user_key})
        organizations = []
        for org in orgs_cursor:
            organizations.append({
                "organization_name": org.get("organization_name", "Unnamed"),
                "balance": org.get("balance", 0),
            })

        return {"organizations": organizations}

    except Exception as e:
        print(f"[list-by-email][x] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during organization lookup.")

