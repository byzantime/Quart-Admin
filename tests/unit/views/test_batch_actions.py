"""Tests for batch action registration and execution."""

from unittest.mock import DEFAULT
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from quart import Blueprint
from quart import Quart

from quart_admin.actions import action
from quart_admin.config import QuartAdminConfig
from quart_admin.views.model import ModelView


def _make_view(view_class=None):
    """Instantiate a ModelView (or subclass) with a mock model and database."""
    mock_model = MagicMock()
    mock_model.__name__ = "TestModel"
    mock_db = MagicMock()
    cls = view_class or ModelView
    view = cls(model=mock_model, database_provider=mock_db)
    return view, mock_model, mock_db


def _make_app_with_view(view_class):
    """Build a minimal Quart app with the given ModelView subclass registered."""
    app = Quart(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    view, mock_model, mock_db = _make_view(view_class)
    view.admin = MagicMock()
    view.admin.config = QuartAdminConfig(name="admin", url_prefix="/admin")

    bp = Blueprint("admin", __name__, url_prefix="/admin")
    view.create_blueprint(bp)
    app.register_blueprint(bp)

    return app, view


class TestActionDecorator:
    def setup_method(self):
        class MyView(ModelView):
            @action("foo", "Foo", "Sure?")
            async def do_foo(self, ids):
                pass

        self.view, _, _ = _make_view(MyView)

    def test_action_appears_in_actions_list(self):
        names = [name for name, _ in self.view._actions]
        assert "foo" in names

    def test_action_text_is_correct(self):
        names_texts = dict(self.view._actions)
        assert names_texts["foo"] == "Foo"

    def test_action_registered_in_actions_data(self):
        assert "foo" in self.view._actions_data

    def test_actions_data_has_correct_text_and_confirmation(self):
        _, text, confirmation = self.view._actions_data["foo"]
        assert text == "Foo"
        assert confirmation == "Sure?"

    def test_get_actions_list_returns_allowed_action(self):
        actions, confirmation = self.view.get_actions_list()
        names = [n for n, _ in actions]
        assert "foo" in names
        assert confirmation.get("foo") == "Sure?"

    def test_default_delete_action_registered(self):
        names = [name for name, _ in self.view._actions]
        assert "delete" in names


class TestActionEndpoint:
    @pytest.fixture
    def app_and_calls(self):
        handler_calls = []

        class MyView(ModelView):
            @action("foo", "Foo")
            async def do_foo(self, ids):
                handler_calls.append(list(ids))

        app, view = _make_app_with_view(MyView)
        return app, view, handler_calls

    @pytest.mark.asyncio
    async def test_post_dispatches_to_handler(self, app_and_calls):
        app, view, handler_calls = app_and_calls
        async with app.test_client() as client:
            response = await client.post(
                f"/admin{view.url}/action/",
                form=[("action", "foo"), ("rowid", "1"), ("rowid", "2")],
            )
        assert response.status_code == 302
        assert handler_calls == [["1", "2"]]

    @pytest.mark.asyncio
    async def test_post_redirects_to_list(self, app_and_calls):
        app, view, _ = app_and_calls
        async with app.test_client() as client:
            response = await client.post(
                f"/admin{view.url}/action/",
                form=[("action", "foo"), ("rowid", "1")],
            )
        location = response.headers.get("Location", "")
        assert view.endpoint in location or view.url in location


class TestDeleteSelectedAction:
    @pytest.fixture
    def view_with_mock_db(self):
        view, mock_model, mock_db = _make_view()

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        class FakeSessionCtx:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_db.get_session.return_value = FakeSessionCtx()
        mock_db.get_primary_key_fields.return_value = ["id"]

        fake_instance = MagicMock()
        mock_db.get_model_by_pk = AsyncMock(return_value=fake_instance)
        mock_db.delete = AsyncMock(return_value=True)

        return view, mock_db, mock_session

    @pytest.mark.asyncio
    async def test_delete_selected_calls_delete_for_each_id(self, view_with_mock_db):
        view, mock_db, _ = view_with_mock_db
        app = Quart(__name__)
        app.config["SECRET_KEY"] = "test"
        async with app.app_context():
            with patch("quart_admin.views.model.flash", new_callable=AsyncMock):
                await view.delete_selected(["1", "2"])
        assert mock_db.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_selected_calls_lifecycle_hooks(self, view_with_mock_db):
        view, mock_db, _ = view_with_mock_db
        app = Quart(__name__)
        app.config["SECRET_KEY"] = "test"
        with patch.multiple(
            view,
            on_model_delete=DEFAULT,
            after_model_delete=DEFAULT,
            new_callable=AsyncMock,
        ) as hooks:
            async with app.app_context():
                with patch("quart_admin.views.model.flash", new_callable=AsyncMock):
                    await view.delete_selected(["1", "2"])
        assert hooks["on_model_delete"].call_count == 2
        assert hooks["after_model_delete"].call_count == 2

    @pytest.mark.asyncio
    async def test_delete_selected_flashes_count(self, view_with_mock_db):
        view, mock_db, _ = view_with_mock_db
        app = Quart(__name__)
        app.config["SECRET_KEY"] = "test"
        flash_calls = []

        async def fake_flash(msg, cat):
            flash_calls.append(msg)

        async with app.app_context():
            with patch("quart_admin.views.model.flash", side_effect=fake_flash):
                await view.delete_selected(["1", "2", "3"])

        assert len(flash_calls) == 1
        assert "3" in flash_calls[0]

    @pytest.mark.asyncio
    async def test_delete_selected_skips_missing_records(self, view_with_mock_db):
        view, mock_db, _ = view_with_mock_db
        mock_db.get_model_by_pk = AsyncMock(side_effect=[None, MagicMock()])
        app = Quart(__name__)
        app.config["SECRET_KEY"] = "test"
        flash_calls = []

        async def fake_flash(msg, cat):
            flash_calls.append(msg)

        async with app.app_context():
            with patch("quart_admin.views.model.flash", side_effect=fake_flash):
                await view.delete_selected(["1", "2"])

        assert mock_db.delete.call_count == 1
        assert "1" in flash_calls[0]


class TestUnknownActionName:
    @pytest.fixture
    def app_plain(self):
        app, view = _make_app_with_view(ModelView)
        return app, view

    @pytest.mark.asyncio
    async def test_unknown_action_returns_400(self, app_plain):
        app, view = app_plain
        async with app.test_client() as client:
            response = await client.post(
                f"/admin{view.url}/action/",
                form={"action": "nonexistent", "rowid": ["1"]},
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_disallowed_action_returns_403(self, app_plain):
        app, view = app_plain
        view.action_disallowed_list = ["delete"]
        async with app.test_client() as client:
            response = await client.post(
                f"/admin{view.url}/action/",
                form={"action": "delete", "rowid": ["1"]},
            )
        assert response.status_code == 403
