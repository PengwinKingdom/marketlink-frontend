# mongo_conn.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None
_db = None

def get_mongo():
    """
    Devuelve (client, db). Lanza excepción si algo está mal
    para que /health o la ruta muestren el error real.
    """
    global _client, _db
    if _client is not None and _db is not None:
        return _client, _db

    
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    dbname = os.getenv("DB_NAME", "marketlink_db")

    _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    # Valida conexión
    _client.admin.command("ping")
    _db = _client[dbname]
    return _client, _db


# ---- Colección de usuarios reutilizable ----

_client, _db = get_mongo()
usuarios_col = _db["usuarios"]
