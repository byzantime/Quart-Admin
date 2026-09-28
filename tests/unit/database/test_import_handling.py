"""Test import handling for database providers, specifically the refactored SQLAlchemy import behavior."""

import importlib
import sys
from unittest.mock import patch

import pytest


class TestDatabaseImportHandling:
    """Test the conditional import handling in database module."""

    def test_database_provider_always_importable(self):
        """Test that DatabaseProvider is always importable regardless of SQLAlchemy availability."""
        from quart_admin.database import DatabaseProvider

        assert DatabaseProvider is not None

        import quart_admin.database as db_module

        assert "DatabaseProvider" in db_module.__all__

    def test_sqlalchemy_provider_import_with_sqlalchemy_available(self):
        """Test SQLAlchemyProvider import when SQLAlchemy is available."""
        try:
            import sqlalchemy  # noqa: F401

            sqlalchemy_available = True
        except ImportError:
            sqlalchemy_available = False

        if sqlalchemy_available:
            from quart_admin.database import SQLAlchemyProvider

            assert SQLAlchemyProvider is not None

            import quart_admin.database as db_module

            assert "SQLAlchemyProvider" in db_module.__all__
        else:
            import quart_admin.database as db_module

            assert "SQLAlchemyProvider" not in db_module.__all__

            with pytest.raises(ImportError):
                from quart_admin.database import SQLAlchemyProvider

    @patch.dict("sys.modules", {"sqlalchemy": None})
    def test_sqlalchemy_provider_import_without_sqlalchemy(self):
        """Test SQLAlchemyProvider import when SQLAlchemy is not available."""
        if "quart_admin.database" in sys.modules:
            del sys.modules["quart_admin.database"]
        if "quart_admin.database.sqlalchemy" in sys.modules:
            del sys.modules["quart_admin.database.sqlalchemy"]

        with patch.dict(
            "sys.modules", {"sqlalchemy": None, "sqlalchemy.inspection": None}
        ):
            import quart_admin.database as db_module

            importlib.reload(db_module)

            assert hasattr(db_module, "DatabaseProvider")
            assert "DatabaseProvider" in db_module.__all__

            assert not hasattr(db_module, "SQLAlchemyProvider")
            assert "SQLAlchemyProvider" not in db_module.__all__

    def test_sqlalchemy_provider_import_with_mock_failure(self):
        """Test import handling when SQLAlchemy import fails."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("sqlalchemy"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            if "quart_admin.database" in sys.modules:
                del sys.modules["quart_admin.database"]
            if "quart_admin.database.sqlalchemy" in sys.modules:
                del sys.modules["quart_admin.database.sqlalchemy"]

            import quart_admin.database as db_module

            assert "DatabaseProvider" in db_module.__all__

            assert "SQLAlchemyProvider" not in db_module.__all__

    def test_direct_sqlalchemy_provider_import_fails_gracefully(self):
        """Test that direct import of SQLAlchemyProvider fails gracefully when SQLAlchemy unavailable."""
        try:
            import sqlalchemy  # noqa: F401

            pytest.skip("SQLAlchemy is available, cannot test failure case")
        except ImportError:
            pass

        with pytest.raises(ImportError):
            from quart_admin.database.sqlalchemy import SQLAlchemyProvider  # noqa: F401

    def test_database_module_all_contents(self):
        """Test that __all__ contains expected items based on availability."""
        import quart_admin.database as db_module

        assert "DatabaseProvider" in db_module.__all__

        for item_name in db_module.__all__:
            assert hasattr(db_module, item_name), (
                f"{item_name} in __all__ but not available"
            )

    def test_no_leftover_import_errors_in_sqlalchemy_provider(self):
        """Test that SQLAlchemy provider doesn't contain old ImportError handling."""
        try:
            import inspect

            import sqlalchemy  # noqa: F401

            from quart_admin.database.sqlalchemy import SQLAlchemyProvider

            source = inspect.getsource(SQLAlchemyProvider)

            assert "ImportError" not in source, (
                "SQLAlchemyProvider still contains ImportError handling"
            )
            assert "pip install quart-admin[sqlalchemy]" not in source, (
                "Old error message still present"
            )

        except ImportError:
            pytest.skip("SQLAlchemy not available, cannot test provider internals")
