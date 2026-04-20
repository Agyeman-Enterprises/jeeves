"""
SQLAlchemy models for Unified Knowledge Graph.
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Entity(Base):
    """Entity node in the knowledge graph."""

    __tablename__ = "entities"

    id = Column(String, primary_key=True)  # e.g. "company:agyeman-enterprises"
    type = Column(String, index=True)  # e.g. "company", "person", "project"
    name = Column(String, index=True)
    summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column("metadata", JSON, default={})  # arbitrary attrs

    outgoing = relationship(
        "Relationship",
        back_populates="source",
        foreign_keys="Relationship.source_id",
        cascade="all, delete-orphan",
    )
    incoming = relationship(
        "Relationship",
        back_populates="target",
        foreign_keys="Relationship.target_id",
        cascade="all, delete-orphan",
    )


class Relationship(Base):
    """Relationship edge in the knowledge graph."""

    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, index=True)  # e.g. "OWNS", "MENTIONS"
    source_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    target_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column("metadata", JSON, default={})

    source = relationship("Entity", foreign_keys=[source_id], back_populates="outgoing")
    target = relationship("Entity", foreign_keys=[target_id], back_populates="incoming")

    __table_args__ = (
        Index("ix_relations_src_type", "source_id", "type"),
        Index("ix_relations_tgt_type", "target_id", "type"),
        UniqueConstraint("source_id", "target_id", "type", name="uq_relationship"),
    )


# Separate index on Entity table (can't reference Entity inside Relationship class body)
Index("ix_entities_type_name", Entity.type, Entity.name)

