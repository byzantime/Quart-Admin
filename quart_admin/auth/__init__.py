"""Authentication providers for Quart-Admin."""

from .base import AuthProvider
from .quart_auth import QuartAuthProvider

__all__ = ["AuthProvider", "QuartAuthProvider"]
