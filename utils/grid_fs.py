from pymongo import MongoClient
import gridfs

# Connect to your MongoDB
client = MongoClient("mongodb://localhost:27017")

# Select your database (example: parse_bunny)
db = client["parsebunny"]

# Create GridFS handler
fs = gridfs.GridFS(db)
