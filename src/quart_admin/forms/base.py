"""Base form generator interface."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type


class FormGenerator(ABC):
    """Abstract base class for form generators."""

    @abstractmethod
    def create_form(
        self,
        model: Type,
        database_provider,
        obj: Optional[Dict[str, Any]] = None,
        excluded_columns: Optional[List[str]] = None,
        **kwargs,
    ) -> Any:
        """Create form for model.

        Args:
            model: Database model class
            database_provider: Database provider for model introspection
            obj: Optional object to populate form with
            excluded_columns: Optional list of columns to exclude
            **kwargs: Additional form arguments

        Returns:
            Form instance
        """
        pass

    @abstractmethod
    def get_field_for_column(self, column_info: Dict[str, Any], **kwargs) -> Any:
        """Get form field for database column.

        Args:
            column_info: Column information from database provider
            **kwargs: Additional field arguments

        Returns:
            Form field instance
        """
        pass

    @abstractmethod
    def validate_form(self, form: Any) -> bool:
        """Validate form data.

        Args:
            form: Form instance to validate

        Returns:
            bool: True if form is valid
        """
        pass
