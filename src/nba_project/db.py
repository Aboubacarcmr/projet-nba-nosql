from pymongo import MongoClient
from pymongo.database import Database

from .config import load_settings


def get_db() -> Database:
    uri, db_name = load_settings()
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    return client[db_name]

