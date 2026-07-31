"""
MongoDB CRUD service for AgriSense AI.
Wraps raw motor calls with typed helpers used across routes.
"""

import uuid
from datetime import datetime
from typing import Optional

from app.database.mongodb import mongodb_manager
from app.database.models import DiagnosisDocument
from app.utils.logger import logger

# Collection name in MongoDB
COLLECTION = "diagnoses"


class MongoService:
    """
    High-level async service for interacting with the diagnoses collection.
    All methods silently handle the case where MongoDB is unavailable.
    """

    # ─── Write ────────────────────────────────────────────────────────────────

    async def save_diagnosis(self, document: DiagnosisDocument) -> Optional[str]:
        """
        Persist a DiagnosisDocument to MongoDB.

        Args:
            document: The fully-populated diagnosis document.

        Returns:
            The inserted document's ``session_id`` on success, None otherwise.
        """
        collection = mongodb_manager.get_collection(COLLECTION)
        if collection is None:
            logger.warning("MongoDB unavailable – diagnosis not persisted.")
            return None

        try:
            doc_dict = document.model_dump()
            # Store datetime as UTC-aware ISO string for readability
            doc_dict["timestamp"] = document.timestamp.isoformat()
            result = await collection.insert_one(doc_dict)
            logger.info(
                "Diagnosis saved → _id=%s, session_id=%s",
                result.inserted_id,
                document.session_id,
            )
            return document.session_id
        except Exception as exc:
            logger.error("Failed to save diagnosis: %s", exc)
            return None

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_history(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Return a paginated list of diagnosis records sorted newest-first.

        Args:
            page:      1-indexed page number.
            page_size: Number of records per page.

        Returns:
            Tuple of (records list, total count). Returns ([], 0) on error.
        """
        collection = mongodb_manager.get_collection(COLLECTION)
        if collection is None:
            return [], 0

        try:
            skip = (page - 1) * page_size
            total = await collection.count_documents({})
            cursor = (
                collection.find({}, {"_id": 0})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(page_size)
            )
            records = await cursor.to_list(length=page_size)
            return records, total
        except Exception as exc:
            logger.error("Failed to fetch history: %s", exc)
            return [], 0

    async def get_diagnosis_by_session(
        self, session_id: str
    ) -> Optional[dict]:
        """
        Retrieve a single diagnosis by its session_id.

        Args:
            session_id: The UUID session identifier.

        Returns:
            Document dict (without _id), or None if not found / DB unavailable.
        """
        collection = mongodb_manager.get_collection(COLLECTION)
        if collection is None:
            return None

        try:
            record = await collection.find_one(
                {"session_id": session_id}, {"_id": 0}
            )
            return record
        except Exception as exc:
            logger.error("Failed to fetch diagnosis %s: %s", session_id, exc)
            return None

    # ─── Delete ───────────────────────────────────────────────────────────────

    async def delete_diagnosis(self, session_id: str) -> bool:
        """
        Delete a single diagnosis document by session_id.

        Returns:
            True if a document was deleted, False otherwise.
        """
        collection = mongodb_manager.get_collection(COLLECTION)
        if collection is None:
            return False

        try:
            result = await collection.delete_one({"session_id": session_id})
            deleted = result.deleted_count > 0
            if deleted:
                logger.info("Diagnosis %s deleted from DB.", session_id)
            return deleted
        except Exception as exc:
            logger.error("Failed to delete diagnosis %s: %s", session_id, exc)
            return False


# ─── Singleton ────────────────────────────────────────────────────────────────
mongo_service = MongoService()
