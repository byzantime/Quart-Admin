"""Test the QuartAdminConfig class."""

from quart_admin.config import QuartAdminConfig


class TestQuartAdminConfig:
    """Test the QuartAdminConfig configuration class."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = QuartAdminConfig()

        assert config.name == "admin"
        assert config.url_prefix == "/admin"
        assert config.template_folder is None
        assert config.static_folder is None
        assert config.require_auth is True
        assert config.default_page_size == 20
        assert config.enable_search is True
        assert config.enable_batch_actions is True
        assert config.csrf_protection is True

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = QuartAdminConfig(
            name="custom-admin",
            url_prefix="/custom",
            require_auth=False,
            default_page_size=50,
            enable_search=False,
        )

        assert config.name == "custom-admin"
        assert config.url_prefix == "/custom"
        assert config.require_auth is False
        assert config.default_page_size == 50
        assert config.enable_search is False

        # Defaults should still apply for unspecified values
        assert config.enable_batch_actions is True
        assert config.csrf_protection is True

    def test_configuration_is_dataclass(self):
        """Test that QuartAdminConfig is a proper dataclass."""
        config1 = QuartAdminConfig(name="test1")
        config2 = QuartAdminConfig(name="test1")
        config3 = QuartAdminConfig(name="test2")

        # Should be equal when values are the same
        assert config1 == config2

        # Should not be equal when values differ
        assert config1 != config3
