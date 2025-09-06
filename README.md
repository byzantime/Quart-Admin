# Quart-Admin

An async admin interface for Quart applications, inspired by Flask-Admin but built specifically for Quart's async capabilities.

## Features

- **Fully Async**: Built from the ground up for Quart's async/await patterns
- **Pluggable Architecture**: Extensible auth, database, and form providers
- **Database Agnostic**: Support for different database backends via providers
- **Authentication Flexible**: Integrate with any auth system
- **Modern UI**: Bootstrap-based responsive interface
- **CRUD Operations**: Automatic Create, Read, Update, Delete for models
- **Search & Filtering**: Built-in search and filtering capabilities
- **Customizable**: Extensive configuration and customization options

## Installation

### Basic Installation

```bash
pip install quart-admin
```

### With Database Support

```bash
pip install quart-admin[sqlalchemy]
```

### With Authentication Support

```bash
pip install quart-admin[auth]
```

### Full Installation

```bash
pip install quart-admin[sqlalchemy,auth,dev]
```

## Quick Start

### Basic Setup

```python
from quart import Quart
from quart_admin import QuartAdmin

app = Quart(__name__)
admin = QuartAdmin(app)

# Register the admin blueprint
admin.register_blueprint()

if __name__ == '__main__':
    app.run()
```

### With Database Models

```python
from quart import Quart
from quart_admin import QuartAdmin
from quart_admin.database import SQLAlchemyProvider
from quart_admin.forms import WTFormsGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_async_engine("sqlite+aiosqlite:///example.db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

app = Quart(__name__)

# Configure admin with providers
admin = QuartAdmin(
    app,
    database_provider=SQLAlchemyProvider(session_factory=AsyncSessionLocal),
    form_generator=WTFormsGenerator()
)

# Add model views
admin.add_model_view(User, name="Users", category="Management")
admin.add_model_view(Post, name="Posts", category="Content")

admin.register_blueprint()
```

### With Authentication

```python
from quart import Quart
from quart_admin import QuartAdmin
from quart_admin.auth import QuartAuthProvider

app = Quart(__name__)

# Configure with auth
auth_provider = QuartAuthProvider(
    user_loader=my_user_loader,
    admin_check=lambda user: user.is_admin if user else False
)

admin = QuartAdmin(
    app,
    auth_provider=auth_provider,
    require_auth=True
)

admin.register_blueprint()
```

## Configuration

### Using QuartAdminConfig

```python
from quart_admin import QuartAdmin, QuartAdminConfig

config = QuartAdminConfig(
    name="admin",
    url_prefix="/admin",
    site_name="My Admin Panel",
    brand_color="#28a745",
    enable_search=True,
    enable_export=True,
    default_page_size=25,
    require_auth=True
)

admin = QuartAdmin(app, config=config)
```

### Configuration Options

- `name`: Blueprint name (default: "admin")
- `url_prefix`: URL prefix for admin routes (default: "/admin")
- `site_name`: Display name for the admin interface
- `brand_color`: Primary color for the UI
- `template_folder`: Custom template directory
- `static_folder`: Custom static files directory
- `enable_search`: Enable search functionality
- `enable_export`: Enable export functionality
- `enable_batch_actions`: Enable batch operations
- `default_page_size`: Default pagination size
- `require_auth`: Require authentication for access
- `csrf_protection`: Enable CSRF protection

## Providers

### Database Providers

#### SQLAlchemy Provider

```python
from quart_admin.database import SQLAlchemyProvider

provider = SQLAlchemyProvider(
    session_factory=AsyncSessionLocal,
    engine=engine  # optional
)
```

#### Custom Database Provider

```python
from quart_admin.database import DatabaseProvider

class MyDatabaseProvider(DatabaseProvider):
    async def get_all(self, model, session, **filters):
        # Implementation for getting all records
        pass

    async def get_by_id(self, model, session, id):
        # Implementation for getting record by ID
        pass

    # ... implement other required methods
```

### Authentication Providers

#### Quart-Auth Provider

```python
from quart_admin.auth import QuartAuthProvider

provider = QuartAuthProvider(
    user_loader=lambda: current_user.load_data(),
    admin_check=lambda user: user.has_role('admin')
)
```

#### Custom Auth Provider

```python
from quart_admin.auth import AuthProvider

class MyAuthProvider(AuthProvider):
    async def is_authenticated(self):
        # Check if user is authenticated
        pass

    async def has_admin_access(self):
        # Check if user has admin privileges
        pass

    # ... implement other required methods
```

### Form Providers

#### WTForms Provider

```python
from quart_admin.forms import WTFormsGenerator

generator = WTFormsGenerator()
```

## Custom Views

### Basic Custom View

```python
from quart_admin.views import AdminView

class CustomView(AdminView):
    async def list_view(self):
        # Custom list implementation
        items = await self.get_custom_data()
        return await render_template(
            self.list_template,
            view=self,
            items=items
        )

admin.add_view(CustomView("Custom", category="Special"))
```

### Enhanced Model View

```python
from quart_admin.views import ModelView

class UserAdminView(ModelView):
    column_list = ['id', 'username', 'email', 'active', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['active']
    column_labels = {
        'created_at': 'Registration Date',
        'updated_at': 'Last Modified'
    }
    form_excluded_columns = ['password_hash', 'created_at', 'updated_at']

    def format_column_value(self, item, column):
        if column == 'active':
            return '✅' if item[column] else '❌'
        return super().format_column_value(item, column)

admin.add_view(UserAdminView(User, name="Users"))
```

## Templates

### Custom Templates

You can override default templates by setting `template_folder` in configuration:

```python
config = QuartAdminConfig(
    template_folder="/path/to/custom/templates"
)
```

### Template Structure

```
templates/
├── admin/
│   ├── base.html          # Base template
│   ├── index.html         # Dashboard
│   ├── list.html          # List view
│   ├── create.html        # Create form
│   ├── edit.html          # Edit form
│   └── details.html       # Detail view
```

## API Reference

### QuartAdmin

Main admin class for managing views and configuration.

**Methods:**
- `init_app(app)`: Initialize with Quart app
- `add_view(view)`: Add custom admin view
- `add_model_view(model, **kwargs)`: Add model-based view
- `register_blueprint()`: Register admin routes

### AdminView

Base class for all admin views.

**Methods:**
- `list_view()`: Handle list requests
- `create_view()`: Handle create requests
- `edit_view(id)`: Handle edit requests
- `details_view(id)`: Handle detail requests
- `delete_view(id)`: Handle delete requests

### ModelView

Database model admin view with automatic CRUD.

**Attributes:**
- `column_list`: Columns to display in list view
- `column_searchable_list`: Searchable columns
- `column_filters`: Filterable columns
- `column_labels`: Custom column labels
- `form_excluded_columns`: Columns to exclude from forms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### 0.1.0 (Initial Release)

- Basic admin interface with CRUD operations
- Pluggable architecture for auth, database, and forms
- SQLAlchemy and Quart-Auth provider implementations
- Bootstrap-based responsive UI
- Search and pagination support
- Configurable templates and styling
