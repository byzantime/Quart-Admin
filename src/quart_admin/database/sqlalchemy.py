"""SQLAlchemy database provider implementation."""

from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from sqlalchemy import Unicode
from sqlalchemy import cast as sql_cast
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.inspection import inspect

from .base import DatabaseProvider


def _parse_like_term(term: str) -> str:
    """Convert a search term to a LIKE pattern (mirrors Flask-Admin _apply_search)."""
    if term.startswith("^"):
        return f"{term[1:]}%"
    elif term.startswith("="):
        return term[1:]
    else:
        return f"%{term}%"


class SQLAlchemyProvider(DatabaseProvider):
    """SQLAlchemy database provider implementation."""

    def __init__(self, session_factory=None, engine=None):
        """Initialize SQLAlchemyProvider.

        Args:
            session_factory: SQLAlchemy async session factory.
            engine: SQLAlchemy async engine.
        """
        self.session_factory = session_factory
        self.engine = engine

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Any, None]:
        """Get SQLAlchemy async session context manager."""
        if not self.session_factory:
            raise ValueError("Session factory not configured")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def get_all(
        self, model: Type, session: Any, **filters
    ) -> List[Dict[str, Any]]:
        """Get all records for a SQLAlchemy model."""
        query = select(model)

        limit = filters.pop("limit", None)
        offset = filters.pop("offset", None)
        search = filters.pop("search", None)
        searchable_columns = filters.pop("searchable_columns", [])
        sort_by = filters.pop("sort_by", None)
        sort_desc_flag = filters.pop("sort_desc", False)

        # Apply regular column filters
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)

        # Apply search: one .where() per term (AND logic across terms, OR across columns)
        if search and searchable_columns:
            valid_columns = [c for c in searchable_columns if hasattr(model, c)]
            for term in search.split():
                if not term or not valid_columns:
                    continue
                stmt = _parse_like_term(term)
                clause = or_(
                    *[
                        sql_cast(getattr(model, c), Unicode).ilike(stmt)
                        for c in valid_columns
                    ]
                )
                query = query.where(clause)

        if sort_by and hasattr(model, sort_by):
            col = getattr(model, sort_by)
            query = query.order_by(desc(col) if sort_desc_flag else col)

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        result = await session.execute(query)
        records = result.scalars().all()
        return [self._model_to_dict(record) for record in records]

    async def get_by_pk(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get single SQLAlchemy record by primary key values."""
        query = select(model)
        for key, value in pk_values.items():
            query = query.where(getattr(model, key) == value)

        result = await session.execute(query)
        record = result.scalar_one_or_none()
        return self._model_to_dict(record) if record else None

    async def create(
        self, model: Type, session: Any, commit: bool = True, **data
    ) -> Any:
        """Create new SQLAlchemy record.

        Args:
            model: The SQLAlchemy model class
            session: The async session
            commit: Whether to commit the transaction (default True)
            **data: Field values for the new record

        Returns:
            The created model instance
        """
        instance = model(**data)
        session.add(instance)
        await session.flush()  # Get the ID
        if commit:
            await session.commit()
        return instance

    async def update(
        self,
        model: Type,
        session: Any,
        pk_values: Dict[str, Any],
        commit: bool = True,
        **data,
    ) -> Any:
        """Update existing SQLAlchemy record.

        Args:
            model: The SQLAlchemy model class
            session: The async session
            pk_values: Primary key field name to value mapping
            commit: Whether to commit the transaction (default True)
            **data: Field values to update

        Returns:
            The updated model instance
        """
        query = select(model)
        for key, value in pk_values.items():
            query = query.where(getattr(model, key) == value)

        result = await session.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            raise ValueError(f"Record with primary key {pk_values} not found")

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await session.flush()
        await session.refresh(instance)
        if commit:
            await session.commit()
        return instance

    async def get_model_by_pk(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> Optional[Any]:
        """Get model instance by primary key values.

        Args:
            model: The SQLAlchemy model class
            session: The async session
            pk_values: Primary key field name to value mapping

        Returns:
            The model instance or None if not found
        """
        query = select(model)
        for key, value in pk_values.items():
            query = query.where(getattr(model, key) == value)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def delete(
        self, model: Type, session: Any, pk_values: Dict[str, Any], commit: bool = True
    ) -> Optional[Any]:
        """Delete SQLAlchemy record by primary key values.

        Args:
            model: The SQLAlchemy model class
            session: The async session
            pk_values: Primary key field name to value mapping
            commit: Whether to commit the transaction (default True)

        Returns:
            The deleted model instance or None if not found
        """
        instance = await self.get_model_by_pk(model, session, pk_values)

        if not instance:
            return None

        await session.delete(instance)
        if commit:
            await session.commit()
        return instance

    async def count(self, model: Type, session: Any, **filters) -> int:
        """Count SQLAlchemy records."""
        query = select(func.count()).select_from(model)

        filters.pop("limit", None)
        filters.pop("offset", None)
        search = filters.pop("search", None)
        searchable_columns = filters.pop("searchable_columns", [])
        filters.pop("sort_by", None)
        filters.pop("sort_desc", None)

        # Apply regular column filters
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)

        if search and searchable_columns:
            valid_columns = [c for c in searchable_columns if hasattr(model, c)]
            for term in search.split():
                if not term or not valid_columns:
                    continue
                stmt = _parse_like_term(term)
                clause = or_(
                    *[
                        sql_cast(getattr(model, c), Unicode).ilike(stmt)
                        for c in valid_columns
                    ]
                )
                query = query.where(clause)

        result = await session.execute(query)
        return result.scalar()

    def get_model_fields(self, model: Type) -> List[Dict[str, Any]]:
        """Get field information for SQLAlchemy model."""
        inspector = inspect(model)
        fields = []

        for column in inspector.columns:
            field_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "default": (
                    getattr(column.default, "arg", None) if column.default else None
                ),
            }
            fields.append(field_info)

        return fields

    def get_primary_key_fields(self, model: Type) -> List[str]:
        """Get primary key field names for SQLAlchemy model."""
        inspector = inspect(model)
        return [column.name for column in inspector.columns if column.primary_key]

    def get_model_relationships(self, model: Type) -> Dict[str, Dict[str, Any]]:
        """Get relationship information for SQLAlchemy model."""
        inspector = inspect(model)
        relationships = {}

        for relationship in inspector.relationships:
            rel_info = {
                "name": relationship.key,
                "direction": str(relationship.direction),
                "uselist": relationship.uselist,
                "back_populates": relationship.back_populates,
                "related_model": relationship.mapper.class_,
            }
            relationships[relationship.key] = rel_info

        return relationships

    def _model_to_dict(self, instance: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy model instance to dictionary."""
        if instance is None:
            return {}

        inspector = inspect(instance.__class__)
        result = {}

        for column in inspector.columns:
            value = getattr(instance, column.name)
            result[column.name] = value

        return result
