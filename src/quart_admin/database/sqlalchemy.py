"""SQLAlchemy database provider implementation."""

from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from .base import DatabaseProvider


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
        try:
            from sqlalchemy import select
        except ImportError as err:
            raise ImportError(
                "SQLAlchemy is not installed. Install with: pip install quart-admin[sqlalchemy]"
            ) from err

        query = select(model)

        # Handle special filters
        filters.pop("search", None)

        # Apply regular column filters
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)

        # TODO: Implement proper search functionality
        # For now, ignore search to get basic listing working
        # In a full implementation, this would search across searchable columns

        result = await session.execute(query)
        records = result.scalars().all()
        return [self._model_to_dict(record) for record in records]

    async def get_by_pk(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get single SQLAlchemy record by primary key values."""
        try:
            from sqlalchemy import select
        except ImportError as err:
            raise ImportError(
                "SQLAlchemy is not installed. Install with: pip install quart-admin[sqlalchemy]"
            ) from err

        query = select(model)
        for key, value in pk_values.items():
            query = query.where(getattr(model, key) == value)

        result = await session.execute(query)
        record = result.scalar_one_or_none()
        return self._model_to_dict(record) if record else None

    async def create(self, model: Type, session: Any, **data) -> Dict[str, Any]:
        """Create new SQLAlchemy record."""
        instance = model(**data)
        session.add(instance)
        await session.flush()  # Get the ID
        result_dict = self._model_to_dict(instance)
        await session.commit()
        return result_dict

    async def update(
        self, model: Type, session: Any, pk_values: Dict[str, Any], **data
    ) -> Dict[str, Any]:
        """Update existing SQLAlchemy record."""
        try:
            from sqlalchemy import select
        except ImportError as err:
            raise ImportError(
                "SQLAlchemy is not installed. Install with: pip install quart-admin[sqlalchemy]"
            ) from err

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
        result_dict = self._model_to_dict(instance)
        await session.commit()
        return result_dict

    async def delete(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> bool:
        """Delete SQLAlchemy record by primary key values."""
        try:
            from sqlalchemy import select
        except ImportError as err:
            raise ImportError(
                "SQLAlchemy is not installed. Install with: pip install quart-admin[sqlalchemy]"
            ) from err

        query = select(model)
        for key, value in pk_values.items():
            query = query.where(getattr(model, key) == value)

        result = await session.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            return False

        await session.delete(instance)
        await session.commit()
        return True

    async def count(self, model: Type, session: Any, **filters) -> int:
        """Count SQLAlchemy records."""
        try:
            from sqlalchemy import func
            from sqlalchemy import select
        except ImportError as err:
            raise ImportError(
                "SQLAlchemy is not installed. Install with: pip install quart-admin[sqlalchemy]"
            ) from err

        query = select(func.count()).select_from(model)

        # Handle special filters
        filters.pop("search", None)

        # Apply regular column filters
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)

        # TODO: Implement proper search functionality
        # For now, ignore search to get basic listing working

        result = await session.execute(query)
        return result.scalar()

    def get_model_fields(self, model: Type) -> List[Dict[str, Any]]:
        """Get field information for SQLAlchemy model."""
        try:
            from sqlalchemy.inspection import inspect
        except ImportError as err:
            raise ImportError("SQLAlchemy is not installed") from err

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
        try:
            from sqlalchemy.inspection import inspect
        except ImportError as err:
            raise ImportError("SQLAlchemy is not installed") from err

        inspector = inspect(model)
        return [column.name for column in inspector.columns if column.primary_key]

    def get_model_relationships(self, model: Type) -> Dict[str, Dict[str, Any]]:
        """Get relationship information for SQLAlchemy model."""
        try:
            from sqlalchemy.inspection import inspect
        except ImportError as err:
            raise ImportError("SQLAlchemy is not installed") from err

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

        try:
            from sqlalchemy.inspection import inspect
        except ImportError as err:
            raise ImportError("SQLAlchemy is not installed") from err

        inspector = inspect(instance.__class__)
        result = {}

        for column in inspector.columns:
            value = getattr(instance, column.name)
            result[column.name] = value

        return result
