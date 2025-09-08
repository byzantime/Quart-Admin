"""ModelView for database-backed admin views."""

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from quart import flash
from quart import redirect
from quart import render_template
from quart import request

from ..auth.base import AuthProvider
from ..database.base import DatabaseProvider
from ..forms.base import FormGenerator
from .base import AdminView


class ModelView(AdminView):
    """Database model admin view with CRUD operations."""

    def __init__(
        self,
        model: Type,
        name: Optional[str] = None,
        category: Optional[str] = None,
        endpoint: Optional[str] = None,
        url: Optional[str] = None,
        auth_provider: Optional[AuthProvider] = None,
        database_provider: Optional[DatabaseProvider] = None,
        form_generator: Optional[FormGenerator] = None,
        **kwargs,
    ):
        """Initialize ModelView.

        Args:
            model: Database model class
            name: Human-readable name (defaults to model.__name__)
            category: Category for grouping views
            endpoint: Blueprint endpoint name
            url: URL pattern
            auth_provider: Authentication provider
            database_provider: Database provider
            form_generator: Form generator for creating/editing forms
            **kwargs: Additional arguments for parent class
        """
        if name is None:
            name = model.__name__

        super().__init__(
            name=name,
            category=category,
            endpoint=endpoint,
            url=url,
            auth_provider=auth_provider,
            database_provider=database_provider,
            **kwargs,
        )

        self.model = model
        self.form_generator = form_generator

        # Model-specific settings
        self.column_list: Optional[List[str]] = None
        self.column_searchable_list: Optional[List[str]] = None
        self.column_filters: Optional[List[str]] = None
        self.column_sortable_list: Optional[List[str]] = None
        self.column_labels: Dict[str, str] = {}
        self.column_formatters: Dict[str, Callable] = {}

        # Form settings
        self.form_columns: Optional[List[str]] = []
        self.form_excluded_columns: Optional[List[str]] = []

        # Validation
        self.form_validators: Dict[str, List[Callable]] = {}

    def get_database_session(self):
        """Get database session from provider."""
        if not self.database_provider:
            raise ValueError("Database provider not configured")
        return self.database_provider.get_session()

    def get_model_fields(self) -> List[Dict[str, Any]]:
        """Get field information from database provider."""
        if not self.database_provider:
            return []
        return self.database_provider.get_model_fields(self.model)

    def get_columns_list(self) -> List[str]:
        """Get list of columns to display."""
        if self.column_list:
            return self.column_list

        # Default to all model fields
        fields = self.get_model_fields()
        return [field["name"] for field in fields if not field.get("is_relationship")]

    def get_searchable_columns(self) -> List[str]:
        """Get list of searchable columns."""
        return self.column_searchable_list or []

    async def list_view(self):
        """Enhanced list view with database integration."""
        if not self.database_provider:
            return await super().list_view()

        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", self.page_size)), 100)
        search = request.args.get("search", "")
        # TODO: Implement sorting
        # sort_by = request.args.get("sort", "")
        # sort_desc = request.args.get("desc", "") == "1"

        async with self.get_database_session() as session:
            # Build filters
            filters = {}
            if search and self.get_searchable_columns():
                # Basic search implementation - database provider could enhance this
                filters["search"] = search

            # Get total count
            total_count = await self.database_provider.count(
                self.model, session, **filters
            )
            # Get records for current page
            # Note: Pagination logic would be enhanced in a full implementation
            items = await self.database_provider.get_all(self.model, session, **filters)

            # Simple pagination by slicing
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_items = items[start_idx:end_idx]

            columns = self.get_columns_list()
            admin = getattr(self, "admin", None)
            return await render_template(
                self.list_template,
                admin=admin,
                view=self,
                items=page_items,
                total_count=total_count,
                page=page,
                per_page=per_page,
                search=search,
                columns=columns,
                column_labels=self.column_labels,
                config=admin.config if admin else None,
            )

    async def create_view(self):
        """Enhanced create view with form generation."""
        if not self.database_provider:
            return await super().create_view()

        form = self.form_generator.create_form(
            self.model,
            self.database_provider,
            excluded_columns=self.form_excluded_columns,
        )

        if form.validate_on_submit():
            async with self.get_database_session() as session:
                form_data = {}
                for field in form:
                    if field.name != "csrf_token" and field.data is not None:
                        form_data[field.name] = field.data

                # Create record
                await self.database_provider.create(self.model, session, **form_data)

                await flash(f"{self.name} created successfully!", "success")
                return redirect(self.get_list_url())
        elif request.method == "POST":
            for field_name, errors in form.errors.items():
                for error in errors:
                    await flash(f"{field_name}: {error}", "error")

        return await render_template(
            self.form_template,
            view=self,
            admin=getattr(self, "admin", None),
            form=form,
            item_id=None,
            item=None,
            fields=self.get_model_fields(),
        )

    async def edit_view(self, id: int):
        """Enhanced edit view with form generation."""
        if not self.database_provider:
            return await super().edit_view(id)

        # Get primary key fields and build pk_values dict
        pk_fields = self.database_provider.get_primary_key_fields(self.model)
        if len(pk_fields) == 1:
            pk_values = {pk_fields[0]: id}
        else:
            # For composite keys, this would need to be handled differently
            # For now, assume single primary key
            raise ValueError("Composite primary keys not yet supported in edit_view")

        # First, get the item to edit (separate session context)
        async with self.get_database_session() as session:
            item = await self.database_provider.get_by_pk(
                self.model, session, pk_values
            )

            if not item:
                await flash(f"{self.name} not found", "error")
                return redirect(self.get_list_url())

        # Create form with the retrieved item
        form = self.form_generator.create_form(
            self.model,
            self.database_provider,
            obj=item,
            excluded_columns=self.form_excluded_columns,
        )

        if form.validate_on_submit():
            async with self.get_database_session() as session:
                excluded_fields = {"csrf_token"} | set(pk_fields)

                form_data = {}
                for field in form:
                    if field.name not in excluded_fields:
                        form_data[field.name] = field.data

                await self.database_provider.update(
                    self.model, session, pk_values, **form_data
                )

                await flash(f"{self.name} updated successfully!", "success")
                return redirect(self.get_list_url())
        elif request.method == "POST":
            for field_name, errors in form.errors.items():
                for error in errors:
                    await flash(f"{field_name}: {error}", "error")

        return await render_template(
            self.form_template,
            view=self,
            admin=getattr(self, "admin", None),
            form=form,
            item=item,
            item_id=id,
            fields=self.get_model_fields(),
        )

    async def details_view(self, id: int):
        """Enhanced details view with database integration."""
        if not self.database_provider:
            return await super().details_view(id)

        async with self.get_database_session() as session:
            # Get primary key fields and build pk_values dict
            pk_fields = self.database_provider.get_primary_key_fields(self.model)
            if len(pk_fields) == 1:
                pk_values = {pk_fields[0]: id}
            else:
                # For composite keys, this would need to be handled differently
                # For now, assume single primary key
                raise ValueError(
                    "Composite primary keys not yet supported in details_view"
                )

            item = await self.database_provider.get_by_pk(
                self.model, session, pk_values
            )

            if not item:
                await flash(f"{self.name} not found", "error")
                return redirect(self.get_list_url())

            return await render_template(
                self.details_template,
                view=self,
                admin=getattr(self, "admin", None),
                item=item,
                item_id=id,
                fields=self.get_model_fields(),
            )

    async def delete_view(self, id: int):
        """Enhanced delete view with database integration."""
        if not self.database_provider:
            return await super().delete_view(id)

        async with self.get_database_session() as session:
            # Get primary key fields and build pk_values dict
            pk_fields = self.database_provider.get_primary_key_fields(self.model)
            if len(pk_fields) == 1:
                pk_values = {pk_fields[0]: id}
            else:
                # For composite keys, this would need to be handled differently
                # For now, assume single primary key
                raise ValueError(
                    "Composite primary keys not yet supported in delete_view"
                )

            success = await self.database_provider.delete(
                self.model, session, pk_values
            )

            if success:
                await flash(f"{self.name} deleted successfully!", "success")
            else:
                await flash(f"{self.name} not found", "error")

        return redirect(self.get_list_url())

    def format_column_value(self, item: Dict[str, Any], column: str) -> str:
        """Format column value using custom formatters or defaults."""
        if column in self.column_formatters:
            return self.column_formatters[column](item, column)

        value = item.get(column)
        if value is None:
            return ""

        # Basic formatting for common types
        if isinstance(value, bool):
            return "✓" if value else "✗"
        elif hasattr(value, "strftime"):  # datetime
            return value.strftime("%Y-%m-%d %H:%M")

        return str(value)
