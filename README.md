# Quart-Admin

⚠️ **DEVELOPMENT STATUS WARNING** ⚠️

**This project is in early development and is NOT ready for production use or public consumption. It currently has no tests, incomplete functionality, and may undergo significant breaking changes. Please do not use this in any real projects at this time.**

---

An async admin interface for Quart applications, inspired by Flask-Admin but built specifically for Quart's async capabilities.

## Planned Features

- **Fully Async**: Built for Quart's async/await patterns
- **Pluggable Architecture**: Extensible auth, database, and form providers
- **Database Support**: SQLAlchemy async support
- **Authentication**: Basic auth provider structure
- **CRUD Operations**: Basic model views and forms
- **Templates**: Bootstrap-based HTML templates included

## Installation

**NOT RECOMMENDED - PROJECT NOT READY FOR USE**

For development only:

```bash
git clone https://github.com/yourusername/quart-admin
cd quart-admin
uv sync --extra dev
```

## Development Status

This project currently includes:

- Basic `QuartAdmin` class structure
- Configuration system (`QuartAdminConfig`)
- Provider interfaces for auth, database, and forms
- Basic view classes (`AdminView`, `ModelView`)
- HTML templates for admin interface
- SQLAlchemy and WTForms provider implementations (partial)

**What's missing:**
- Tests (none exist yet)
- Complete implementations of providers
- Working examples
- Documentation beyond this README
- Proper error handling
- Security features

## Project Structure

```
src/quart_admin/
├── admin.py           # Main QuartAdmin class
├── config.py          # Configuration dataclass
├── auth/              # Authentication providers
├── database/          # Database providers
├── forms/             # Form generators
├── views/             # Admin view classes
└── templates/         # HTML templates
```

## Development Notes

The project uses a provider pattern for extensibility:

- **Database providers**: Abstract database operations
- **Auth providers**: Handle authentication and authorization
- **Form generators**: Create forms from models
- **View classes**: Handle HTTP requests and responses

All providers are designed around async/await patterns.


## Contributing

**Please wait** - This project is not ready for external contributions yet. Once basic functionality is implemented and tested, contribution guidelines will be added.
