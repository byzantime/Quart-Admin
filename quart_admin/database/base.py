"""Base database provider interface."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional
from typing import Type


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""

    @abstractmethod
    async def get_session(self) -> AsyncGenerator[Any, None]:
        """Get database session context manager.

        Yields:
            Database session object.
        """
        pass

    @abstractmethod
    async def get_all(
        self, model: Type, session: Any, **filters
    ) -> List[Dict[str, Any]]:
        """Get all records for a model.

        Args:
            model: Model class to query.
            session: Database session.
            **filters: Optional filters to apply.

        Returns:
            List[Dict[str, Any]]: List of records as dictionaries.
        """
        pass

    @abstractmethod
    async def get_by_pk(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get single record by primary key values.

        Args:
            model: Model class to query.
            session: Database session.
            pk_values: Dictionary of primary key field names and values.

        Returns:
            Optional[Dict[str, Any]]: Record as dictionary or None.
        """
        pass

    @abstractmethod
    async def create(self, model: Type, session: Any, **data) -> Dict[str, Any]:
        """Create new record.

        Args:
            model: Model class to create.
            session: Database session.
            **data: Record data.

        Returns:
            Dict[str, Any]: Created record as dictionary.
        """
        pass

    @abstractmethod
    async def update(
        self, model: Type, session: Any, pk_values: Dict[str, Any], **data
    ) -> Dict[str, Any]:
        """Update existing record.

        Args:
            model: Model class to update.
            session: Database session.
            pk_values: Dictionary of primary key field names and values.
            **data: Updated data.

        Returns:
            Dict[str, Any]: Updated record as dictionary.
        """
        pass

    @abstractmethod
    async def delete(
        self, model: Type, session: Any, pk_values: Dict[str, Any]
    ) -> bool:
        """Delete record by primary key values.

        Args:
            model: Model class.
            session: Database session.
            pk_values: Dictionary of primary key field names and values.

        Returns:
            bool: True if deleted successfully.
        """
        pass

    @abstractmethod
    async def count(self, model: Type, session: Any, **filters) -> int:
        """Count records for a model.

        Args:
            model: Model class to count.
            session: Database session.
            **filters: Optional filters to apply.

        Returns:
            int: Total count of records.
        """
        pass

    @abstractmethod
    def get_model_fields(self, model: Type) -> List[Dict[str, Any]]:
        """Get field information for a model.

        Args:
            model: Model class.

        Returns:
            List[Dict[str, Any]]: List of field definitions.
        """
        pass

    @abstractmethod
    def get_model_relationships(self, model: Type) -> Dict[str, Dict[str, Any]]:
        """Get relationship information for a model.

        Args:
            model: Model class.

        Returns:
            Dict[str, Dict[str, Any]]: Relationship definitions.
        """
        pass
