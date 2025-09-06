"""Base AdminView class for Quart-Admin."""

import asyncio
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

from quart import Blueprint
from quart import abort
from quart import flash
from quart import redirect
from quart import render_template
from quart import url_for

from ..auth.base import AuthProvider
from ..database.base import DatabaseProvider


class AdminView:
    """Base class for all admin views."""

    def __init__(
        self,
        name: str,
        category: Optional[str] = None,
        endpoint: Optional[str] = None,
        url: Optional[str] = None,
        auth_provider: Optional[AuthProvider] = None,
        database_provider: Optional[DatabaseProvider] = None,
    ):
        """Initialize admin view.

        Args:
            name: Human-readable name for the view
            category: Category for grouping views
            endpoint: Blueprint endpoint name (defaults to name)
            url: URL pattern (defaults to name)
            auth_provider: Authentication provider instance
            database_provider: Database provider instance
        """
        self.name = name
        self.category = category
        self.endpoint = endpoint or name.lower().replace(" ", "_")
        self.url = url or f"/{self.endpoint}"
        self.auth_provider = auth_provider
        self.database_provider = database_provider

        # View capabilities
        self.can_create = True
        self.can_edit = True
        self.can_delete = True
        self.can_view_details = True
        self.can_export = True

        # Pagination
        self.page_size = 20

        # Template names - can be overridden
        self.list_template = "admin/list.html"
        self.edit_template = "admin/edit.html"
        self.create_template = "admin/create.html"
        self.form_template = "admin/form.html"  # Unified form template
        self.details_template = "admin/details.html"

    def create_blueprint(self, parent_blueprint: Blueprint):
        """Create and register routes on the parent blueprint."""
        # List view
        parent_blueprint.add_url_rule(
            self.url,
            endpoint=f"{self.endpoint}_list",
            view_func=self._wrap_with_auth(self.list_view),
            methods=["GET"],
        )

        # Unified form view - handles both create and edit
        if self.can_create or self.can_edit:
            # Create view (no ID parameter)
            if self.can_create:
                parent_blueprint.add_url_rule(
                    f"{self.url}/new",
                    endpoint=f"{self.endpoint}_create",
                    view_func=self._wrap_with_auth(self.form_view),
                    methods=["GET", "POST"],
                )

            # Edit view (with ID parameter)
            if self.can_edit:
                parent_blueprint.add_url_rule(
                    f"{self.url}/<int:id>/edit",
                    endpoint=f"{self.endpoint}_edit",
                    view_func=self._wrap_with_auth(self.form_view),
                    methods=["GET", "POST"],
                )

        # Details view
        if self.can_view_details:
            parent_blueprint.add_url_rule(
                f"{self.url}/<int:id>",
                endpoint=f"{self.endpoint}_details",
                view_func=self._wrap_with_auth(self.details_view),
                methods=["GET"],
            )

        # Delete view
        if self.can_delete:
            parent_blueprint.add_url_rule(
                f"{self.url}/<int:id>/delete",
                endpoint=f"{self.endpoint}_delete",
                view_func=self._wrap_with_auth(self.delete_view),
                methods=["POST"],
            )

        # Export view
        if self.can_export:
            parent_blueprint.add_url_rule(
                f"{self.url}/export",
                endpoint=f"{self.endpoint}_export",
                view_func=self._wrap_with_auth(self.export_view),
                methods=["GET"],
            )

    def _wrap_with_auth(self, view_func: Callable) -> Callable:
        """Wrap view function with authentication if provider is available."""
        if self.auth_provider:
            if asyncio.iscoroutinefunction(view_func):

                async def async_wrapper(*args, **kwargs):
                    # Always check authentication for admin endpoints
                    if not await self.auth_provider.is_authenticated():
                        abort(401, "Authentication required")

                    # Always check admin access for admin endpoints
                    if not await self.auth_provider.has_admin_access():
                        abort(403, "Admin access required")

                    return await view_func(*args, **kwargs)

                return async_wrapper
            else:
                # For sync functions, use the admin_required decorator
                return self.auth_provider.admin_required(view_func)
        return view_func

    async def list_view(self):
        """List view - override in subclasses."""
        return await render_template(
            self.list_template,
            view=self,
            admin=getattr(self, "admin", None),
            items=[],
            total_count=0,
            page=1,
            per_page=self.page_size,
        )

    async def form_view(self, id: int = None):
        """Unified form view for both create and edit operations."""
        if id is None:
            # Create mode
            return await self.create_view()
        else:
            # Edit mode
            return await self.edit_view(id)

    async def create_view(self):
        """Create view - override in subclasses."""
        return await render_template(
            self.form_template,
            view=self,
            admin=getattr(self, "admin", None),
            form=None,
            item_id=None,
            item=None,
        )

    async def edit_view(self, id: int):
        """Edit view - override in subclasses."""
        return await render_template(
            self.form_template,
            view=self,
            admin=getattr(self, "admin", None),
            form=None,
            item_id=id,
            item=None,
        )

    async def details_view(self, id: int):
        """Details view - override in subclasses."""
        return await render_template(
            self.details_template,
            view=self,
            admin=getattr(self, "admin", None),
            item=None,
            item_id=id,
        )

    async def delete_view(self, id: int):
        """Delete view - override in subclasses."""
        await flash(f"{self.name} deletion not implemented", "error")
        return redirect(self.get_list_url())

    async def export_view(self):
        """Export view - override in subclasses."""
        await flash(f"{self.name} export not implemented", "error")
        return redirect(self.get_list_url())

    def get_list_url(self):
        """Get URL for list view."""
        return url_for(f"admin.{self.endpoint}_list")

    def get_create_url(self):
        """Get URL for create view."""
        if self.can_create:
            return url_for(f"admin.{self.endpoint}_create")
        return None

    def get_edit_url(self, id: int):
        """Get URL for edit view."""
        if self.can_edit:
            return url_for(f"admin.{self.endpoint}_edit", id=id)
        return None

    def get_details_url(self, id: int):
        """Get URL for details view."""
        if self.can_view_details:
            return url_for(f"admin.{self.endpoint}_details", id=id)
        return None

    def get_delete_url(self, id: int):
        """Get URL for delete view."""
        if self.can_delete:
            return url_for(f"admin.{self.endpoint}_delete", id=id)
        return None

    def get_export_url(self):
        """Get URL for export view."""
        if self.can_export:
            return url_for(f"admin.{self.endpoint}_export")
        return None

    def format_column_value(self, item: Dict[str, Any], column: str) -> str:
        """Format column value for display - override in subclasses."""
        value = item.get(column)
        if value is None:
            return ""
        return str(value)
