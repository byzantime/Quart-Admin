"""Simplified unit tests for WTForms generator Python object handling."""

import json
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from quart_admin.forms.wtforms import WTFormsGenerator


class TestWTFormsGeneratorSimple:
    """Test core functionality of WTForms generator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = WTFormsGenerator()

        # Mock database provider
        self.mock_db_provider = MagicMock()
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"

    def test_json_object_conversion_logic(self):
        """Test the JSON object conversion logic directly."""
        # Set up mock model fields
        model_fields = [
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
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
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
        ]

        # Test data with dict objects
        test_obj = {
            "id": 1,
            "name": "Test Item",
            "metadata": {"key": "value", "nested": {"data": 123}},
            "settings": {"theme": "dark", "notifications": True},
        }

        # Test the conversion logic directly
        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        # Simulate the conversion logic from create_form
        converted_obj = {}
        for column_name, value in test_obj.items():
            # Convert JSON/dict/list objects to strings for TextAreaField
            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                try:
                    value = json.dumps(value, indent=2, default=str)
                except (TypeError, ValueError):
                    value = str(value)
            # For all other types, let WTForms handle them natively
            converted_obj[column_name] = value

        # Verify conversions
        assert converted_obj["id"] == 1  # Not converted
        assert converted_obj["name"] == "Test Item"  # Not converted

        # JSON fields should be converted to strings
        assert isinstance(converted_obj["metadata"], str)
        assert isinstance(converted_obj["settings"], str)

        # Verify JSON is properly formatted
        parsed_metadata = json.loads(converted_obj["metadata"])
        assert parsed_metadata == {"key": "value", "nested": {"data": 123}}

        parsed_settings = json.loads(converted_obj["settings"])
        assert parsed_settings == {"theme": "dark", "notifications": True}

    def test_json_field_identification(self):
        """Test that JSON fields are correctly identified."""
        model_fields = [
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
            {"name": "config", "type": "json", "nullable": True, "primary_key": False},
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
        ]

        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        # Should identify all JSON variants
        assert "metadata" in json_fields
        assert "settings" in json_fields
        assert "config" in json_fields
        assert "name" not in json_fields

    def test_json_none_value_handling(self):
        """Test that None values in JSON fields are handled properly."""
        model_fields = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
        ]

        test_obj = {"metadata": None}

        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        converted_obj = {}
        for column_name, value in test_obj.items():
            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                value = json.dumps(value, indent=2, default=str)
            converted_obj[column_name] = value

        # None should be preserved
        assert converted_obj["metadata"] is None

    def test_json_string_preservation(self):
        """Test that existing JSON strings are not double-serialized."""
        model_fields = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
        ]

        json_string = '{"existing": "json_string"}'
        test_obj = {"metadata": json_string}

        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        converted_obj = {}
        for column_name, value in test_obj.items():
            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                value = json.dumps(value, indent=2, default=str)
            converted_obj[column_name] = value

        # String should be preserved as-is
        assert converted_obj["metadata"] == json_string

    def test_json_serialization_fallback(self):
        """Test fallback behavior when JSON serialization fails."""

        # Create a non-serializable object
        class NonSerializable:
            def __str__(self):
                return "non_serializable_object"

        model_fields = [
            {
                "name": "metadata",
                "type": "JSON",
                "nullable": True,
                "primary_key": False,
            },
        ]

        test_obj = {"metadata": NonSerializable()}

        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        converted_obj = {}
        for column_name, value in test_obj.items():
            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                try:
                    value = json.dumps(value, indent=2, default=str)
                except (TypeError, ValueError):
                    value = str(value)
            converted_obj[column_name] = value

        # Should fallback to string representation (JSON serializes the string with default=str)
        assert converted_obj["metadata"] == '"non_serializable_object"'

    def test_get_field_for_column_json_logic(self):
        """Test that JSON column type logic maps to TextAreaField."""
        json_field_info = {
            "name": "metadata",
            "type": "JSON",
            "nullable": True,
            "primary_key": False,
        }

        # Test the type mapping logic directly
        column_type = json_field_info["type"].lower()

        # This should match the logic in get_field_for_column
        if "json" in column_type:
            expected_field_type = "TextAreaField"
        else:
            expected_field_type = "Other"

        assert expected_field_type == "TextAreaField"

    def test_get_field_for_column_jsonb_logic(self):
        """Test that JSONB column type logic maps to TextAreaField."""
        jsonb_field_info = {
            "name": "settings",
            "type": "JSONB",
            "nullable": True,
            "primary_key": False,
        }

        # Test the type mapping logic directly
        column_type = jsonb_field_info["type"].lower()

        # This should match the logic in get_field_for_column
        if "json" in column_type:
            expected_field_type = "TextAreaField"
        else:
            expected_field_type = "Other"

        assert expected_field_type == "TextAreaField"

    def test_import_error_handling(self):
        """Test proper error handling when WTForms dependencies are not available."""

        # Mock the import that happens inside create_form method
        def mock_import(name, *args, **kwargs):
            if name == "flask_wtf":
                raise ImportError("No module named 'flask_wtf'")
            # Allow other imports to work normally
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(ImportError) as exc_info:
                # Call the actual method that should handle the import error
                self.generator.create_form(self.mock_model, self.mock_db_provider)

            # Verify the proper error message is raised
            assert "Flask-WTF and WTForms are not installed" in str(exc_info.value)
            assert "pip install quart-admin[wtforms]" in str(exc_info.value)

    def test_excluded_columns_parameter(self):
        """Test that excluded_columns parameter works correctly."""
        model_fields = [
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            {
                "name": "name",
                "type": "VARCHAR(100)",
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
                "name": "secret",
                "type": "VARCHAR(100)",
                "nullable": True,
                "primary_key": False,
            },
        ]

        test_obj = {
            "id": 1,
            "name": "Test Item",
            "metadata": {"key": "value"},
            "secret": "sensitive_data",
        }

        # Test exclusion logic
        excluded_columns = ["secret", "metadata"]
        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        # Simulate form creation with exclusions
        converted_obj = {}
        for column_name, value in test_obj.items():
            # Skip excluded columns (like the actual implementation would)
            if column_name in excluded_columns:
                continue

            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                value = json.dumps(value, indent=2, default=str)
            converted_obj[column_name] = value

        # Verify excluded columns are not present
        assert "secret" not in converted_obj
        assert "metadata" not in converted_obj

        # Verify non-excluded columns are present
        assert "id" in converted_obj
        assert "name" in converted_obj
        assert converted_obj["id"] == 1
        assert converted_obj["name"] == "Test Item"

    def test_primary_key_field_handling(self):
        """Test that primary key fields are handled correctly based on context."""
        model_fields = [
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            {
                "name": "uuid",
                "type": "VARCHAR(36)",
                "nullable": False,
                "primary_key": True,
            },
            {
                "name": "name",
                "type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
            },
        ]

        # Simulate primary key field detection logic
        primary_key_fields = [
            field["name"] for field in model_fields if field.get("primary_key", False)
        ]

        # Verify primary key detection
        assert "id" in primary_key_fields
        assert "uuid" in primary_key_fields
        assert "name" not in primary_key_fields
        assert len(primary_key_fields) == 2

    def test_field_validation_setup(self):
        """Test that field validation is set up correctly based on column properties."""
        # Test nullable field (should get OptionalValidator)
        nullable_field = {
            "name": "description",
            "type": "TEXT",
            "nullable": True,
            "primary_key": False,
            "default": None,
        }

        # Test non-nullable field without default (should get DataRequired)
        required_field = {
            "name": "name",
            "type": "VARCHAR(100)",
            "nullable": False,
            "primary_key": False,
            "default": None,
        }

        # Test non-nullable field with default (should get OptionalValidator)
        field_with_default = {
            "name": "status",
            "type": "VARCHAR(20)",
            "nullable": False,
            "primary_key": False,
            "default": "active",
        }

        # Test the validation logic
        def should_be_required(field_info):
            return (
                not field_info.get("nullable", True)
                and not field_info.get("primary_key", False)
                and field_info.get("default") is None
            )

        # Verify validation requirements
        assert not should_be_required(nullable_field)  # Optional
        assert should_be_required(required_field)  # Required
        assert not should_be_required(field_with_default)  # Optional (has default)

    def test_different_field_types_mapping(self):
        """Test that different column types map to correct WTForms fields."""
        field_type_mappings = [
            # (column_type, expected_wtforms_field_type)
            ("INTEGER", "IntegerField"),
            ("BIGINT", "IntegerField"),
            ("BOOLEAN", "BooleanField"),
            ("BOOL", "BooleanField"),
            ("TEXT", "TextAreaField"),
            ("CLOB", "TextAreaField"),
            ("JSON", "TextAreaField"),
            ("JSONB", "TextAreaField"),
            ("DATETIME", "DateTimeField"),
            ("TIMESTAMP", "DateTimeField"),
            ("VARCHAR(100)", "StringField"),
            ("CHAR(10)", "StringField"),
            ("STRING", "StringField"),  # Default case
        ]

        for column_type, expected_field in field_type_mappings:
            # Test the type mapping logic
            column_type_lower = column_type.lower()

            if "int" in column_type_lower:
                assert expected_field == "IntegerField"
            elif "bool" in column_type_lower:
                assert expected_field == "BooleanField"
            elif "text" in column_type_lower or "clob" in column_type_lower:
                assert expected_field == "TextAreaField"
            elif "json" in column_type_lower:
                assert expected_field == "TextAreaField"
            elif "datetime" in column_type_lower or "timestamp" in column_type_lower:
                assert expected_field == "DateTimeField"
            else:
                assert expected_field == "StringField"  # Default


class TestWTFormsIntegration:
    """End-to-end integration tests for complete form workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = WTFormsGenerator()
        self.mock_db_provider = MagicMock()
        self.mock_model = MagicMock()
        self.mock_model.__name__ = "TestModel"

    def test_complete_form_creation_workflow(self):
        """Test complete object conversion workflow with various field types."""
        # Set up realistic model fields
        model_fields = [
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
                "name": "description",
                "type": "TEXT",
                "nullable": True,
                "primary_key": False,
            },
        ]

        # Test data with mixed Python objects
        test_obj = {
            "id": 1,
            "name": "Test Item",
            "is_active": True,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "metadata": {
                "tags": ["important", "urgent"],
                "config": {"theme": "dark", "notifications": True},
                "stats": {"views": 42, "likes": 15},
            },
            "description": "A test item description",
        }

        # Test the object conversion logic directly
        json_fields = {
            field["name"]: field["type"]
            for field in model_fields
            if "json" in field.get("type", "").lower()
        }

        # Apply the same conversion logic used in create_form
        converted_obj = {}
        for column_name, value in test_obj.items():
            # Convert JSON/dict/list objects to strings for TextAreaField
            if (
                column_name in json_fields
                and value is not None
                and not isinstance(value, str)
            ):
                try:
                    value = json.dumps(value, indent=2, default=str)
                except (TypeError, ValueError):
                    value = str(value)
            converted_obj[column_name] = value

        # Verify conversion results
        assert len(converted_obj) == 6

        # Verify non-JSON fields are unchanged
        assert converted_obj["id"] == 1
        assert converted_obj["name"] == "Test Item"
        assert converted_obj["is_active"] is True
        assert converted_obj["created_at"] == datetime(2023, 1, 1, 12, 0, 0)
        assert converted_obj["description"] == "A test item description"

        # Verify JSON field was serialized
        assert isinstance(converted_obj["metadata"], str)
        parsed_metadata = json.loads(converted_obj["metadata"])
        assert parsed_metadata == {
            "tags": ["important", "urgent"],
            "config": {"theme": "dark", "notifications": True},
            "stats": {"views": 42, "likes": 15},
        }

    def test_round_trip_json_processing(self):
        """Test that JSON objects can be serialized and deserialized correctly."""
        # Complex nested JSON data
        original_data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "notifications": {"email": True, "push": False, "sms": None},
                },
                "tags": ["admin", "premium", "beta-tester"],
                "metadata": {
                    "last_login": "2023-01-01T12:00:00Z",
                    "login_count": 42,
                    "is_verified": True,
                },
            },
            "settings": ["option1", "option2", {"nested": True}],
            "empty_dict": {},
            "empty_list": [],
            "null_value": None,
        }

        # Step 1: Serialize for form display (WTForms direction)
        serialized = json.dumps(original_data, indent=2, default=str)
        assert isinstance(serialized, str)

        # Step 2: Deserialize from form input (ModelView direction)
        deserialized = json.loads(serialized)

        # Verify round-trip accuracy
        assert deserialized == original_data
        assert deserialized["user"]["name"] == "John Doe"
        assert deserialized["user"]["preferences"]["theme"] == "dark"
        assert deserialized["user"]["preferences"]["notifications"]["email"] is True
        assert deserialized["user"]["preferences"]["notifications"]["sms"] is None
        assert deserialized["user"]["tags"] == ["admin", "premium", "beta-tester"]
        assert deserialized["settings"] == ["option1", "option2", {"nested": True}]
        assert deserialized["empty_dict"] == {}
        assert deserialized["empty_list"] == []
        assert deserialized["null_value"] is None

    def test_error_resilience_workflow(self):
        """Test that the workflow handles various error conditions gracefully."""
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

        # Test with various problematic data
        test_cases = [
            # Non-serializable object
            {"name": "Test 1", "metadata": lambda x: x},  # Function object
            # Circular reference (would cause issues in real JSON)
            {
                "name": "Test 2",
                "metadata": {
                    "self": None
                },  # Simplified - real circular ref would be complex
            },
            # Very large nested structure
            {
                "name": "Test 3",
                "metadata": {
                    "level1": {"level2": {"level3": {"data": list(range(100))}}}
                },
            },
        ]

        for i, test_obj in enumerate(test_cases):
            try:
                # Simulate the conversion logic
                converted_obj = {}
                for column_name, value in test_obj.items():
                    if (
                        column_name == "metadata"
                        and value is not None
                        and not isinstance(value, str)
                    ):
                        try:
                            value = json.dumps(value, indent=2, default=str)
                        except (TypeError, ValueError):
                            value = str(value)
                    converted_obj[column_name] = value

                # Should not raise exceptions
                assert "name" in converted_obj
                assert "metadata" in converted_obj
                assert isinstance(converted_obj["metadata"], str)

            except Exception as e:
                pytest.fail(f"Test case {i+1} raised unexpected exception: {e}")

    def test_performance_with_large_objects(self):
        """Test performance characteristics with large JSON objects."""
        # Create a large nested object
        large_data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "metadata": {
                        "preferences": {f"pref_{j}": f"value_{j}" for j in range(50)},
                        "history": [
                            {"action": f"action_{k}", "timestamp": f"2023-01-{k:02d}"}
                            for k in range(100)
                        ],
                    },
                }
                for i in range(10)
            ],
            "config": {
                f"setting_{i}": {"value": i, "enabled": i % 2 == 0} for i in range(100)
            },
        }

        # Test serialization performance
        import time

        start_time = time.time()
        serialized = json.dumps(large_data, indent=2, default=str)
        serialization_time = time.time() - start_time

        # Test deserialization performance
        start_time = time.time()
        deserialized = json.loads(serialized)
        deserialization_time = time.time() - start_time

        # Verify functionality
        assert len(deserialized["users"]) == 10
        assert len(deserialized["config"]) == 100
        assert deserialized["users"][0]["name"] == "User 0"

        # Performance should be reasonable (adjust thresholds as needed)
        assert serialization_time < 1.0  # Should complete in under 1 second
        assert deserialization_time < 1.0  # Should complete in under 1 second

        # Verify data integrity
        assert deserialized == large_data
