"""Form generation for Quart-Admin."""

from .base import FormGenerator
from .wtforms import WTFormsGenerator

__all__ = ["FormGenerator", "WTFormsGenerator"]
