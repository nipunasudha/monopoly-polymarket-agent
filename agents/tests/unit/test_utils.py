"""
Unit tests for utility functions.
"""
import pytest
from agents.utils.utils import parse_camel_case, preprocess_market_object, metadata_func


@pytest.mark.unit
class TestParseCamelCase:
    """Test camelCase parsing utility."""

    def test_simple_camel_case(self):
        """Test parsing simple camelCase string."""
        assert parse_camel_case("camelCase") == "camel case"

    def test_multiple_capitals(self):
        """Test parsing with multiple capital letters."""
        assert parse_camel_case("thisIsATest") == "this is a test"

    def test_all_lowercase(self):
        """Test parsing all lowercase (no change)."""
        assert parse_camel_case("lowercase") == "lowercase"

    def test_single_word_capitalized(self):
        """Test single capitalized word."""
        assert parse_camel_case("Word") == " word"

    def test_empty_string(self):
        """Test empty string."""
        assert parse_camel_case("") == ""


@pytest.mark.unit
class TestPreprocessMarketObject:
    """Test market object preprocessing."""

    def test_adds_boolean_fields_to_description(self, sample_market):
        """Test that boolean fields are added to description."""
        market = sample_market.copy()
        market["active"] = True
        market["closed"] = False

        result = preprocess_market_object(market)

        assert "active" in result["description"]
        assert "not closed" in result["description"]

    def test_adds_volume_and_liquidity(self, sample_market):
        """Test that volume and liquidity are added to description."""
        market = sample_market.copy()

        result = preprocess_market_object(market)

        assert "volume" in result["description"]
        assert "liquidity" in result["description"]
        assert str(market["volume"]) in result["description"]
        assert str(market["liquidity"]) in result["description"]

    def test_preserves_original_description(self, sample_market):
        """Test that original description is preserved."""
        market = sample_market.copy()
        original_desc = market["description"]

        result = preprocess_market_object(market)

        assert original_desc in result["description"]

    def test_handles_missing_fields(self):
        """Test handling of minimal market object."""
        minimal_market = {
            "id": 1,
            "description": "Test market",
        }

        result = preprocess_market_object(minimal_market)

        assert result["description"] == "Test market"


@pytest.mark.unit
class TestMetadataFunc:
    """Test metadata function."""

    def test_copies_record_to_metadata(self):
        """Test that record fields are copied to metadata."""
        record = {"id": 123, "question": "Test?", "description": "Desc"}
        metadata = {}

        result = metadata_func(record, metadata)

        assert result["id"] == 123
        assert result["question"] == "Test?"

    def test_removes_description_field(self):
        """Test that description is removed from metadata."""
        record = {"id": 123, "description": "Should be removed"}
        metadata = {}

        result = metadata_func(record, metadata)

        assert "description" not in result

    def test_removes_events_field(self):
        """Test that events field is removed from metadata."""
        record = {"id": 123, "description": "Desc", "events": ["event1"]}
        metadata = {}

        result = metadata_func(record, metadata)

        assert "events" not in result

    def test_preserves_other_fields(self):
        """Test that other fields are preserved."""
        record = {
            "id": 123,
            "question": "Test?",
            "description": "Desc",
            "events": [],
            "liquidity": 1000,
            "volume": 5000,
        }
        metadata = {}

        result = metadata_func(record, metadata)

        assert result["id"] == 123
        assert result["question"] == "Test?"
        assert result["liquidity"] == 1000
        assert result["volume"] == 5000
        assert "description" not in result
        assert "events" not in result
