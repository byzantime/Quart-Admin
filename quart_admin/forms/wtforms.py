"""WTForms integration for form generation."""

from datetime import datetime
from types import SimpleNamespace
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DateTimeField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Optional as OptionalValidator

from .base import FormGenerator


class WTFormsGenerator(FormGenerator):
    """WTForms-based form generator."""

    def __init__(self):
        """Initialize WTFormsGenerator."""
        pass

    def create_form(
        self,
        model: Type,
        database_provider: Any,
        obj: Optional[Dict[str, Any]] = None,
        excluded_columns: Optional[List[str]] = None,
        **kwargs,
    ) -> Any:
        """Create WTForms form for model using intelligent field generation."""
        if excluded_columns is None:
            excluded_columns = []
        base_class = FlaskForm

        # Get model fields from database provider
        class DynamicForm(base_class):
            pass

        # Get column information from the model
        model_fields = database_provider.get_model_fields(model)
        if not model_fields:
            model_fields = []

        # Create fields using type mapping
        for field_info in model_fields:
            column_name = field_info["name"]

            # Skip excluded columns
            if excluded_columns and column_name in excluded_columns:
                continue

            field = self.get_field_for_column(field_info)
            setattr(DynamicForm, column_name, field)

        # Convert dictionary obj to SimpleNamespace for WTForms compatibility
        if obj and isinstance(obj, dict):
            # Parse datetime strings for datetime columns only
            converted_obj = {}
            datetime_fields = {
                field_info["name"]: field_info["type"]
                for field_info in model_fields
                if "datetime" in field_info.get("type", "").lower()
            }

            for column_name, value in obj.items():
                if column_name in datetime_fields and isinstance(value, str) and value:
                    try:
                        # SQLAlchemy typically returns ISO format: "2023-01-01T12:00:00"
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        # Keep original string if parsing fails
                        pass

                converted_obj[column_name] = value

            obj = SimpleNamespace(**converted_obj)

        # Create form instance
        form = DynamicForm(obj=obj, **kwargs)
        return form

    def get_field_for_column(self, column_info: Dict[str, Any], **kwargs) -> Any:
        """Get WTForms field for database column."""
        column_type = column_info.get("type", "").lower()
        column_name = column_info.get("name", "")
        nullable = column_info.get("nullable", True)

        validators = []
        if not nullable and not column_info.get("primary_key", False):
            validators.append(DataRequired())
        else:
            validators.append(OptionalValidator())

        # Map database types to form fields
        if "int" in column_type:
            return IntegerField(
                column_name.replace("_", " ").title(), validators=validators, **kwargs
            )
        elif "bool" in column_type:
            return BooleanField(column_name.replace("_", " ").title(), **kwargs)
        elif "text" in column_type or "clob" in column_type or "json" in column_type:
            return TextAreaField(
                column_name.replace("_", " ").title(), validators=validators, **kwargs
            )
        elif "datetime" in column_type or "timestamp" in column_type:
            return DateTimeField(
                column_name.replace("_", " ").title(), validators=validators, **kwargs
            )
        else:
            # Default to string field
            field_validators = validators.copy()
            if "varchar" in column_type or "char" in column_type:
                # Extract length if available
                try:
                    # Simple regex to extract length - would be more robust
                    import re

                    match = re.search(r"\((\d+)\)", column_type)
                    if match:
                        max_length = int(match.group(1))
                        field_validators.append(Length(max=max_length))
                except Exception:
                    pass

            return StringField(
                column_name.replace("_", " ").title(),
                validators=field_validators,
                **kwargs,
            )

    def validate_form(self, form: Any) -> bool:
        """Validate WTForms form."""
        if hasattr(form, "validate"):
            return form.validate()
        return True
