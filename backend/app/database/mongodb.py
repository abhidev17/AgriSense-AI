"""
MongoDB connection manager for AgriSense AI.
Uses motor (async MongoDB driver) for non-blocking database operations.

Phase 2 additions:
  - create_indexes() called on startup for query performance
  - Indexes on: session_id (unique), timestamp (desc), crop.name, disease.name, text search
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# Collection name
DIAGNOSES_COLLECTION = "diagnoses"


class MongoDBManager:
    """
    Async MongoDB connection manager (singleton).

    Lifecycle:
        - Call ``connect()`` at application startup.
        - Call ``close()`` at application shutdown.
    """

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    # ─── Connection management ─────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Open the MongoDB connection, ping the server, and create indexes.
        Logs a warning (but does not crash) if the server is unavailable.
        """
        try:
            logger.info(
                "Connecting to MongoDB at %s (db: %s)...",
                settings.MONGODB_URI,
                settings.MONGODB_DB_NAME,
            )
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5_000,
            )
            await self._client.admin.command("ping")
            self._db = self._client[settings.MONGODB_DB_NAME]
            logger.info("MongoDB connected successfully (OK)")

            # Create indexes for optimal query performance
            await self.create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.warning(
                "MongoDB connection failed (%s). "
                "Diagnosis history will not be persisted.",
                exc,
            )
            self._client = None
            self._db = None

    async def close(self) -> None:
        """Close the MongoDB client connection pool."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed.")

    async def create_indexes(self) -> None:
        """
        Create optimised indexes on the diagnoses collection.

        Index strategy:
          - session_id:   Unique index for O(1) lookups by session
          - timestamp:    Descending for fast "newest first" pagination
          - crop.name:    For filtering history by crop
          - disease.name: For filtering history by disease
          - text index:   Full-text search across crop, disease, and explanation
          - action_plan.risk_score: For filtering high-risk diagnoses
        """
        if self._db is None:
            return

        collection = self._db[DIAGNOSES_COLLECTION]
        try:
            # Unique index on session_id
            await collection.create_index(
                [("session_id", ASCENDING)],
                unique=True,
                name="idx_session_id_unique",
                background=True,
            )

            # Descending timestamp for newest-first pagination
            await collection.create_index(
                [("timestamp", DESCENDING)],
                name="idx_timestamp_desc",
                background=True,
            )

            # Compound index for common history filters
            await collection.create_index(
                [("crop.name", ASCENDING), ("timestamp", DESCENDING)],
                name="idx_crop_name_timestamp",
                background=True,
            )
            await collection.create_index(
                [("disease.name", ASCENDING), ("timestamp", DESCENDING)],
                name="idx_disease_name_timestamp",
                background=True,
            )

            # Risk score index for high-risk dashboards
            await collection.create_index(
                [("action_plan.risk_score", DESCENDING)],
                name="idx_risk_score_desc",
                background=True,
                sparse=True,  # sparse because older docs may not have action_plan
            )

            # Full-text search index
            await collection.create_index(
                [
                    ("crop.name", TEXT),
                    ("disease.name", TEXT),
                    ("explanation", TEXT),
                ],
                name="idx_text_search",
                background=True,
                weights={"crop.name": 10, "disease.name": 10, "explanation": 1},
            )

            logger.info(
                "MongoDB indexes created/verified on '%s' collection.",
                DIAGNOSES_COLLECTION,
            )
        except Exception as exc:
            logger.warning("Index creation failed (non-fatal): %s", exc)

    # ─── Property accessors ────────────────────────────────────────────────────

    @property
    def client(self) -> AsyncIOMotorClient | None:
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase | None:
        return self._db

    @property
    def is_connected(self) -> bool:
        return self._db is not None

    def get_collection(self, name: str):
        if self._db is None:
            return None
        return self._db[name]


# ─── Singleton ────────────────────────────────────────────────────────────────
mongodb_manager = MongoDBManager()
