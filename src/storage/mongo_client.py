import structlog
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timezone
from typing import List, Dict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import mongo_config

logger = structlog.get_logger()

class MongoDBStorage:
    def __init__(self):
        self.client = MongoClient(mongo_config.connection_string)
        self.db = self.client[mongo_config.database]
        
        self.products = self.db["products"]
        self.quotes = self.db["quotes"]
        self.logs = self.db["scraping_logs"]
        
        self._ensure_indexes()
        logger.info("mongodb_storage_ready")


    def _ensure_indexes(self):
        self.products.create_index([("title", ASCENDING)], unique=True)
        self.quotes.create_index([("text", ASCENDING)], unique=True)


    def save_item(self, collection_name: str, data: Dict) -> bool:
        try:
            data["scraped_at"] = datetime.utcnow()
            collection = self.db[collection_name]
        
            search_key = "title" if collection_name == "products" else "text"
            
            collection.update_one(
                {search_key: data.get(search_key)},
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"save_failed_in_{collection_name}", error=str(e))
            return False

    def get_all(self, collection_name: str) -> List[Dict]:
        """Récupère tout le contenu d'une collection (sans les ID techniques)."""
        return list(self.db[collection_name].find({}, {"_id": 0}))

    def log_run(self, scraper_name: str, count: int, status: str = "success"):
        """Enregistre le passage d'un scraper."""
        self.logs.insert_one({
            "scraper": scraper_name,
            "count": count,
            "status": status,
            "timestamp": datetime.now(timezone.utc)
        })

if __name__ == "__main__":
    storage = MongoDBStorage()
    storage.save_item("quotes", {"text": "La vie est belle", "author": "Anonyme"})
    storage.save_item("products", {"title": "iPhone 15", "price": 999})
    print("Test terminé, vérifiez Compass !")