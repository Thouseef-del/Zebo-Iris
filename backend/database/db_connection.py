# backend/database/db_connection.py

from pymongo import MongoClient
from config import Config


def get_db():
    """Return a reference to the MongoDB database."""
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.MONGO_DB_NAME]
    return db


# Shared database instance used by models and routes
db = get_db()
