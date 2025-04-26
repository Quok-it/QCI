from pymongo import MongoClient
import datetime

class DatabaseInterface:
    def __init__(self, db_uri: str, collection_name: str):
        self.client = MongoClient(db_uri)
        self.db = self.client["QCP"]
        self.collection = self.db["collection_name"]  

    def save_gpu_instance(self, gpu_info: dict) -> None:
        """Save GPU instance info into MongoDB."""
        gpu_info["timestamp"] = datetime.datetime.now(datetime.UTC) # Add timestamp
        self.collection.insert_one(gpu_info)
