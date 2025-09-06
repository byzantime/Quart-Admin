"""
Quart-Admin: An async admin interface for Quart applications.

A Flask-Admin inspired admin interface built specifically for Quart's async capabilities.
Provides CRUD operations, customizable views, and extensible plugin architecture.
"""

__version__ = "0.1.0"
__author__ = "Octovox Team"

from .admin import QuartAdmin
from .auth.base import AuthProvider
from .database.base import DatabaseProvider
from .views import AdminView
from .views import ModelView

__all__ = [
    "QuartAdmin",
    "AdminView",
    "ModelView",
    "AuthProvider",
    "DatabaseProvider",
]
