"""Database providers for Quart-Admin."""

from .base import DatabaseProvider

__all__ = ["DatabaseProvider"]

try:
    from .sqlalchemy import SQLAlchemyProvider

    __all__.append(SQLAlchemyProvider)
except ImportError:
    pass
