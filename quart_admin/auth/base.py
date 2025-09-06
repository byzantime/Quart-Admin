"""Base authentication provider interface."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Optional


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check if current user is authenticated.

        Returns:
            bool: True if user is authenticated, False otherwise.
        """
        pass

    @abstractmethod
    async def has_admin_access(self) -> bool:
        """Check if current user has admin access privileges.

        Returns:
            bool: True if user has admin access, False otherwise.
        """
        pass

    @abstractmethod
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information.

        Returns:
            Optional[Dict[str, Any]]: User information dict or None if not authenticated.
        """
        pass

    @abstractmethod
    async def get_user_identifier(self) -> Optional[str]:
        """Get unique identifier for current user.

        Returns:
            Optional[str]: User identifier or None if not authenticated.
        """
        pass

    async def login_required(self, f):
        """Decorator to require authentication.

        Args:
            f: Function to protect with authentication.

        Returns:
            Decorated function that checks authentication.
        """
        from functools import wraps

        from quart import abort

        @wraps(f)
        async def decorated_function(*args, **kwargs):
            if not await self.is_authenticated():
                abort(401, "Authentication required")
            return await f(*args, **kwargs)

        return decorated_function

    async def admin_required(self, f):
        """Decorator to require admin access.

        Args:
            f: Function to protect with admin access check.

        Returns:
            Decorated function that checks admin access.
        """
        from functools import wraps

        from quart import abort

        @wraps(f)
        async def decorated_function(*args, **kwargs):
            if not await self.is_authenticated():
                abort(401, "Authentication required")
            if not await self.has_admin_access():
                abort(403, "Admin access required")
            return await f(*args, **kwargs)

        return decorated_function
