import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "parsebunny"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
