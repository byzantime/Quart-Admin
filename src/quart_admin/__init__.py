"""
Quart-Admin: An async admin interface for Quart applications.

A Flask-Admin inspired admin interface built specifically for Quart's async capabilities.
Provides CRUD operations, customizable views, and extensible plugin architecture.
"""

__version__ = "0.1.0"
__author__ = "Hugo Baldwin"

from .admin import QuartAdmin
from .auth.base import AuthProvider
from .auth.helpers import create_combined_check
from .auth.helpers import create_domain_check
from .auth.helpers import create_email_list_check
from .auth.helpers import quart_auth_user_loader
from .database.base import DatabaseProvider
from .views import AdminView
from .views import ModelView

__all__ = [
    "QuartAdmin",
    "AdminView",
    "ModelView",
    "AuthProvider",
    "DatabaseProvider",
    "create_domain_check",
    "create_email_list_check",
    "create_combined_check",
    "quart_auth_user_loader",
]
