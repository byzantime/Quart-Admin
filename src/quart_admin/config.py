"""Configuration system for Quart-Admin."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import Optional


@dataclass
class QuartAdminConfig:
    """Configuration for Quart-Admin."""

    # Basic settings
    name: str = "admin"
    url_prefix: str = "/admin"

    # Template settings
    template_folder: Optional[str] = None
    static_folder: Optional[str] = None
    base_template: str = "admin/base.html"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Features
    enable_search: bool = True
    enable_batch_actions: bool = True

    # UI settings
    site_name: str = "Admin"
    site_logo: Optional[str] = None
    brand_color: str = "#007bff"

    # Security
    require_auth: bool = True
    csrf_protection: bool = True

    # Custom settings
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None

    # Plugin configurations
    auth_config: Dict[str, Any] = field(default_factory=dict)
    database_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "QuartAdminConfig":
        """Create config from dictionary."""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "url_prefix": self.url_prefix,
            "template_folder": self.template_folder,
            "static_folder": self.static_folder,
            "base_template": self.base_template,
            "default_page_size": self.default_page_size,
            "max_page_size": self.max_page_size,
            "enable_search": self.enable_search,
            "enable_batch_actions": self.enable_batch_actions,
            "site_name": self.site_name,
            "site_logo": self.site_logo,
            "brand_color": self.brand_color,
            "require_auth": self.require_auth,
            "csrf_protection": self.csrf_protection,
            "custom_css": self.custom_css,
            "custom_js": self.custom_js,
            "auth_config": self.auth_config,
            "database_config": self.database_config,
        }
