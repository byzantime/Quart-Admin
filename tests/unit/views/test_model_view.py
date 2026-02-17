"""Tests for ModelView lifecycle hooks."""

from unittest.mock import MagicMock

import pytest

from quart_admin.views.model import ModelView


class TestLifecycleHooks:
    """Test model lifecycle hooks."""

    def setup_method(self):
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"
        self.mock_db_provider = MagicMock()
        self.view = ModelView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )

    # 1. Test default hooks do nothing
    @pytest.mark.asyncio
    async def test_on_model_change_default_does_nothing(self):
        """Default on_model_change should do nothing."""
        result = await self.view.on_model_change(MagicMock(), MagicMock(), True)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_model_delete_default_does_nothing(self):
        """Default on_model_delete should do nothing."""
        result = await self.view.on_model_delete(MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_after_model_change_default_does_nothing(self):
        """Default after_model_change should do nothing."""
        result = await self.view.after_model_change(MagicMock(), MagicMock(), False)
        assert result is None

    @pytest.mark.asyncio
    async def test_after_model_delete_default_does_nothing(self):
        """Default after_model_delete should do nothing."""
        result = await self.view.after_model_delete(MagicMock())
        assert result is None

    # 2. Test hooks can modify model
    @pytest.mark.asyncio
    async def test_on_model_change_can_modify_model(self):
        """on_model_change should be able to modify model before save."""

        class CustomView(ModelView):
            async def on_model_change(self, form, model, is_created):
                model.email = model.email.lower()

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )
        mock_model = MagicMock()
        mock_model.email = "TEST@EXAMPLE.COM"

        await view.on_model_change(MagicMock(), mock_model, True)
        assert mock_model.email == "test@example.com"

    # 3. Test is_created flag
    @pytest.mark.asyncio
    async def test_on_model_change_receives_is_created_flag(self):
        """on_model_change should receive correct is_created flag."""
        received_flags = []

        class CustomView(ModelView):
            async def on_model_change(self, form, model, is_created):
                received_flags.append(is_created)

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )
        await view.on_model_change(MagicMock(), MagicMock(), True)
        await view.on_model_change(MagicMock(), MagicMock(), False)

        assert received_flags == [True, False]

    # 4. Test hook exception handling
    @pytest.mark.asyncio
    async def test_on_model_change_exception_propagates(self):
        """Exceptions in on_model_change should propagate."""

        class CustomView(ModelView):
            async def on_model_change(self, form, model, is_created):
                raise ValueError("Validation failed")

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )

        with pytest.raises(ValueError, match="Validation failed"):
            await view.on_model_change(MagicMock(), MagicMock(), True)

    @pytest.mark.asyncio
    async def test_on_model_delete_exception_propagates(self):
        """Exceptions in on_model_delete should propagate."""

        class CustomView(ModelView):
            async def on_model_delete(self, model):
                raise ValueError("Cannot delete this record")

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )

        with pytest.raises(ValueError, match="Cannot delete this record"):
            await view.on_model_delete(MagicMock())

    @pytest.mark.asyncio
    async def test_after_model_change_can_perform_side_effects(self):
        """after_model_change should be able to perform side effects."""
        side_effect_called = []

        class CustomView(ModelView):
            async def after_model_change(self, form, model, is_created):
                side_effect_called.append((model.id, is_created))

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )
        mock_model = MagicMock()
        mock_model.id = 123

        await view.after_model_change(MagicMock(), mock_model, True)
        assert side_effect_called == [(123, True)]

    @pytest.mark.asyncio
    async def test_after_model_delete_can_perform_cleanup(self):
        """after_model_delete should be able to perform cleanup tasks."""
        deleted_ids = []

        class CustomView(ModelView):
            async def after_model_delete(self, model):
                deleted_ids.append(model.id)

        view = CustomView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )
        mock_model = MagicMock()
        mock_model.id = 456

        await view.after_model_delete(mock_model)
        assert deleted_ids == [456]
