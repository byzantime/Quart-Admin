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

        # Should also be in __all__
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
            # Should be able to import SQLAlchemyProvider
            from quart_admin.database import SQLAlchemyProvider

            assert SQLAlchemyProvider is not None

            # Should be in __all__
            import quart_admin.database as db_module

            assert "SQLAlchemyProvider" in db_module.__all__
        else:
            # Should not be able to import SQLAlchemyProvider
            import quart_admin.database as db_module

            assert "SQLAlchemyProvider" not in db_module.__all__

            with pytest.raises(ImportError):
                from quart_admin.database import SQLAlchemyProvider

    @patch.dict("sys.modules", {"sqlalchemy": None})
    def test_sqlalchemy_provider_import_without_sqlalchemy(self):
        """Test SQLAlchemyProvider import when SQLAlchemy is not available."""
        # Force reload to simulate fresh import without SQLAlchemy
        if "quart_admin.database" in sys.modules:
            del sys.modules["quart_admin.database"]
        if "quart_admin.database.sqlalchemy" in sys.modules:
            del sys.modules["quart_admin.database.sqlalchemy"]

        # Mock SQLAlchemy as unavailable
        with patch.dict(
            "sys.modules", {"sqlalchemy": None, "sqlalchemy.inspection": None}
        ):
            # Re-import the module
            import quart_admin.database as db_module

            importlib.reload(db_module)

            # DatabaseProvider should still be available
            assert hasattr(db_module, "DatabaseProvider")
            assert "DatabaseProvider" in db_module.__all__

            # SQLAlchemyProvider should not be available
            assert not hasattr(db_module, "SQLAlchemyProvider")
            assert "SQLAlchemyProvider" not in db_module.__all__

    def test_sqlalchemy_provider_import_with_mock_failure(self):
        """Test import handling when SQLAlchemy import fails."""
        # Simulate SQLAlchemy import failure
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("sqlalchemy"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Force reload
            if "quart_admin.database" in sys.modules:
                del sys.modules["quart_admin.database"]
            if "quart_admin.database.sqlalchemy" in sys.modules:
                del sys.modules["quart_admin.database.sqlalchemy"]

            import quart_admin.database as db_module

            # DatabaseProvider should be available
            assert "DatabaseProvider" in db_module.__all__

            # SQLAlchemyProvider should not be in __all__ due to import failure
            assert "SQLAlchemyProvider" not in db_module.__all__

    def test_direct_sqlalchemy_provider_import_fails_gracefully(self):
        """Test that direct import of SQLAlchemyProvider fails gracefully when SQLAlchemy unavailable."""
        try:
            import sqlalchemy  # noqa: F401

            pytest.skip("SQLAlchemy is available, cannot test failure case")
        except ImportError:
            pass

        # Attempting to import SQLAlchemyProvider directly should fail
        with pytest.raises(ImportError):
            from quart_admin.database.sqlalchemy import SQLAlchemyProvider  # noqa: F401

    def test_database_module_all_contents(self):
        """Test that __all__ contains expected items based on availability."""
        import quart_admin.database as db_module

        # DatabaseProvider should always be present
        assert "DatabaseProvider" in db_module.__all__

        # Check that __all__ only contains what's actually importable
        for item_name in db_module.__all__:
            assert hasattr(
                db_module, item_name
            ), f"{item_name} in __all__ but not available"

    def test_no_leftover_import_errors_in_sqlalchemy_provider(self):
        """Test that SQLAlchemy provider doesn't contain old ImportError handling."""
        try:
            # This test only runs if SQLAlchemy is available
            # Read the source code to ensure no ImportError handling remains
            import inspect

            import sqlalchemy  # noqa: F401

            from quart_admin.database.sqlalchemy import SQLAlchemyProvider

            source = inspect.getsource(SQLAlchemyProvider)

            # Should not contain any ImportError handling for SQLAlchemy
            assert (
                "ImportError" not in source
            ), "SQLAlchemyProvider still contains ImportError handling"
            assert (
                "pip install quart-admin[sqlalchemy]" not in source
            ), "Old error message still present"

        except ImportError:
            pytest.skip("SQLAlchemy not available, cannot test provider internals")
