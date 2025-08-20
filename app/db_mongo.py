import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

load_dotenv()


def get_mongo_collection() -> Collection:
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "autoposter")
    col_name = os.getenv("MONGO_COLLECTION", "posts")
    client = MongoClient(uri)
    db = client[db_name]
    col = db[col_name]
    # Ensure unique index per platform+source_url
    col.create_index([("platform", ASCENDING), ("source_url", ASCENDING)], unique=True)
    # Index on posted_at for queries
    col.create_index([("posted_at", ASCENDING)])
    return col


def initialize_database() -> None:
    _ = get_mongo_collection()


def has_been_posted(platform: str, source_url: str) -> bool:
    col = get_mongo_collection()
    doc = col.find_one({"platform": platform, "source_url": source_url, "posted_at": {"$ne": None}}, {"_id": 1})
    print(f"Already posted check: ",doc)
    return doc is not None


def exists_record(platform: str, source_url: str) -> bool:
    col = get_mongo_collection()
    doc = col.find_one({"platform": platform, "source_url": source_url}, {"_id": 1})
    return doc is not None


def record_post(
    *,
    platform: str,
    source: str,
    source_url: str,
    title: Optional[str],
    linkedin_text: Optional[str],
    x_text: Optional[str],
    success: bool,
    error: Optional[str] = None,
    posted_at: Optional[datetime] = None,
) -> None:
    col = get_mongo_collection()
    doc: Dict[str, Any] = {
        "platform": platform,
        "source": source,
        "source_url": source_url,
        "title": title,
        "linkedin_text": linkedin_text,
        "x_text": x_text,
        "posted_at": (posted_at or datetime.utcnow()).isoformat() if success else None,
        "error": error,
        "updated_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }
    col.update_one(
        {"platform": platform, "source_url": source_url},
        {"$set": doc},
        upsert=True,
    )


def fetch_pending_posts(platform: str, limit: int = 10) -> List[Dict[str, Any]]:
    col = get_mongo_collection()
    cursor = col.find({"platform": platform, "posted_at": None}).sort("_id", ASCENDING).limit(limit)
    return list(cursor)


def update_post_success(platform: str, source_url: str) -> None:
    col = get_mongo_collection()
    col.update_one(
        {"platform": platform, "source_url": source_url},
        {"$set": {"posted_at": datetime.utcnow().isoformat(), "error": None, "updated_at": datetime.utcnow().isoformat()}},
    )


def update_post_error(platform: str, source_url: str, error: str) -> None:
    col = get_mongo_collection()
    col.update_one(
        {"platform": platform, "source_url": source_url},
        {"$set": {"error": error, "updated_at": datetime.utcnow().isoformat()}},
    )
