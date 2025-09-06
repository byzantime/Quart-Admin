"""Authentication helper functions."""

from typing import Callable
from typing import List


def create_domain_check(allowed_domains: List[str]) -> Callable:
    """Create a domain check function for admin access.

    Args:
        allowed_domains: List of allowed email domains (e.g., ['@company.com', '@example.com'])

    Returns:
        Function that checks if user email ends with allowed domain

    Example:
        >>> staff_check = create_domain_check(['@example.com'])
        >>> staff_check({'email': 'user@example.com'})  # Returns True
        >>> staff_check({'email': 'user@other.com'})   # Returns False
    """
    # Normalize domains to ensure they start with @
    normalized_domains = []
    for domain in allowed_domains:
        if not domain.startswith("@"):
            domain = "@" + domain
        normalized_domains.append(domain)

    def check_domain(user_data):
        if not user_data or not user_data.get("email"):
            return False

        email = user_data["email"].lower()
        return any(email.endswith(domain.lower()) for domain in normalized_domains)

    return check_domain


def create_email_list_check(allowed_emails: List[str]) -> Callable:
    """Create an email allowlist check function for admin access.

    Args:
        allowed_emails: List of specific allowed email addresses

    Returns:
        Function that checks if user email is in the allowed list

    Example:
        >>> admin_check = create_email_list_check(['admin@example.com'])
        >>> admin_check({'email': 'admin@example.com'})  # Returns True
        >>> admin_check({'email': 'user@example.com'})   # Returns False
    """
    # Normalize emails to lowercase for comparison
    normalized_emails = {email.lower() for email in allowed_emails}

    def check_email(user_data):
        if not user_data or not user_data.get("email"):
            return False

        return user_data["email"].lower() in normalized_emails

    return check_email


def create_combined_check(*check_functions: Callable) -> Callable:
    """Create a combined check that passes if ANY of the provided checks pass.

    Args:
        *check_functions: Multiple check functions to combine with OR logic

    Returns:
        Function that returns True if any check function returns True

    Example:
        >>> domain_check = create_domain_check(['@example.com'])
        >>> email_check = create_email_list_check(['admin@external.com'])
        >>> combined = create_combined_check(domain_check, email_check)
        >>> combined({'email': 'user@example.com'})     # True (domain match)
        >>> combined({'email': 'admin@external.com'})  # True (email match)
        >>> combined({'email': 'user@other.com'})      # False (no match)
    """

    def check_any(user_data):
        return any(check_func(user_data) for check_func in check_functions)

    return check_any


async def quart_auth_user_loader():
    """Create a standard user loader for Quart-Auth integration.

    Returns:
        Async function that loads user data from Quart's g object
    """
    from quart import g

    user = g.user if hasattr(g, "user") else None
    if not user:
        return None

    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "name": getattr(user, "name", None),
        "authenticated": True,
    }
