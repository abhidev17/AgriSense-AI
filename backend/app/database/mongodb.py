"""
MongoDB connection manager for AgriSense AI.
Uses motor (async MongoDB driver) for non-blocking database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()


class MongoDBManager:
    """
    Async MongoDB connection manager.

    Lifecycle:
        - Call ``connect()`` once at application startup.
        - Call ``close()`` once at application shutdown.
        - Access the database via the ``db`` property after connecting.
    """

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    # ─── Connection management ─────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Open the MongoDB connection and verify it is reachable.
        Logs a warning (but does not crash) if the server is unavailable,
        so the rest of the API can still respond with degraded functionality.
        """
        try:
            logger.info(
                "Connecting to MongoDB at %s (db: %s)…",
                settings.MONGODB_URI,
                settings.MONGODB_DB_NAME,
            )
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5_000,
            )
            # Ping to confirm connection
            await self._client.admin.command("ping")
            self._db = self._client[settings.MONGODB_DB_NAME]
            logger.info("MongoDB connected successfully (OK)")
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

    # ─── Property accessors ────────────────────────────────────────────────────

    @property
    def client(self) -> AsyncIOMotorClient | None:
        """Return the raw AsyncIOMotorClient (may be None if not connected)."""
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase | None:
        """Return the application database handle (may be None if not connected)."""
        return self._db

    @property
    def is_connected(self) -> bool:
        """Return True when a live database handle is available."""
        return self._db is not None

    # ─── Helper: collection access ─────────────────────────────────────────────

    def get_collection(self, name: str):
        """
        Convenience accessor for a named collection.

        Args:
            name: Collection name.

        Returns:
            AsyncIOMotorCollection, or None if the DB is not connected.
        """
        if self._db is None:
            return None
        return self._db[name]


# ─── Singleton instance ────────────────────────────────────────────────────────
# All routes import this object so they share a single connection pool.
mongodb_manager = MongoDBManager()
