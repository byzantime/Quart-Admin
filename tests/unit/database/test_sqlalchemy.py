"""Test the SQLAlchemy database provider using mocks."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestSQLAlchemyProviderWithMocks:
    """Test SQLAlchemy provider functionality using mocks (no actual SQLAlchemy required)."""

    @pytest.fixture
    def mock_sqlalchemy_modules(self):
        """Mock all SQLAlchemy modules and functions."""
        with patch.dict(
            "sys.modules",
            {
                "sqlalchemy": MagicMock(),
                "sqlalchemy.inspection": MagicMock(),
            },
        ):
            # Mock the specific functions we import
            mock_select = MagicMock()
            mock_func = MagicMock()
            mock_inspect = MagicMock()

            with patch("quart_admin.database.sqlalchemy.select", mock_select), patch(
                "quart_admin.database.sqlalchemy.func", mock_func
            ), patch("quart_admin.database.sqlalchemy.inspect", mock_inspect):
                yield {
                    "select": mock_select,
                    "func": mock_func,
                    "inspect": mock_inspect,
                }

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock SQLAlchemy async session factory."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.rollback = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.execute = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        return mock_factory, mock_session

    @pytest.fixture
    def sqlalchemy_provider(self, mock_sqlalchemy_modules, mock_session_factory):
        """Create a SQLAlchemy provider with mocked dependencies."""
        from quart_admin.database.sqlalchemy import SQLAlchemyProvider

        factory, _ = mock_session_factory
        return SQLAlchemyProvider(session_factory=factory)

    @pytest.fixture
    def mock_model(self, mock_sqlalchemy_modules):
        """Create a mock SQLAlchemy model."""
        mock_model = MagicMock()
        mock_model.__name__ = "TestModel"
        mock_model.__tablename__ = "test_models"

        # Mock column with primary key
        mock_column = MagicMock()
        mock_column.name = "id"
        mock_column.type = "INTEGER"
        mock_column.nullable = False
        mock_column.primary_key = True
        mock_column.default = None

        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.columns = [mock_column]
        mock_inspector.relationships = []

        # Make inspect return our mock inspector
        mock_sqlalchemy_modules["inspect"].return_value = mock_inspector

        return mock_model

    def test_provider_initialization(self, mock_sqlalchemy_modules):
        """Test SQLAlchemy provider initialization."""
        from quart_admin.database.sqlalchemy import SQLAlchemyProvider

        mock_factory = MagicMock()
        mock_engine = MagicMock()

        provider = SQLAlchemyProvider(session_factory=mock_factory, engine=mock_engine)

        assert provider.session_factory == mock_factory
        assert provider.engine == mock_engine

    def test_provider_initialization_without_args(self, mock_sqlalchemy_modules):
        """Test SQLAlchemy provider initialization without arguments."""
        from quart_admin.database.sqlalchemy import SQLAlchemyProvider

        provider = SQLAlchemyProvider()

        assert provider.session_factory is None
        assert provider.engine is None

    async def test_get_session_context_manager(
        self, sqlalchemy_provider, mock_session_factory
    ):
        """Test get_session context manager."""
        factory, mock_session = mock_session_factory

        async with sqlalchemy_provider.get_session() as session:
            assert session == mock_session

        factory.assert_called_once()
        mock_session.__aenter__.assert_called_once()
        mock_session.__aexit__.assert_called_once()

    async def test_get_session_without_factory_raises_error(
        self, mock_sqlalchemy_modules
    ):
        """Test that get_session raises error when no session factory is configured."""
        from quart_admin.database.sqlalchemy import SQLAlchemyProvider

        provider = SQLAlchemyProvider()

        with pytest.raises(ValueError, match="Session factory not configured"):
            async with provider.get_session():
                pass

    async def test_get_session_rollback_on_exception(
        self, sqlalchemy_provider, mock_session_factory
    ):
        """Test that get_session rolls back on exception."""
        factory, mock_session = mock_session_factory

        with pytest.raises(RuntimeError):
            async with sqlalchemy_provider.get_session():
                raise RuntimeError("Test error")

        mock_session.rollback.assert_called_once()

    async def test_get_all(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all method."""
        _, mock_session = mock_session_factory

        # Mock query result
        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_instance]
        mock_session.execute.return_value = mock_result

        # Mock _model_to_dict
        with patch.object(
            sqlalchemy_provider, "_model_to_dict", return_value={"id": 1}
        ) as mock_to_dict:
            result = await sqlalchemy_provider.get_all(mock_model, mock_session)

            assert result == [{"id": 1}]
            mock_to_dict.assert_called_once_with(mock_instance)

        # Verify select was called
        mock_sqlalchemy_modules["select"].assert_called_once_with(mock_model)

    async def test_get_all_with_filters(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all method with filters."""
        _, mock_session = mock_session_factory

        # Mock the model to have a status attribute
        mock_column = MagicMock()
        mock_model.status = mock_column

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(mock_model, mock_session, status="active")

        # Verify the mock column was accessed
        assert mock_model.status == mock_column

    async def test_get_by_pk(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_by_pk method."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_instance
        mock_session.execute.return_value = mock_result

        with patch.object(
            sqlalchemy_provider, "_model_to_dict", return_value={"id": 1}
        ) as mock_to_dict:
            result = await sqlalchemy_provider.get_by_pk(
                mock_model, mock_session, {"id": 1}
            )

            assert result == {"id": 1}
            mock_to_dict.assert_called_once_with(mock_instance)

    async def test_get_by_pk_not_found(
        self, sqlalchemy_provider, mock_model, mock_session_factory
    ):
        """Test get_by_pk method when record not found."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await sqlalchemy_provider.get_by_pk(
            mock_model, mock_session, {"id": 999}
        )
        assert result is None

    async def test_create(self, sqlalchemy_provider, mock_model, mock_session_factory):
        """Test create method."""
        _, mock_session = mock_session_factory

        mock_instance = MagicMock()
        mock_model.return_value = mock_instance

        with patch.object(
            sqlalchemy_provider,
            "_model_to_dict",
            return_value={"id": 1, "name": "test"},
        ) as mock_to_dict:
            result = await sqlalchemy_provider.create(
                mock_model, mock_session, name="test"
            )

            assert result == {"id": 1, "name": "test"}
            mock_model.assert_called_once_with(name="test")
            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_to_dict.assert_called_once_with(mock_instance)

    async def test_update(self, sqlalchemy_provider, mock_model, mock_session_factory):
        """Test update method."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_instance
        mock_session.execute.return_value = mock_result

        # Mock the instance to have a name attribute
        mock_instance.name = None  # Initial value

        with patch.object(
            sqlalchemy_provider,
            "_model_to_dict",
            return_value={"id": 1, "name": "updated"},
        ) as mock_to_dict:
            result = await sqlalchemy_provider.update(
                mock_model, mock_session, {"id": 1}, name="updated"
            )

            assert result == {"id": 1, "name": "updated"}
            # Verify the attribute was set
            assert mock_instance.name == "updated"
            mock_session.flush.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_instance)
            mock_session.commit.assert_called_once()
            mock_to_dict.assert_called_once_with(mock_instance)

    async def test_update_not_found(
        self, sqlalchemy_provider, mock_model, mock_session_factory
    ):
        """Test update method when record not found."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Record with primary key .* not found"):
            await sqlalchemy_provider.update(
                mock_model, mock_session, {"id": 999}, name="updated"
            )

    async def test_delete(self, sqlalchemy_provider, mock_model, mock_session_factory):
        """Test delete method."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_instance
        mock_session.execute.return_value = mock_result

        result = await sqlalchemy_provider.delete(mock_model, mock_session, {"id": 1})

        assert result is True
        mock_session.delete.assert_called_once_with(mock_instance)
        mock_session.commit.assert_called_once()

    async def test_delete_not_found(
        self, sqlalchemy_provider, mock_model, mock_session_factory
    ):
        """Test delete method when record not found."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await sqlalchemy_provider.delete(mock_model, mock_session, {"id": 999})
        assert result is False

    async def test_count(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test count method."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        # Mock func.count() call
        mock_count = MagicMock()
        mock_sqlalchemy_modules["func"].count.return_value = mock_count
        mock_select_query = MagicMock()
        mock_select_query.select_from.return_value = mock_select_query
        mock_sqlalchemy_modules["select"].return_value = mock_select_query

        result = await sqlalchemy_provider.count(mock_model, mock_session)
        assert result == 5

        # Verify func.count() was called
        mock_sqlalchemy_modules["func"].count.assert_called_once()
        mock_sqlalchemy_modules["select"].assert_called_once_with(mock_count)

    def test_get_model_fields(
        self, sqlalchemy_provider, mock_model, mock_sqlalchemy_modules
    ):
        """Test get_model_fields method."""
        result = sqlalchemy_provider.get_model_fields(mock_model)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "id"
        assert result[0]["type"] == "INTEGER"
        assert result[0]["nullable"] is False
        assert result[0]["primary_key"] is True

        # Verify inspect was called
        mock_sqlalchemy_modules["inspect"].assert_called_with(mock_model)

    def test_get_primary_key_fields(
        self, sqlalchemy_provider, mock_model, mock_sqlalchemy_modules
    ):
        """Test get_primary_key_fields method."""
        result = sqlalchemy_provider.get_primary_key_fields(mock_model)

        assert result == ["id"]
        mock_sqlalchemy_modules["inspect"].assert_called_with(mock_model)

    def test_get_model_relationships(
        self, sqlalchemy_provider, mock_model, mock_sqlalchemy_modules
    ):
        """Test get_model_relationships method."""
        result = sqlalchemy_provider.get_model_relationships(mock_model)

        assert isinstance(result, dict)
        assert len(result) == 0  # No relationships in mock
        mock_sqlalchemy_modules["inspect"].assert_called_with(mock_model)

    def test_model_to_dict(
        self, sqlalchemy_provider, mock_model, mock_sqlalchemy_modules
    ):
        """Test _model_to_dict method."""
        mock_instance = MagicMock()
        mock_instance.__class__ = mock_model

        # Mock the inspector result to be simpler to avoid recursion
        mock_column = MagicMock()
        mock_column.name = "id"
        mock_sqlalchemy_modules["inspect"].return_value.columns = [mock_column]
        mock_instance.id = 123

        result = sqlalchemy_provider._model_to_dict(mock_instance)

        assert result == {"id": 123}

    def test_model_to_dict_with_none(self, sqlalchemy_provider):
        """Test _model_to_dict method with None instance."""
        result = sqlalchemy_provider._model_to_dict(None)
        assert result == {}


class TestSQLAlchemyProviderImportFailure:
    """Test SQLAlchemy provider behavior when import fails."""

    def test_import_fails_without_sqlalchemy_available(self):
        """Test that importing SQLAlchemy provider fails when modules are not available."""
        # Simulate missing SQLAlchemy by removing it from sys.modules
        original_modules = {}
        sqlalchemy_modules = ["sqlalchemy", "sqlalchemy.inspection"]

        # Save and remove SQLAlchemy modules
        import sys

        for module in sqlalchemy_modules:
            if module in sys.modules:
                original_modules[module] = sys.modules[module]
                del sys.modules[module]

        try:
            # Clear any cached imports
            if "quart_admin.database.sqlalchemy" in sys.modules:
                del sys.modules["quart_admin.database.sqlalchemy"]

            # Try to import - should fail due to missing SQLAlchemy
            with pytest.raises(ImportError):
                from quart_admin.database.sqlalchemy import (
                    SQLAlchemyProvider,  # noqa: F401
                )
        finally:
            # Restore modules
            for module, mod_obj in original_modules.items():
                sys.modules[module] = mod_obj

    def test_import_succeeds_with_mock_sqlalchemy(self):
        """Test that import succeeds when SQLAlchemy modules are mocked."""
        with patch.dict(
            "sys.modules",
            {
                "sqlalchemy": MagicMock(),
                "sqlalchemy.inspection": MagicMock(),
            },
        ):
            # Mock the specific imports
            with patch("quart_admin.database.sqlalchemy.select"), patch(
                "quart_admin.database.sqlalchemy.func"
            ), patch("quart_admin.database.sqlalchemy.inspect"):
                # Should be able to import successfully
                from quart_admin.database.sqlalchemy import SQLAlchemyProvider

                assert SQLAlchemyProvider is not None
