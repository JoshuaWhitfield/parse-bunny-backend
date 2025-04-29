# backend/routes/user.py

from fastapi import APIRouter, HTTPException
from backend.models.user import User
from backend.utils.mongo import db
from typing import List
from datetime import datetime
import hashlib
import random

router = APIRouter()

# Collections
users_collection = db["users"]
organizations_collection = db["organizations"]

# 🔹 Utility: Generate CLI user_key
def generate_cli_user_key() -> str:
    num = str(random.randint(10000000, 99999999))
    hash_prefix = hashlib.md5(num.encode()).hexdigest()[:8]
    return f"0x{hash_prefix}"

# 🔹 Utility: Generate Master user_key (frontend signup)
def generate_master_user_key(email: str) -> str:
    rand = str(random.randint(100000, 999999))
    hashed = hashlib.md5((email + rand).encode()).hexdigest()[:12]
    return f"0x{hashed}"

# ==========================================================
# 🖥 Frontend (Website) User Routes
# ==========================================================

@router.post("/user/signup")
async def signup_frontend_user(data: dict):
    """
    Frontend signup for dashboard users (website accounts).
    """
    name = data.get("name")
    email = data.get("email")
    uid = data.get("uid")
    photoURL = data.get("photoURL")

    if not name or not email or not uid:
        raise HTTPException(status_code=400, detail="Missing required fields")

    existing = users_collection.find_one({"email": email})

    if existing:
        return {
            "status": "ok",
            "message": "User already exists",
            "master_user_key": existing["user_key"]
        }

    master_user_key = generate_master_user_key(email)

    users_collection.insert_one({
        "name": name,
        "email": email,
        "uid": uid,
        "photoURL": photoURL,
        "user_key": master_user_key,
        "created_at": datetime.utcnow()
    })

    return {
        "status": "ok",
        "message": "User created",
        "master_user_key": master_user_key
    }

# ==========================================================
# 🐇 CLI User Routes
# ==========================================================

@router.post("/users")
async def create_cli_user(user: User):
    """
    CLI signup route for ParseBunny users.
    """
    user_dict = user.dict()
    user_dict["created_at"] = datetime.utcnow()
    result = users_collection.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

@router.get("/users")
async def list_cli_users():
    """
    Return all CLI users (this can be restricted in production).
    """
    users = users_collection.find({}, {"_id": 0, "username": 1, "user_key": 1})
    return list(users)

@router.get("/verify/{user_key}")
async def verify_license(user_key: str):
    """
    Verify a CLI user's license by user_key.
    """
    user = users_collection.find_one({"user_key": user_key})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("paid", False):
        raise HTTPException(status_code=402, detail="Payment required")
    return {"status": "verified"}

# ==========================================================
# 🏢 Organization Routes
# ==========================================================

@router.post("/api/org/signup")
async def signup_organization(data: dict):
    """
    Create a new organization (used by frontend dashboard).
    """
    org_name = data.get("organization_name")
    username = data.get("username")
    password = data.get("password")
    master_user_key = data.get("master_user_key")

    if not all([org_name, username, password, master_user_key]):
        raise HTTPException(status_code=400, detail="Missing fields")

    master_user = users_collection.find_one({"user_key": master_user_key})
    if not master_user:
        raise HTTPException(status_code=403, detail="Invalid master_user_key")

    if organizations_collection.find_one({"organization_name": org_name}):
        return {"status": "ok", "message": "Organization already exists"}

    organizations_collection.insert_one({
        "organization_name": org_name,
        "master_user_key": master_user_key,
        "date_created": datetime.utcnow(),
        "cli_user_list": [
            {
                "username": username,
                "password": password,
                "user_key": generate_cli_user_key(),
                "backups": {}
            }
        ]
    })

    return {"status": "ok", "message": "Organization created"}

@router.get("/api/org/by-user")
async def list_organizations_for_master(master_user_key: str):
    """
    List organizations associated with a frontend website user.
    """
    orgs = organizations_collection.find(
        {"master_user_key": master_user_key},
        {"organization_name": 1, "_id": 0}
    )
    return {"organizations": [org["organization_name"] for org in orgs]}

@router.post("/api/lookup")
async def lookup_by_username(data: dict):
    """
    Lookup a CLI user's MD5 and short_key by username.
    (Internal use only)
    """
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "md5": user.get("md5"),
        "short_key": user.get("short_key")
    }
