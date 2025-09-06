"""Main QuartAdmin extension class."""

import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from quart import Blueprint
from quart import render_template

from .auth.base import AuthProvider
from .config import QuartAdminConfig
from .database.base import DatabaseProvider
from .forms.base import FormGenerator
from .forms.wtforms import WTFormsGenerator
from .views.base import AdminView
from .views.model import ModelView


class QuartAdmin:
    """Main admin extension for Quart applications."""

    def __init__(
        self,
        app=None,
        config: Optional[QuartAdminConfig] = None,
        auth_provider: Optional[AuthProvider] = None,
        database_provider: Optional[DatabaseProvider] = None,
        form_generator: Optional[FormGenerator] = None,
        **kwargs,
    ):
        """Initialize QuartAdmin extension.

        Args:
            app: Quart application instance
            config: Configuration object
            auth_provider: Authentication provider instance
            database_provider: Database provider instance
            form_generator: Form generator instance
            **kwargs: Additional configuration options
        """
        self.config = config or QuartAdminConfig(**kwargs)
        self.auth_provider = auth_provider
        self.database_provider = database_provider
        self.form_generator = form_generator

        self._views: Dict[str, AdminView] = {}
        self._models: Dict[str, Type] = {}
        self._categories: Dict[str, List[AdminView]] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize admin extension with Quart app."""
        app.extensions = getattr(app, "extensions", {})
        app.extensions["quart_admin"] = self

        # Store app for later blueprint registration
        self.app = app

        # Set up template folder
        if not self.config.template_folder:
            # Use built-in templates
            template_folder = os.path.join(os.path.dirname(__file__), "templates")
        else:
            template_folder = self.config.template_folder

        # Create blueprint
        self.blueprint = Blueprint(
            self.config.name,
            __name__,
            url_prefix=self.config.url_prefix,
            template_folder=template_folder,
            static_folder=self.config.static_folder,
        )

        # Register admin index route
        @self.blueprint.route("/")
        async def index():
            # Apply auth if configured
            if self.config.require_auth and self.auth_provider:
                if not await self.auth_provider.is_authenticated():
                    from quart import abort

                    abort(401, "Authentication required")
                if not await self.auth_provider.has_admin_access():
                    from quart import abort

                    abort(403, "Admin access required")

            return await render_template(
                "admin/index.html",
                admin=self,
                views=self._views,
                categories=self._categories,
                config=self.config,
            )

    def register_blueprint(self):
        """Register the blueprint after all views are added."""
        if hasattr(self, "app") and self.app:
            self.app.register_blueprint(self.blueprint)

    def add_view(self, view: AdminView):
        """Add an admin view.

        Args:
            view: AdminView instance to add
        """
        # Set admin instance reference
        view.admin = self

        # Set providers on the view if not already set
        if not view.auth_provider and self.auth_provider:
            view.auth_provider = self.auth_provider
        if not view.database_provider and self.database_provider:
            view.database_provider = self.database_provider

        # Add to views registry
        self._views[view.name] = view

        # Add to category
        category = view.category or "Default"
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(view)

        # Create blueprint routes
        view.create_blueprint(self.blueprint)

        # Register model if it's a ModelView
        if isinstance(view, ModelView) and hasattr(view, "model"):
            self._models[view.name] = view.model

    def add_model_view(
        self,
        model: Type,
        name: Optional[str] = None,
        category: Optional[str] = None,
        view_class: Type[ModelView] = ModelView,
        **kwargs,
    ):
        """Add a model view with automatic CRUD generation.

        Args:
            model: Database model class
            name: View name (defaults to model.__name__)
            category: Category for grouping views
            view_class: ModelView subclass to use
            **kwargs: Additional arguments for ModelView
        """
        if name is None:
            name = model.__name__

        view = view_class(
            model=model,
            name=name,
            category=category,
            auth_provider=self.auth_provider,
            database_provider=self.database_provider,
            form_generator=self.form_generator,
            **kwargs,
        )
        self.add_view(view)

    def get_view(self, name: str) -> Optional[AdminView]:
        """Get admin view by name."""
        return self._views.get(name)

    def get_views(self) -> List[AdminView]:
        """Get all admin views."""
        return list(self._views.values())

    def get_models(self) -> Dict[str, Type]:
        """Get all registered models."""
        return self._models.copy()

    def get_categories(self) -> Dict[str, List[AdminView]]:
        """Get views organized by category."""
        return self._categories.copy()

    def create_default_providers(self):
        """Create default providers if none are set."""
        if not self.auth_provider:
            from .auth.quart_auth import QuartAuthProvider

            try:
                self.auth_provider = QuartAuthProvider()
            except ImportError:
                # QuartAuth not available, skip auth
                pass

        if not self.database_provider:
            from .database.sqlalchemy import SQLAlchemyProvider

            try:
                # Would need to get session factory from app
                # This is a placeholder - would be configured properly
                self.database_provider = SQLAlchemyProvider()
            except ImportError:
                # SQLAlchemy not available
                pass

        if not self.form_generator:
            self.form_generator = WTFormsGenerator()

    @property
    def __version__(self):
        """Get version for template context."""
        return "0.1.0"
