"""Batch action decorator and mixin for ModelView."""

from quart import abort
from quart import redirect
from quart import request
from quart import url_for


def action(name, text, confirmation=None):
    """Decorator to mark a ModelView method as a batch action.

    Args:
        name: Action identifier used in form submissions
        text: Human-readable display text for the action button
        confirmation: Optional confirmation prompt shown before executing
    """

    def decorator(f):
        f._action = (name, text, confirmation)
        return f

    return decorator


class ActionsMixin:
    """Mixin that adds batch action support to a view class."""

    action_disallowed_list: list = []

    def init_actions(self):
        """Scan for @action-decorated methods and populate the actions registry."""
        self._actions = []
        self._actions_data = {}

        for attr_name in dir(self):
            attr = getattr(type(self), attr_name, None)
            if attr is None or not hasattr(attr, "_action"):
                continue
            action_name, action_text, action_confirmation = attr._action
            self._actions.append((action_name, action_text))
            self._actions_data[action_name] = (
                getattr(self, attr_name),
                action_text,
                action_confirmation,
            )

    def is_action_allowed(self, name: str) -> bool:
        """Return True if the action name is not in the disallowed list."""
        return name not in self.action_disallowed_list

    def get_actions_list(self):
        """Return allowed actions and their confirmation messages.

        Returns:
            tuple: ([(name, text), ...], {name: confirmation_msg, ...})
        """
        actions = []
        actions_confirmation = {}
        for name, text in self._actions:
            if not self.is_action_allowed(name):
                continue
            actions.append((name, text))
            _, _, confirmation = self._actions_data[name]
            if confirmation:
                actions_confirmation[name] = confirmation
        return actions, actions_confirmation

    def get_action_url(self):
        """Return the URL for the action POST endpoint."""
        return url_for(f"admin.{self.endpoint}_action")

    async def handle_action(self, return_view=None):
        """Process a batch action POST request.

        Reads ``action`` and ``rowid`` from the submitted form, validates the
        action name, calls the registered handler, and redirects.
        """
        form = await request.form
        action_name = form.get("action", "")
        ids = form.getlist("rowid")

        if action_name not in self._actions_data:
            abort(400)

        if not self.is_action_allowed(action_name):
            abort(403)

        handler, _, _ = self._actions_data[action_name]
        await handler(ids)

        return redirect(return_view or self.get_list_url())
