# utils/db.py
from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["parsebunny"]
collection = db["logs"]

def insert_log(command_name, payload):
    doc = {
        "command": command_name,
        "payload": payload,
        "status": "success"
    }
    try:
        collection.insert_one(doc)
        #print(f"[log][✓] Inserted log for: {command_name}")
    except Exception as e:
        print(f"[log][x] Failed to insert log: {e}")

def get_all_logs():
    return list(collection.find())
