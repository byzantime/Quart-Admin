"""Test QuartAdmin initialisation on a Quart app."""

from quart_admin import QuartAdmin


async def test_quart_admin_initialises_on_app(test_app):
    """QuartAdmin registers itself on the app and serves its index page."""
    admin = QuartAdmin(test_app)

    assert test_app.extensions["quart_admin"] is admin
    assert admin.blueprint.name == admin.config.name

    admin.register_blueprint()
    response = await test_app.test_client().get(f"{admin.config.url_prefix}/")

    assert response.status_code == 200
