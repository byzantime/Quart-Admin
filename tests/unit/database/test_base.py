"""Test the DatabaseProvider abstract base class."""

from abc import ABC
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

import pytest

from quart_admin.database.base import DatabaseProvider


class TestDatabaseProvider:
    """Test the DatabaseProvider abstract base class."""

    def test_database_provider_is_abstract(self):
        """Test that DatabaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DatabaseProvider()

    def test_database_provider_inheritance(self):
        """Test that DatabaseProvider is properly set up as an ABC."""
        assert issubclass(DatabaseProvider, ABC)
        assert hasattr(DatabaseProvider, "__abstractmethods__")

        # Check that all expected methods are abstract
        expected_abstract_methods = {
            "get_session",
            "get_all",
            "get_by_pk",
            "create",
            "update",
            "delete",
            "count",
            "get_model_fields",
            "get_model_relationships",
        }
        assert expected_abstract_methods.issubset(DatabaseProvider.__abstractmethods__)

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation of DatabaseProvider can be instantiated."""

        class ConcreteDatabaseProvider(DatabaseProvider):
            async def get_session(self) -> AsyncGenerator[Any, None]:
                yield None

            async def get_all(
                self, model: Type, session: Any, **filters
            ) -> List[Dict[str, Any]]:
                return []

            async def get_by_pk(
                self, model: Type, session: Any, pk_values: Dict[str, Any]
            ) -> Optional[Dict[str, Any]]:
                return None

            async def create(self, model: Type, session: Any, **data) -> Dict[str, Any]:
                return {}

            async def update(
                self, model: Type, session: Any, pk_values: Dict[str, Any], **data
            ) -> Dict[str, Any]:
                return {}

            async def delete(
                self, model: Type, session: Any, pk_values: Dict[str, Any]
            ) -> bool:
                return True

            async def count(self, model: Type, session: Any, **filters) -> int:
                return 0

            def get_model_fields(self, model: Type) -> List[Dict[str, Any]]:
                return []

            def get_model_relationships(self, model: Type) -> Dict[str, Dict[str, Any]]:
                return {}

        # Should be able to instantiate concrete implementation
        provider = ConcreteDatabaseProvider()
        assert isinstance(provider, DatabaseProvider)

    def test_partial_implementation_cannot_be_instantiated(self):
        """Test that partial implementations cannot be instantiated."""

        class PartialDatabaseProvider(DatabaseProvider):
            async def get_session(self) -> AsyncGenerator[Any, None]:
                yield None

            async def get_all(
                self, model: Type, session: Any, **filters
            ) -> List[Dict[str, Any]]:
                return []

            # Missing other required methods

        with pytest.raises(TypeError):
            PartialDatabaseProvider()

    def test_method_signatures(self):
        """Test that the abstract methods have correct signatures."""
        import inspect

        # Test get_session signature
        sig = inspect.signature(DatabaseProvider.get_session)
        assert len(sig.parameters) == 1  # self only
        assert sig.return_annotation == AsyncGenerator[Any, None]

        # Test get_all signature
        sig = inspect.signature(DatabaseProvider.get_all)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "filters"]
        assert sig.return_annotation == List[Dict[str, Any]]

        # Test get_by_pk signature
        sig = inspect.signature(DatabaseProvider.get_by_pk)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "pk_values"]
        assert sig.return_annotation == Optional[Dict[str, Any]]

        # Test create signature
        sig = inspect.signature(DatabaseProvider.create)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "data"]
        assert sig.return_annotation == Dict[str, Any]

        # Test update signature
        sig = inspect.signature(DatabaseProvider.update)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "pk_values", "data"]
        assert sig.return_annotation == Dict[str, Any]

        # Test delete signature
        sig = inspect.signature(DatabaseProvider.delete)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "pk_values"]
        assert sig.return_annotation is bool

        # Test count signature
        sig = inspect.signature(DatabaseProvider.count)
        params = list(sig.parameters.keys())
        assert params == ["self", "model", "session", "filters"]
        assert sig.return_annotation is int

        # Test get_model_fields signature
        sig = inspect.signature(DatabaseProvider.get_model_fields)
        params = list(sig.parameters.keys())
        assert params == ["self", "model"]
        assert sig.return_annotation == List[Dict[str, Any]]

        # Test get_model_relationships signature
        sig = inspect.signature(DatabaseProvider.get_model_relationships)
        params = list(sig.parameters.keys())
        assert params == ["self", "model"]
        assert sig.return_annotation == Dict[str, Dict[str, Any]]
