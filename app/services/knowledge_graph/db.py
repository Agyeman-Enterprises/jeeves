"""
Database session factory and initialization for knowledge graph.
"""

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.knowledge_graph.models import Base

LOGGER = logging.getLogger(__name__)

# On Railway/cloud, /tmp is always writable. Local dev uses data/.
# Explicit KNOWLEDGE_GRAPH_DB_PATH env var overrides both.
_is_cloud = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("FLY_APP_NAME"))
_default_path = "/tmp/knowledge_graph.db" if _is_cloud else "data/knowledge_graph.db"
DB_PATH = os.getenv("KNOWLEDGE_GRAPH_DB_PATH", _default_path)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_graph_db() -> None:
    """Initialize the knowledge graph database."""
    try:
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        Base.metadata.create_all(bind=engine)
        LOGGER.info("Knowledge graph database initialized at %s", DB_PATH)
    except Exception as exc:
        LOGGER.error("Failed to initialize knowledge graph database: %s", exc)
        raise

