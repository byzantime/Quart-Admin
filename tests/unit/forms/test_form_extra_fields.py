"""Tests for form_extra_fields support in WTFormsGenerator and ModelView."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from quart_admin.forms.wtforms import WTFormsGenerator
from quart_admin.views.model import ModelView

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_provider(fields=None):
    provider = MagicMock()
    provider.get_model_fields.return_value = fields or []
    return provider


def _make_model():
    model = MagicMock()
    model.__name__ = "TestModel"
    return model


# ---------------------------------------------------------------------------
# TestWTFormsExtraFields
# ---------------------------------------------------------------------------


class TestWTFormsExtraFields:
    """Unit tests for WTFormsGenerator.create_form extra_fields parameter."""

    def setup_method(self):
        self.generator = WTFormsGenerator()
        self.db_provider = _make_db_provider()
        self.model = _make_model()

    def test_extra_field_appears_on_form(self, flask_app):
        """Extra field shows up on the generated form with the correct WTForms type."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        extra = {"password": PasswordField("Password", validators=[Optional()])}
        with flask_app.app_context():
            form = self.generator.create_form(
                self.model, self.db_provider, extra_fields=extra
            )

        assert hasattr(form, "password")
        assert isinstance(form.password, PasswordField)

    def test_extra_field_alongside_excluded_columns(self, flask_app):
        """Extra field works correctly when excluded_columns is also set."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        fields = [
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "password_hash",
                "type": "VARCHAR(255)",
                "nullable": True,
                "primary_key": False,
            },
        ]
        db_provider = _make_db_provider(fields)
        extra = {"password": PasswordField("Password", validators=[Optional()])}

        with flask_app.app_context():
            form = self.generator.create_form(
                self.model,
                db_provider,
                excluded_columns=["password_hash"],
                extra_fields=extra,
            )

        assert hasattr(form, "password")
        assert isinstance(form.password, PasswordField)
        assert hasattr(form, "name")
        assert not hasattr(form, "password_hash")

    def test_extra_field_overrides_auto_generated_column(self, flask_app):
        """An extra field with the same name as a model column shadows the auto-generated one."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        fields = [
            {
                "name": "token",
                "type": "VARCHAR(255)",
                "nullable": True,
                "primary_key": False,
            },
        ]
        db_provider = _make_db_provider(fields)
        extra = {"token": PasswordField("Token", validators=[Optional()])}

        with flask_app.app_context():
            form = self.generator.create_form(
                self.model, db_provider, extra_fields=extra
            )

        # The last setattr wins — PasswordField should override the auto StringField
        assert isinstance(form.token, PasswordField)

    def test_none_extra_fields_no_crash(self, flask_app):
        """Passing extra_fields=None (or omitting it) produces a valid form with no extra field."""
        with flask_app.app_context():
            form_none = self.generator.create_form(
                self.model, self.db_provider, extra_fields=None
            )
            form_omitted = self.generator.create_form(self.model, self.db_provider)

        assert not hasattr(form_none, "password")
        assert not hasattr(form_omitted, "password")


# ---------------------------------------------------------------------------
# TestModelViewFormExtraFields
# ---------------------------------------------------------------------------


