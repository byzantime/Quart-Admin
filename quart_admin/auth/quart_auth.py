"""Quart-Auth integration provider."""

from typing import Any
from typing import Dict
from typing import Optional

from .base import AuthProvider


class QuartAuthProvider(AuthProvider):
    """Authentication provider for Quart-Auth integration."""

    def __init__(self, user_loader=None, admin_check=None):
        """Initialize QuartAuthProvider.

        Args:
            user_loader: Optional callable to load user data from authenticated user.
            admin_check: Optional callable to check if user has admin privileges.
        """
        self.user_loader = user_loader
        self.admin_check = admin_check

    async def is_authenticated(self) -> bool:
        """Check if current user is authenticated using Quart-Auth."""
        try:
            from quart_auth import current_user

            return await current_user.is_authenticated
        except ImportError as err:
            raise ImportError("Quart-Auth is not installed.") from err

    async def has_admin_access(self) -> bool:
        """Check if current user has admin access privileges."""
        if not await self.is_authenticated():
            return False

        if self.admin_check:
            user = await self.get_current_user()
            return self.admin_check(user)

        # Default: any authenticated user has admin access
        return True

    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information from Quart-Auth."""
        try:
            from quart_auth import current_user

            if not await current_user.is_authenticated:
                return None

            if self.user_loader:
                return await self.user_loader()

            # Default: return basic user info
            return {"id": await current_user.auth_id, "authenticated": True}
        except ImportError as err:
            raise ImportError(
                "Quart-Auth is not installed. Please install with: pip install"
                " quart-auth"
            ) from err

    async def get_user_identifier(self) -> Optional[str]:
        """Get unique identifier for current user."""
        try:
            from quart_auth import current_user

            if not await current_user.is_authenticated:
                return None

            return await current_user.auth_id
        except ImportError as err:
            raise ImportError("Quart-Auth is not installed.") from err
