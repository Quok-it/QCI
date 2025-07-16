from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from tensorbot.config.config import MONGODB_URI

class DatabaseInterface:
    def __init__(self, db_uri: str, collection_name: str):
        try: 
            self.client = MongoClient(db_uri)
            self.client.server_info()  # Force connection on init
            print("[INFO] Connected successfully to MongoDB.")
        except ConnectionFailure as e:
            raise Exception(f"[ERROR] Could not connect to MongoDB: {e}")

        self.db = self.client["QCP"]
        self.collection = self.db[collection_name]  

    def save_rental_session(self, session_data: dict):
        """Save a rental session document to the database."""
        try:
            self.collection.insert_one(session_data)
            print(f"[INFO] Rental session {session_data.get('session_id')} saved to MongoDB.")
        except OperationFailure as e:
            print(f"[ERROR] Failed to save rental session: {e}")

    def close(self):
        self.client.close()
        print("[INFO] MongoDB connection closed.")
