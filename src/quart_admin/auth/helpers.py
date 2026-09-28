"""Authentication helper functions."""

from typing import Callable
from typing import List


def create_domain_check(allowed_domains: List[str]) -> Callable:
    """Return a check that passes if the user's email ends with an allowed domain.

    ``allowed_domains`` are email domains such as ``'@example.com'``; a missing
    leading ``@`` is added and matching is case-insensitive.

    >>> create_domain_check(['@example.com'])({'email': 'user@example.com'})
    True
    """
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
    """Return a check that passes if the user's email is in ``allowed_emails``.

    Matching is case-insensitive.

    >>> create_email_list_check(['admin@example.com'])({'email': 'admin@example.com'})
    True
    """
    normalized_emails = {email.lower() for email in allowed_emails}

    def check_email(user_data):
        if not user_data or not user_data.get("email"):
            return False

        return user_data["email"].lower() in normalized_emails

    return check_email


def create_combined_check(*check_functions: Callable) -> Callable:
    """Return a check that passes if ANY of ``check_functions`` passes (OR logic).

    >>> combined = create_combined_check(
    ...     create_domain_check(['@example.com']),
    ...     create_email_list_check(['admin@external.com']),
    ... )
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
