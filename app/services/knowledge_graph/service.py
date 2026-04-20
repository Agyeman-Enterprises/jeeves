"""
Unified Knowledge Graph service.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.services.knowledge_graph.db import SessionLocal
from app.services.knowledge_graph.models import Entity, Relationship

LOGGER = logging.getLogger(__name__)


@contextmanager
def get_session() -> Session:
    """Get a database session with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class UnifiedKnowledgeGraph:
    """Service for managing the unified knowledge graph."""

    def upsert_entity(
        self,
        id: str,
        type: str,
        name: str,
        summary: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Entity:
        """
        Create or update an entity.

        Args:
            id: Unique entity identifier
            type: Entity type (e.g., "company", "person", "document")
            name: Entity name
            summary: Optional summary/description
            metadata: Optional metadata dictionary

        Returns:
            Entity object
        """
        with get_session() as session:
            entity = session.query(Entity).filter(Entity.id == id).first()

            if entity:
                # Update existing
                entity.type = type
                entity.name = name
                if summary is not None:
                    entity.summary = summary
                if metadata:
                    # Merge metadata
                    current_meta = entity.extra_data or {}
                    current_meta.update(metadata)
                    entity.extra_data = current_meta
                entity.updated_at = Entity.updated_at.property.columns[0].default.arg()
            else:
                # Create new
                entity = Entity(
                    id=id,
                    type=type,
                    name=name,
                    summary=summary,
                    extra_data=metadata or {},
                )
                session.add(entity)

            session.commit()
            session.refresh(entity)
            return entity

    def upsert_relationship(
        self,
        source_id: str,
        target_id: str,
        type: str,
        metadata: Optional[Dict] = None,
    ) -> Relationship:
        """
        Create a relationship between entities (idempotent).

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            type: Relationship type (e.g., "OWNS", "MENTIONS")
            metadata: Optional metadata

        Returns:
            Relationship object
        """
        with get_session() as session:
            # Check if relationship already exists
            rel = (
                session.query(Relationship)
                .filter(
                    Relationship.source_id == source_id,
                    Relationship.target_id == target_id,
                    Relationship.type == type,
                )
                .first()
            )

            if not rel:
                rel = Relationship(
                    source_id=source_id,
                    target_id=target_id,
                    type=type,
                    extra_data=metadata or {},
                )
                session.add(rel)
                session.commit()
                session.refresh(rel)
            else:
                # Update metadata if provided
                if metadata:
                    current_meta = rel.extra_data or {}
                    current_meta.update(metadata)
                    rel.extra_data = current_meta
                    session.commit()
                    session.refresh(rel)

            return rel

    def get_entity(self, id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        with get_session() as session:
            return session.query(Entity).filter(Entity.id == id).first()

    def find_entities(
        self,
        type: Optional[str] = None,
        name_query: Optional[str] = None,
        limit: int = 50,
    ) -> List[Entity]:
        """
        Find entities by type and/or name.

        Args:
            type: Filter by entity type
            name_query: Search in entity name (case-insensitive substring)
            limit: Maximum results

        Returns:
            List of matching entities
        """
        with get_session() as session:
            query = session.query(Entity)

            if type:
                query = query.filter(Entity.type == type)

            if name_query:
                query = query.filter(Entity.name.ilike(f"%{name_query}%"))

            return query.order_by(Entity.updated_at.desc()).limit(limit).all()

    def neighbors(
        self,
        id: str,
        max_depth: int = 1,
        edge_types: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get entity and its neighbors.

        Args:
            id: Entity ID
            max_depth: Maximum traversal depth (currently supports 1)
            edge_types: Optional filter by relationship types

        Returns:
            Dictionary with entity and neighbors grouped by relationship type
        """
        with get_session() as session:
            entity = session.query(Entity).filter(Entity.id == id).first()
            if not entity:
                return {"entity": None, "neighbors": {}}

            result = {
                "entity": {
                    "id": entity.id,
                    "type": entity.type,
                    "name": entity.name,
                    "summary": entity.summary,
                    "metadata": entity.extra_data,
                },
                "neighbors": {},
            }

            # Get outgoing relationships
            outgoing_query = session.query(Relationship).filter(Relationship.source_id == id)
            if edge_types:
                outgoing_query = outgoing_query.filter(Relationship.type.in_(edge_types))

            for rel in outgoing_query.all():
                target = session.query(Entity).filter(Entity.id == rel.target_id).first()
                if target:
                    rel_type = rel.type
                    if rel_type not in result["neighbors"]:
                        result["neighbors"][rel_type] = []
                    result["neighbors"][rel_type].append({
                        "id": target.id,
                        "type": target.type,
                        "name": target.name,
                        "summary": target.summary,
                        "metadata": target.extra_data,
                        "relationship_metadata": rel.extra_data,
                    })

            # Get incoming relationships
            incoming_query = session.query(Relationship).filter(Relationship.target_id == id)
            if edge_types:
                incoming_query = incoming_query.filter(Relationship.type.in_(edge_types))

            for rel in incoming_query.all():
                source = session.query(Entity).filter(Entity.id == rel.source_id).first()
                if source:
                    rel_type = f"{rel.type}_REVERSE"  # Mark as reverse
                    if rel_type not in result["neighbors"]:
                        result["neighbors"][rel_type] = []
                    result["neighbors"][rel_type].append({
                        "id": source.id,
                        "type": source.type,
                        "name": source.name,
                        "summary": source.summary,
                        "metadata": source.extra_data,
                        "relationship_metadata": rel.extra_data,
                    })

            return result


# Singleton instance
graph = UnifiedKnowledgeGraph()

