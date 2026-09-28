"""Test the SQLAlchemy database provider using mocks."""

from unittest.mock import DEFAULT
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
            mock_select = MagicMock()
            mock_func = MagicMock()
            mock_inspect = MagicMock()
            mock_or_ = MagicMock()
            mock_desc = MagicMock()
            mock_unicode = MagicMock()
            mock_sql_cast = MagicMock()

            with patch.multiple(
                "quart_admin.database.sqlalchemy",
                select=mock_select,
                func=mock_func,
                inspect=mock_inspect,
                or_=mock_or_,
                desc=mock_desc,
                Unicode=mock_unicode,
                sql_cast=mock_sql_cast,
            ):
                yield {
                    "select": mock_select,
                    "func": mock_func,
                    "inspect": mock_inspect,
                    "or_": mock_or_,
                    "desc": mock_desc,
                    "Unicode": mock_unicode,
                    "sql_cast": mock_sql_cast,
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

        mock_column = MagicMock()
        mock_column.name = "id"
        mock_column.type = "INTEGER"
        mock_column.nullable = False
        mock_column.primary_key = True
        mock_column.default = None

        mock_inspector = MagicMock()
        mock_inspector.columns = [mock_column]
        mock_inspector.relationships = []

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

        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_instance]
        mock_session.execute.return_value = mock_result

        with patch.object(
            sqlalchemy_provider, "_model_to_dict", return_value={"id": 1}
        ) as mock_to_dict:
            result = await sqlalchemy_provider.get_all(mock_model, mock_session)

            assert result == [{"id": 1}]
            mock_to_dict.assert_called_once_with(mock_instance)

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

        mock_column = MagicMock()
        mock_model.status = mock_column

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(mock_model, mock_session, status="active")

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

        result = await sqlalchemy_provider.create(mock_model, mock_session, name="test")

        assert result is mock_instance
        mock_model.assert_called_once_with(name="test")
        mock_session.add.assert_called_once_with(mock_instance)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_update(self, sqlalchemy_provider, mock_model, mock_session_factory):
        """Test update method."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_instance = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_instance
        mock_session.execute.return_value = mock_result

        mock_instance.name = None

        result = await sqlalchemy_provider.update(
            mock_model, mock_session, {"id": 1}, name="updated"
        )

        assert result is mock_instance
        assert mock_instance.name == "updated"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_instance)
        mock_session.commit.assert_called_once()

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

        assert result is mock_instance
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
        assert result is None

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

        mock_count = MagicMock()
        mock_sqlalchemy_modules["func"].count.return_value = mock_count
        mock_select_query = MagicMock()
        mock_select_query.select_from.return_value = mock_select_query
        mock_sqlalchemy_modules["select"].return_value = mock_select_query

        result = await sqlalchemy_provider.count(mock_model, mock_session)
        assert result == 5

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
        assert len(result) == 0
        mock_sqlalchemy_modules["inspect"].assert_called_with(mock_model)

    def test_model_to_dict(
        self, sqlalchemy_provider, mock_model, mock_sqlalchemy_modules
    ):
        """Test _model_to_dict method."""
        mock_instance = MagicMock()
        mock_instance.__class__ = mock_model

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

    async def test_get_all_with_limit_offset(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all applies SQL LIMIT and OFFSET instead of in-Python slicing."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model, mock_session, limit=10, offset=20
            )

        mock_query.limit.assert_called_once_with(10)
        mock_query.offset.assert_called_once_with(20)

    async def test_get_all_with_search_single_term(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all builds an ilike WHERE clause for a single search term."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query

        mock_sql_cast = mock_sqlalchemy_modules["sql_cast"]
        mock_or_ = mock_sqlalchemy_modules["or_"]

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                search="foo",
                searchable_columns=["name"],
            )

        mock_sql_cast.return_value.ilike.assert_called_once_with("%foo%")
        mock_or_.assert_called_once_with(mock_sql_cast.return_value.ilike.return_value)
        mock_query.where.assert_called_once_with(mock_or_.return_value)

    async def test_get_all_with_search_multi_term(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all applies AND logic across multiple search terms."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                search="foo bar",
                searchable_columns=["name"],
            )

        assert mock_query.where.call_count == 2

    async def test_get_all_with_search_prefix_startswith(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all handles '^' prefix to produce a starts-with LIKE pattern."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query

        mock_sql_cast = mock_sqlalchemy_modules["sql_cast"]

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                search="^foo",
                searchable_columns=["name"],
            )

        mock_sql_cast.return_value.ilike.assert_called_once_with("foo%")

    async def test_get_all_with_search_prefix_exact(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all handles '=' prefix to produce an exact-match LIKE pattern."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query

        mock_sql_cast = mock_sqlalchemy_modules["sql_cast"]

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                search="=foo",
                searchable_columns=["name"],
            )

        mock_sql_cast.return_value.ilike.assert_called_once_with("foo")

    async def test_get_all_with_sort_asc(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all applies ascending ORDER BY without desc() wrapper."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_desc = mock_sqlalchemy_modules["desc"]

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                sort_by="name",
                sort_desc=False,
            )

        mock_query.order_by.assert_called_once_with(mock_model.name)
        mock_desc.assert_not_called()

    async def test_get_all_with_sort_desc(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test get_all wraps the column in desc() for descending ORDER BY."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_query = mock_sqlalchemy_modules["select"].return_value
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_desc = mock_sqlalchemy_modules["desc"]

        with patch.object(sqlalchemy_provider, "_model_to_dict", return_value={}):
            await sqlalchemy_provider.get_all(
                mock_model,
                mock_session,
                sort_by="name",
                sort_desc=True,
            )

        mock_desc.assert_called_once_with(mock_model.name)
        mock_query.order_by.assert_called_once_with(mock_desc.return_value)

    async def test_count_with_search(
        self,
        sqlalchemy_provider,
        mock_model,
        mock_session_factory,
        mock_sqlalchemy_modules,
    ):
        """Test count() applies the same ilike search clause for correct pagination totals."""
        _, mock_session = mock_session_factory

        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result

        mock_count = MagicMock()
        mock_sqlalchemy_modules["func"].count.return_value = mock_count
        mock_select_query = MagicMock()
        mock_select_query.select_from.return_value = mock_select_query
        mock_select_query.where.return_value = mock_select_query
        mock_sqlalchemy_modules["select"].return_value = mock_select_query

        mock_sql_cast = mock_sqlalchemy_modules["sql_cast"]
        mock_or_ = mock_sqlalchemy_modules["or_"]

        result = await sqlalchemy_provider.count(
            mock_model,
            mock_session,
            search="foo",
            searchable_columns=["name"],
        )

        assert result == 3
        mock_sql_cast.return_value.ilike.assert_called_once_with("%foo%")
        mock_or_.assert_called_once_with(mock_sql_cast.return_value.ilike.return_value)
        mock_select_query.where.assert_called_once_with(mock_or_.return_value)


class TestSQLAlchemyProviderImportFailure:
    """Test SQLAlchemy provider behavior when import fails."""

    def test_import_fails_without_sqlalchemy_available(self):
        """Test that importing SQLAlchemy provider fails when modules are not available."""
        import sys

        with patch.dict(
            "sys.modules",
            {"sqlalchemy": None, "sqlalchemy.inspection": None},
        ):
            mods_to_clear = [
                k for k in sys.modules if k.startswith("quart_admin.database")
            ]
            for mod in mods_to_clear:
                del sys.modules[mod]

            with pytest.raises(ImportError):
                from quart_admin.database.sqlalchemy import (
                    SQLAlchemyProvider,  # noqa: F401
                )

    def test_import_succeeds_with_mock_sqlalchemy(self):
        """Test that import succeeds when SQLAlchemy modules are mocked."""
        with patch.dict(
            "sys.modules",
            {
                "sqlalchemy": MagicMock(),
                "sqlalchemy.inspection": MagicMock(),
            },
        ):
            with patch.multiple(
                "quart_admin.database.sqlalchemy",
                select=DEFAULT,
                func=DEFAULT,
                inspect=DEFAULT,
            ):
                from quart_admin.database.sqlalchemy import SQLAlchemyProvider

                assert SQLAlchemyProvider is not None
