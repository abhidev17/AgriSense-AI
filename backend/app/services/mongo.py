"""
MongoDB CRUD service for AgriSense AI.

Phase 2 upgrades:
  - get_history() now supports filtering by crop, disease, date range, and full-text search
  - get_stats() aggregation for dashboard metrics
  - get_high_risk_diagnoses() for alerting
"""

from datetime import datetime
from typing import Optional

from app.database.mongodb import mongodb_manager, DIAGNOSES_COLLECTION
from app.database.models import DiagnosisDocument
from app.utils.logger import logger


class MongoService:
    """
    High-level async service for the diagnoses collection.
    All methods silently handle the case where MongoDB is unavailable.
    """

    # ─── Write ────────────────────────────────────────────────────────────────

    async def save_diagnosis(self, document: DiagnosisDocument) -> Optional[str]:
        """
        Persist a DiagnosisDocument to MongoDB.

        Returns:
            The session_id on success, None otherwise.
        """
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
        if collection is None:
            logger.warning("MongoDB unavailable — diagnosis not persisted.")
            return None

        try:
            doc_dict = document.model_dump()
            doc_dict["timestamp"] = document.timestamp.isoformat()
            result = await collection.insert_one(doc_dict)
            logger.info(
                "Diagnosis saved to MongoDB — _id=%s, session=%s",
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
        crop: Optional[str] = None,
        disease: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        min_risk_score: Optional[int] = None,
    ) -> tuple[list[dict], int]:
        """
        Return paginated, filtered diagnosis records sorted newest-first.

        Args:
            page:           1-indexed page number.
            page_size:      Records per page.
            crop:           Filter by crop name (case-insensitive contains).
            disease:        Filter by disease name (case-insensitive contains).
            date_from:      Filter records after this UTC datetime.
            date_to:        Filter records before this UTC datetime.
            search:         Full-text search across crop, disease, explanation.
            min_risk_score: Only return diagnoses with risk_score >= this value.

        Returns:
            Tuple of (records list, total count matching filters).
        """
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
        if collection is None:
            return [], 0

        try:
            query: dict = {}

            # Full-text search (uses the text index)
            if search:
                query["$text"] = {"$search": search}

            # Crop filter (regex for case-insensitive partial match)
            if crop:
                query["crop.name"] = {"$regex": crop, "$options": "i"}

            # Disease filter
            if disease:
                query["disease.name"] = {"$regex": disease, "$options": "i"}

            # Date range filter
            if date_from or date_to:
                ts_filter: dict = {}
                if date_from:
                    ts_filter["$gte"] = date_from.isoformat()
                if date_to:
                    ts_filter["$lte"] = date_to.isoformat()
                query["timestamp"] = ts_filter

            # Minimum risk score filter
            if min_risk_score is not None:
                query["action_plan.risk_score"] = {"$gte": min_risk_score}

            skip = (page - 1) * page_size

            # Run count and query concurrently for performance
            total = await collection.count_documents(query)

            sort_key = [("timestamp", -1)]
            # If text search, sort by relevance score first
            if search:
                sort_key = [("score", {"$meta": "textScore"}), ("timestamp", -1)]

            projection = {"_id": 0}
            if search:
                projection["score"] = {"$meta": "textScore"}

            cursor = (
                collection.find(query, projection)
                .sort(sort_key)
                .skip(skip)
                .limit(page_size)
            )
            records = await cursor.to_list(length=page_size)

            logger.debug(
                "History query: page=%d, size=%d, total=%d, filters=%s",
                page, page_size, total,
                {"crop": crop, "disease": disease, "search": search},
            )
            return records, total

        except Exception as exc:
            logger.error("Failed to fetch history: %s", exc)
            return [], 0

    async def get_diagnosis_by_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve a single diagnosis by session_id (uses unique index).

        Returns:
            Document dict (without _id), or None.
        """
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
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

    async def get_stats(self) -> dict:
        """
        Return aggregated statistics for the dashboard.

        Returns:
            Dict with total_diagnoses, top_crops, top_diseases, avg_risk_score.
        """
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
        if collection is None:
            return {}

        try:
            pipeline = [
                {
                    "$facet": {
                        "total": [{"$count": "count"}],
                        "top_crops": [
                            {"$group": {"_id": "$crop.name", "count": {"$sum": 1}}},
                            {"$sort": {"count": -1}},
                            {"$limit": 5},
                        ],
                        "top_diseases": [
                            {"$group": {"_id": "$disease.name", "count": {"$sum": 1}}},
                            {"$sort": {"count": -1}},
                            {"$limit": 5},
                        ],
                        "avg_risk": [
                            {
                                "$match": {
                                    "action_plan.risk_score": {"$exists": True}
                                }
                            },
                            {
                                "$group": {
                                    "_id": None,
                                    "avg": {"$avg": "$action_plan.risk_score"},
                                }
                            },
                        ],
                        "severity_distribution": [
                            {
                                "$group": {
                                    "_id": "$disease.severity",
                                    "count": {"$sum": 1},
                                }
                            },
                        ],
                    }
                }
            ]

            result = await collection.aggregate(pipeline).to_list(length=1)
            if not result:
                return {}

            data = result[0]
            return {
                "total_diagnoses": data["total"][0]["count"] if data["total"] else 0,
                "top_crops": [
                    {"crop": r["_id"], "count": r["count"]}
                    for r in data.get("top_crops", [])
                ],
                "top_diseases": [
                    {"disease": r["_id"], "count": r["count"]}
                    for r in data.get("top_diseases", [])
                ],
                "avg_risk_score": (
                    round(data["avg_risk"][0]["avg"], 1)
                    if data.get("avg_risk")
                    else None
                ),
                "severity_distribution": {
                    r["_id"]: r["count"]
                    for r in data.get("severity_distribution", [])
                },
            }
        except Exception as exc:
            logger.error("Failed to aggregate stats: %s", exc)
            return {}

    async def get_high_risk_diagnoses(
        self, min_score: int = 70, limit: int = 10
    ) -> list[dict]:
        """
        Return recent high-risk diagnoses above the given score threshold.
        Useful for alert dashboards.
        """
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
        if collection is None:
            return []

        try:
            cursor = (
                collection.find(
                    {"action_plan.risk_score": {"$gte": min_score}},
                    {"_id": 0},
                )
                .sort("action_plan.risk_score", -1)
                .limit(limit)
            )
            return await cursor.to_list(length=limit)
        except Exception as exc:
            logger.error("Failed to fetch high-risk diagnoses: %s", exc)
            return []

    # ─── Delete ───────────────────────────────────────────────────────────────

    async def delete_diagnosis(self, session_id: str) -> bool:
        """Delete a diagnosis document by session_id. Returns True if deleted."""
        collection = mongodb_manager.get_collection(DIAGNOSES_COLLECTION)
        if collection is None:
            return False

        try:
            result = await collection.delete_one({"session_id": session_id})
            deleted = result.deleted_count > 0
            if deleted:
                logger.info("Diagnosis %s deleted from MongoDB.", session_id)
            return deleted
        except Exception as exc:
            logger.error("Failed to delete diagnosis %s: %s", session_id, exc)
            return False


# ─── Singleton ────────────────────────────────────────────────────────────────
mongo_service = MongoService()
