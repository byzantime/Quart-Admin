"""Shared fixtures and configuration for tests."""

from unittest.mock import MagicMock

import pytest
from quart import Quart

from quart_admin.config import QuartAdminConfig
from quart_admin.database.base import DatabaseProvider


@pytest.fixture
def test_app():
    """Create a test Quart application."""
    app = Quart(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


@pytest.fixture
def flask_app():
    """Create a minimal Flask app for instantiating FlaskForm subclasses in unit tests."""
    try:
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        return app
    except ImportError:
        pytest.skip("Flask not available")


@pytest.fixture
def admin_config():
    """Create a test admin configuration."""
    return QuartAdminConfig(
        name="test-admin",
        url_prefix="/test-admin",
        require_auth=False,
    )


@pytest.fixture
def mock_database_provider():
    """Create a mock database provider."""
    provider = MagicMock(spec=DatabaseProvider)

    provider.get_all.return_value = []
    provider.get_by_pk.return_value = None
    provider.create.return_value = {"id": 1}
    provider.update.return_value = {"id": 1}
    provider.delete.return_value = True
    provider.count.return_value = 0
    provider.get_model_fields.return_value = []
    provider.get_model_relationships.return_value = {}

    return provider


@pytest.fixture
def mock_sqlalchemy_model():
    """Create a mock SQLAlchemy model for testing."""
    mock_model = MagicMock()
    mock_model.__name__ = "TestModel"
    mock_model.__tablename__ = "test_models"
    return mock_model


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_sqlalchemy: mark test as requiring SQLAlchemy"
    )
    config.addinivalue_line(
        "markers", "requires_wtforms: mark test as requiring WTForms"
    )
    config.addinivalue_line(
        "markers", "requires_quart_auth: mark test as requiring Quart-Auth"
    )