class TestModelViewFormExtraFields:
    """Tests that ModelView wires form_extra_fields through to form_generator."""

    def _make_view(self, extra_fields=None):
        db_provider = _make_db_provider()
        db_provider.get_primary_key_fields.return_value = ["id"]
        form_gen = MagicMock()
        form_gen.create_form.return_value = MagicMock()

        class ConcreteView(ModelView):
            pass

        if extra_fields is not None:
            ConcreteView.form_extra_fields = extra_fields

        view = ConcreteView(
            model=_make_model(),
            database_provider=db_provider,
            form_generator=form_gen,
        )
        return view

    def test_default_form_extra_fields_is_none(self):
        """Default ModelView.form_extra_fields is None (falsy, Flask-Admin parity)."""
        assert ModelView.form_extra_fields is None

    def test_subclass_class_level_assignment_respected(self):
        """A subclass that sets form_extra_fields at class level sees it after instantiation."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        extra = {"password": PasswordField("Password", validators=[Optional()])}
        view = self._make_view(extra_fields=extra)
        assert view.form_extra_fields is extra

    @pytest.mark.asyncio
    async def test_extra_fields_passed_to_create_form_in_create_view(self, test_app):
        """create_view() passes extra_fields= to form_generator.create_form()."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        extra = {"password": PasswordField("Password", validators=[Optional()])}
        view = self._make_view(extra_fields=extra)

        mock_form = MagicMock()
        mock_form.validate_on_submit.return_value = False
        mock_form.errors = {}
        view.form_generator.create_form.return_value = mock_form

        async with test_app.test_request_context("/create"):
            with patch(
                "quart_admin.views.model.render_template", new_callable=AsyncMock
            ) as mock_render:
                mock_render.return_value = ""
                await view.create_view()

        call_kwargs = view.form_generator.create_form.call_args[1]
        assert "extra_fields" in call_kwargs
        assert call_kwargs["extra_fields"] is extra

    @pytest.mark.asyncio
    async def test_extra_fields_passed_to_create_form_in_edit_view(self, test_app):
        """edit_view() passes extra_fields= to form_generator.create_form()."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        extra = {"password": PasswordField("Password", validators=[Optional()])}
        view = self._make_view(extra_fields=extra)

        # db provider needs to return an item so the view doesn't redirect
        view.database_provider.get_by_pk = AsyncMock(
            return_value={"id": 1, "name": "x"}
        )
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        view.database_provider.get_session.return_value = session_mock

        mock_form = MagicMock()
        mock_form.validate_on_submit.return_value = False
        mock_form.errors = {}
        view.form_generator.create_form.return_value = mock_form

        async with test_app.test_request_context("/edit/1"):
            with patch(
                "quart_admin.views.model.render_template", new_callable=AsyncMock
            ) as mock_render:
                mock_render.return_value = ""
                await view.edit_view(1)

        call_kwargs = view.form_generator.create_form.call_args[1]
        assert "extra_fields" in call_kwargs
        assert call_kwargs["extra_fields"] is extra

    @pytest.mark.asyncio
    async def test_extra_field_value_excluded_from_create_kwargs(self, test_app):
        """A submitted extra field (e.g. plaintext password) must never reach
        database_provider.create() — it isn't a model column, and on_model_change
        (the intended place to hash/transform it) only runs *after* create()."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        extra = {"password": PasswordField("Password", validators=[Optional()])}
        view = self._make_view(extra_fields=extra)

        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock(return_value=False)
        session_mock.commit = AsyncMock(return_value=None)
        view.database_provider.get_session.return_value = session_mock
        view.database_provider.create = AsyncMock(return_value=MagicMock())
        view.get_list_url = MagicMock(return_value="/admin/testmodel/")

        # MagicMock(name=...) sets the mock's repr, not the `.name` attribute,
        # so it must be assigned explicitly after construction.
        name_field = MagicMock()
        name_field.name = "name"
        name_field.data = "Alice"
        password_field = MagicMock()
        password_field.name = "password"
        password_field.data = "plaintext-secret"

        mock_form = MagicMock()
        mock_form.validate_on_submit.return_value = True
        mock_form.errors = {}
        mock_form.__iter__.return_value = iter([name_field, password_field])
        view.form_generator.create_form.return_value = mock_form

        async with test_app.test_request_context("/create"):
            with patch(
                "quart_admin.views.model.render_template", new_callable=AsyncMock
            ) as mock_render:
                mock_render.return_value = ""
                await view.create_view()

        create_kwargs = view.database_provider.create.call_args[1]
        assert "password" not in create_kwargs
        assert create_kwargs.get("name") == "Alice"


# ---------------------------------------------------------------------------
# TestFlaskAdminParity
# ---------------------------------------------------------------------------


class TestFlaskAdminParity:
    """Verify parity with flask_admin.model.base.BaseModelView.form_extra_fields."""

    def test_flask_admin_base_has_falsy_form_extra_fields(self):
        """flask_admin BaseModelView.form_extra_fields is falsy (None or {})."""
        try:
            from flask_admin.model.base import BaseModelView
        except ImportError:
            pytest.skip("flask-admin not installed")

        assert not BaseModelView.form_extra_fields

    def test_quart_admin_model_view_form_extra_fields_is_falsy(self):
        """ModelView.form_extra_fields is falsy, matching Flask-Admin."""
        assert not ModelView.form_extra_fields

    def test_password_field_injected_via_extra_fields(self, flask_app):
        """A PasswordField injected via extra_fields appears as PasswordField on the form."""
        try:
            from wtforms import PasswordField
            from wtforms.validators import Optional
        except ImportError:
            pytest.skip("WTForms not available")

        generator = WTFormsGenerator()
        db_provider = _make_db_provider()
        model = _make_model()
        extra = {"password": PasswordField("Password", validators=[Optional()])}

        with flask_app.app_context():
            form = generator.create_form(model, db_provider, extra_fields=extra)

        assert isinstance(form.password, PasswordField)
