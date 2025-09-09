"""Unit tests for ModelView with enhanced Python object handling."""

import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from quart_admin.views.model import ModelView


class TestModelView:
    """Test ModelView with enhanced Python object handling."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock model
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"

        # Mock providers
        self.mock_db_provider = MagicMock()
        self.mock_form_generator = MagicMock()

        # Create ModelView instance
        self.view = ModelView(
            model=self.mock_model,
            database_provider=self.mock_db_provider,
            form_generator=self.mock_form_generator,
        )

    @pytest.fixture
    def sample_model_fields(self):
        """Sample model fields with various types including JSON."""
        return [
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
            {
                "name": "is_active",
                "type": "BOOLEAN",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "created_at",
                "type": "DATETIME",
                "nullable": False,
                "primary_key": False,
            },
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "settings",
                "type": "JSONB",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "description",
                "type": "TEXT",
                "nullable": True,
                "primary_key": False,
            },
        ]


class TestProcessFormData:
    """Test the process_form_data method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"
        self.mock_db_provider = MagicMock()

        self.view = ModelView(
            model=self.mock_model, database_provider=self.mock_db_provider
        )

    def test_json_string_conversion_valid_json(self):
        """Test that valid JSON strings are converted back to Python objects."""
        model_fields = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with JSON string data
        mock_form = MagicMock()
        mock_metadata_field = MagicMock()
        mock_metadata_field.name = "metadata"
        mock_metadata_field.data = '{"key": "value", "nested": {"count": 42}}'

        mock_name_field = MagicMock()
        mock_name_field.name = "name"
        mock_name_field.data = "Test Name"

        mock_csrf_field = MagicMock()
        mock_csrf_field.name = "csrf_token"
        mock_csrf_field.data = "csrf_token_value"

        mock_form.__iter__.return_value = [
            mock_metadata_field,
            mock_name_field,
            mock_csrf_field,
        ]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify JSON was parsed
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)
        assert result["metadata"] == {"key": "value", "nested": {"count": 42}}

        # Verify non-JSON fields are unchanged
        assert result["name"] == "Test Name"

        # Verify CSRF token is excluded
        assert "csrf_token" not in result

    def test_json_string_conversion_invalid_json(self):
        """Test that invalid JSON strings are kept as strings."""
        model_fields = [
            {"name": "metadata", "type": "JSON", "nullable": True, "primary_key": False}
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with invalid JSON string data
        mock_form = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "metadata"
        mock_field.data = '{"invalid": json, missing quotes}'

        mock_form.__iter__.return_value = [mock_field]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify invalid JSON is kept as string
        assert result["metadata"] == '{"invalid": json, missing quotes}'

    def test_json_empty_string_handling(self):
        """Test that empty JSON strings are handled properly."""
        model_fields = [
            {"name": "metadata", "type": "JSON", "nullable": True, "primary_key": False}
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with empty string data
        mock_form = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "metadata"
        mock_field.data = ""

        mock_form.__iter__.return_value = [mock_field]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify empty string is kept as is (not parsed as JSON)
        assert result["metadata"] == ""

    def test_json_whitespace_only_handling(self):
        """Test that whitespace-only JSON strings are handled properly."""
        model_fields = [
            {"name": "metadata", "type": "JSON", "nullable": True, "primary_key": False}
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with whitespace-only data
        mock_form = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "metadata"
        mock_field.data = "   \t\n  "

        mock_form.__iter__.return_value = [mock_field]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify whitespace-only string is kept as is
        assert result["metadata"] == "   \t\n  "

    def test_non_json_fields_unchanged(self):
        """Test that non-JSON fields are not processed."""
        model_fields = [
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
            {
                "name": "count",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": False,
            },
            {
                "name": "is_active",
                "type": "BOOLEAN",
                "nullable": True,
                "primary_key": False,
            },
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with various data types
        mock_form = MagicMock()

        mock_name_field = MagicMock()
        mock_name_field.name = "name"
        mock_name_field.data = "Test Name"

        mock_count_field = MagicMock()
        mock_count_field.name = "count"
        mock_count_field.data = 42

        mock_active_field = MagicMock()
        mock_active_field.name = "is_active"
        mock_active_field.data = True

        mock_form.__iter__.return_value = [
            mock_name_field,
            mock_count_field,
            mock_active_field,
        ]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify all fields are unchanged
        assert result["name"] == "Test Name"
        assert result["count"] == 42
        assert result["is_active"] is True

    def test_none_values_handled(self):
        """Test that None values are handled properly."""
        model_fields = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": True,
                "primary_key": False,
            },
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with None values
        mock_form = MagicMock()

        mock_metadata_field = MagicMock()
        mock_metadata_field.name = "metadata"
        mock_metadata_field.data = None

        mock_name_field = MagicMock()
        mock_name_field.name = "name"
        mock_name_field.data = None

        mock_form.__iter__.return_value = [mock_metadata_field, mock_name_field]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify None values are excluded from result
        assert "metadata" not in result
        assert "name" not in result

    def test_json_list_conversion(self):
        """Test that JSON list strings are converted back to lists."""
        model_fields = [
            {"name": "tags", "type": "JSON", "nullable": True, "primary_key": False}
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mock form with JSON list string
        mock_form = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "tags"
        mock_field.data = '[{"id": 1, "name": "Tag 1"}, {"id": 2, "name": "Tag 2"}]'

        mock_form.__iter__.return_value = [mock_field]

        # Process form data
        result = self.view.process_form_data(mock_form)

        # Verify JSON list was parsed
        assert isinstance(result["tags"], list)
        assert result["tags"] == [
            {"id": 1, "name": "Tag 1"},
            {"id": 2, "name": "Tag 2"},
        ]


class TestFormatColumnValue:
    """Test the enhanced format_column_value method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"

        self.view = ModelView(model=self.mock_model)

    def test_dict_formatting(self):
        """Test formatting of dictionary objects."""
        item = {"data": {"key": "value", "nested": {"count": 42}}}

        result = self.view.format_column_value(item, "data")

        # Should be formatted as compact JSON
        expected = '{"key":"value","nested":{"count":42}}'
        assert result == expected

    def test_list_formatting(self):
        """Test formatting of list objects."""
        item = {"tags": [{"id": 1, "name": "Tag 1"}, {"id": 2, "name": "Tag 2"}]}

        result = self.view.format_column_value(item, "tags")

        # Should be formatted as compact JSON
        expected = '[{"id":1,"name":"Tag 1"},{"id":2,"name":"Tag 2"}]'
        assert result == expected

    def test_long_json_truncation(self):
        """Test truncation of long JSON objects."""
        # Create a long dictionary
        long_dict = {f"key_{i}": f"value_{i}" for i in range(20)}
        item = {"data": long_dict}

        result = self.view.format_column_value(item, "data")

        # Should be truncated with ellipsis
        assert len(result) <= 100
        assert result.endswith("...")

    def test_json_serialization_fallback(self):
        """Test fallback when JSON serialization fails."""

        # Create non-serializable object
        class NonSerializable:
            def __str__(self):
                return "non_serializable_object"

        item = {"data": NonSerializable()}

        result = self.view.format_column_value(item, "data")

        # Should fallback to string representation
        assert result == "non_serializable_object"

    def test_long_non_json_truncation(self):
        """Test that regular string objects are not truncated (only JSON objects are)."""

        class LongStringObject:
            def __str__(self):
                return "a" * 150  # Longer than 100 characters

        item = {"data": LongStringObject()}

        result = self.view.format_column_value(item, "data")

        # Regular string objects are not truncated in the current implementation
        # Only dict/list objects are truncated when JSON serialized
        assert result == "a" * 150

    def test_datetime_formatting_preserved(self):
        """Test that datetime formatting is preserved."""
        test_datetime = datetime(2023, 1, 1, 12, 30, 45)
        item = {"created_at": test_datetime}

        result = self.view.format_column_value(item, "created_at")

        # Should be formatted as before
        assert result == "2023-01-01 12:30"

    def test_boolean_formatting_preserved(self):
        """Test that boolean formatting is preserved."""
        item_true = {"is_active": True}
        item_false = {"is_active": False}

        result_true = self.view.format_column_value(item_true, "is_active")
        result_false = self.view.format_column_value(item_false, "is_active")

        # Should be formatted with checkmarks
        assert result_true == "✓"
        assert result_false == "✗"

    def test_none_value_handling(self):
        """Test formatting of None values."""
        item = {"data": None}

        result = self.view.format_column_value(item, "data")

        # Should return empty string
        assert result == ""

    def test_missing_column_handling(self):
        """Test formatting when column doesn't exist in item."""
        item = {"other_field": "value"}

        result = self.view.format_column_value(item, "missing_field")

        # Should return empty string
        assert result == ""

    def test_custom_formatter_priority(self):
        """Test that custom formatters take priority over default formatting."""

        # Set up custom formatter
        def custom_formatter(item, column):
            return f"Custom: {item[column]}"

        self.view.column_formatters = {"data": custom_formatter}

        item = {"data": {"key": "value"}}

        result = self.view.format_column_value(item, "data")

        # Should use custom formatter instead of JSON formatting
        assert result == "Custom: {'key': 'value'}"

    def test_empty_dict_formatting(self):
        """Test formatting of empty dictionary."""
        item = {"data": {}}

        result = self.view.format_column_value(item, "data")

        # Should format as empty JSON object
        assert result == "{}"

    def test_empty_list_formatting(self):
        """Test formatting of empty list."""
        item = {"data": []}

        result = self.view.format_column_value(item, "data")

        # Should format as empty JSON array
        assert result == "[]"


class TestProcessFormDataIntegration:
    """Test process_form_data method integration with the views."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"
        self.mock_db_provider = MagicMock()

        self.view = ModelView(
            model=self.mock_model,
            database_provider=self.mock_db_provider,
        )

        # Mock get_model_fields for process_form_data
        self.mock_db_provider.get_model_fields.return_value = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
        ]

    def test_process_form_data_integration(self):
        """Test that process_form_data works correctly with form-like objects."""

        # Create mock form that behaves like a WTForms form
        class MockField:
            def __init__(self, name, data):
                self.name = name
                self.data = data

        mock_fields = [
            MockField("metadata", '{"key": "value", "count": 42}'),
            MockField("name", "Test Name"),
            MockField("csrf_token", "csrf_value"),  # Should be excluded
        ]

        # Mock form that iterates over fields
        mock_form = MagicMock()
        mock_form.__iter__.return_value = mock_fields

        # Test the process_form_data method
        result = self.view.process_form_data(mock_form)

        # Verify results
        assert len(result) == 2  # Only non-CSRF fields
        assert "metadata" in result
        assert "name" in result
        assert "csrf_token" not in result

        # Verify JSON was parsed
        assert isinstance(result["metadata"], dict)
        assert result["metadata"] == {"key": "value", "count": 42}

        # Verify non-JSON field unchanged
        assert result["name"] == "Test Name"


class TestModelViewPerformance:
    """Test performance and robustness characteristics of ModelView."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"
        self.mock_db_provider = MagicMock()

        self.view = ModelView(
            model=self.mock_model,
            database_provider=self.mock_db_provider,
        )

    def test_process_form_data_with_large_json_objects(self):
        """Test processing form data with large JSON objects."""
        # Set up model fields with JSON type
        model_fields = [
            {
                "name": "large_data",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            }
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Create a large nested JSON structure
        large_data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "profile": {
                        "preferences": {
                            "theme": "dark",
                            "language": "en",
                            "notifications": {
                                "email": True,
                                "push": False,
                                "sms": True,
                            },
                        },
                        "settings": {
                            "privacy": {"public": True, "searchable": False},
                            "security": {
                                "two_factor": True,
                                "backup_codes": list(range(10)),
                            },
                        },
                    },
                    "metadata": {"tags": [f"tag{j}" for j in range(10)]},
                }
                for i in range(100)  # 100 users with nested data
            ],
            "statistics": {
                "total_users": 100,
                "active_users": 95,
                "metrics": {f"metric_{i}": i * 10 for i in range(50)},
            },
        }

        # Mock form with large JSON data
        mock_form = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "large_data"
        mock_field.data = json.dumps(large_data)
        mock_form.__iter__.return_value = [mock_field]

        # Process form data and measure performance
        import time

        start_time = time.time()
        result = self.view.process_form_data(mock_form)
        end_time = time.time()

        # Verify the processing completed in reasonable time (< 1 second)
        processing_time = end_time - start_time
        assert processing_time < 1.0, f"Processing took too long: {processing_time}s"

        # Verify the large data was correctly parsed
        assert "large_data" in result
        assert isinstance(result["large_data"], dict)
        assert len(result["large_data"]["users"]) == 100
        assert result["large_data"]["statistics"]["total_users"] == 100

    def test_format_column_value_with_deeply_nested_objects(self):
        """Test formatting deeply nested JSON objects."""

        # Create deeply nested structure (10 levels deep)
        def create_nested_dict(depth, current_depth=0):
            if current_depth >= depth:
                return {"value": f"level_{current_depth}"}
            return {
                f"level_{current_depth}": create_nested_dict(depth, current_depth + 1),
                "data": [f"item_{current_depth}_{i}" for i in range(5)],
            }

        deeply_nested = create_nested_dict(10)
        item = {"nested_data": deeply_nested}

        # Format the column value
        result = self.view.format_column_value(item, "nested_data")

        # Should be truncated due to length
        assert isinstance(result, str)
        assert len(result) <= 100  # Truncated to max length
        assert result.endswith("...")

    def test_process_form_data_memory_efficiency(self):
        """Test memory efficiency with multiple JSON fields."""
        # Set up multiple JSON fields
        model_fields = [
            {
                "name": f"json_field_{i}",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            }
            for i in range(20)  # 20 JSON fields
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Create form with multiple JSON fields
        mock_fields = []
        for i in range(20):
            mock_field = MagicMock()
            mock_field.name = f"json_field_{i}"
            # Each field has moderate sized JSON data
            mock_field.data = json.dumps(
                {
                    "data": [{"id": j, "value": f"item_{j}"} for j in range(50)],
                    "metadata": {"field_index": i, "items_count": 50},
                }
            )
            mock_fields.append(mock_field)

        mock_form = MagicMock()
        mock_form.__iter__.return_value = mock_fields

        # Process all fields
        result = self.view.process_form_data(mock_form)

        # Verify all fields were processed correctly
        assert len(result) == 20
        for i in range(20):
            field_name = f"json_field_{i}"
            assert field_name in result
            assert isinstance(result[field_name], dict)
            assert len(result[field_name]["data"]) == 50
            assert result[field_name]["metadata"]["field_index"] == i

    def test_format_column_value_robustness(self):
        """Test robustness of column formatting with edge cases."""
        # Test with circular reference object (should not crash)
        circular_obj = {"name": "test"}
        circular_obj["self_ref"] = circular_obj
        item_circular = {"data": circular_obj}

        # Should handle gracefully without crashing
        result = self.view.format_column_value(item_circular, "data")
        assert isinstance(result, str)
        # Should fallback to string representation since JSON serialization fails

        # Test with special float values
        item_special = {"data": {"inf": float("inf"), "nan": float("nan")}}
        result = self.view.format_column_value(item_special, "data")
        assert isinstance(result, str)

        # Test with complex data types that are not JSON serializable
        class CustomClass:
            def __str__(self):
                return "custom_object"

        item_custom = {"data": {"custom": CustomClass(), "regular": "value"}}
        result = self.view.format_column_value(item_custom, "data")
        assert isinstance(result, str)

    def test_process_form_data_error_resilience(self):
        """Test error resilience when processing malformed JSON."""
        model_fields = [
            {
                "name": "good_json",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "bad_json",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
            {
                "name": "empty_json",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
        ]
        self.mock_db_provider.get_model_fields.return_value = model_fields

        # Mix of good, bad, and edge case JSON
        mock_fields = []

        # Good JSON
        good_field = MagicMock()
        good_field.name = "good_json"
        good_field.data = '{"valid": "json", "number": 42}'
        mock_fields.append(good_field)

        # Bad JSON (should be kept as string)
        bad_field = MagicMock()
        bad_field.name = "bad_json"
        bad_field.data = '{"invalid": json, "missing": quotes}'
        mock_fields.append(bad_field)

        # Empty JSON
        empty_field = MagicMock()
        empty_field.name = "empty_json"
        empty_field.data = ""
        mock_fields.append(empty_field)

        mock_form = MagicMock()
        mock_form.__iter__.return_value = mock_fields

        # Should not raise exceptions
        result = self.view.process_form_data(mock_form)

        # Verify handling
        assert isinstance(result["good_json"], dict)
        assert result["good_json"]["valid"] == "json"
        assert result["good_json"]["number"] == 42

        # Bad JSON should be kept as string
        assert isinstance(result["bad_json"], str)
        assert result["bad_json"] == '{"invalid": json, "missing": quotes}'

        # Empty should be kept as string
        assert result["empty_json"] == ""
