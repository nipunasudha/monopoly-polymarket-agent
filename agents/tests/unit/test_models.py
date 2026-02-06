"""
Unit tests for Pydantic models.
"""
import pytest
from pydantic import ValidationError
from agents.utils.objects import (
    Trade,
    SimpleMarket,
    Market,
    PolymarketEvent,
    Article,
    Source,
)


@pytest.mark.unit
class TestTradeModel:
    """Test Trade Pydantic model."""

    def test_valid_trade_creation(self):
        """Test creating a valid Trade object."""
        trade_data = {
            "id": 1,
            "taker_order_id": "order123",
            "market": "market456",
            "asset_id": "asset789",
            "side": "BUY",
            "size": "100",
            "fee_rate_bps": "10",
            "price": "0.50",
            "status": "MATCHED",
            "match_time": "2026-01-01T00:00:00Z",
            "last_update": "2026-01-01T00:00:00Z",
            "outcome": "Yes",
            "maker_address": "0x123",
            "owner": "0x456",
            "transaction_hash": "0xabc",
            "bucket_index": "5",
            "maker_orders": ["order1", "order2"],
            "type": "MARKET",
        }

        trade = Trade(**trade_data)

        assert trade.id == 1
        assert trade.side == "BUY"
        assert trade.size == "100"
        assert len(trade.maker_orders) == 2

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "id": 1,
            "taker_order_id": "order123",
            # Missing many required fields
        }

        with pytest.raises(ValidationError):
            Trade(**incomplete_data)


@pytest.mark.unit
class TestSimpleMarketModel:
    """Test SimpleMarket Pydantic model."""

    def test_valid_simple_market(self):
        """Test creating a valid SimpleMarket."""
        market_data = {
            "id": 123,
            "question": "Will it rain tomorrow?",
            "end": "2026-12-31T23:59:59Z",
            "description": "Weather prediction market",
            "active": True,
            "funded": True,
            "rewardsMinSize": 10.0,
            "rewardsMaxSpread": 0.05,
            "spread": 0.02,
            "outcomes": "Yes,No",
            "outcome_prices": "0.45,0.55",
            "clob_token_ids": "token1,token2",
        }

        market = SimpleMarket(**market_data)

        assert market.id == 123
        assert market.question == "Will it rain tomorrow?"
        assert market.active is True
        assert market.spread == 0.02

    def test_optional_clob_token_ids(self):
        """Test that clob_token_ids is optional."""
        market_data = {
            "id": 123,
            "question": "Test?",
            "end": "2026-12-31",
            "description": "Test",
            "active": True,
            "funded": True,
            "rewardsMinSize": 10.0,
            "rewardsMaxSpread": 0.05,
            "spread": 0.02,
            "outcomes": "Yes,No",
            "outcome_prices": "0.5,0.5",
            "clob_token_ids": None,
        }

        market = SimpleMarket(**market_data)

        assert market.clob_token_ids is None


@pytest.mark.unit
class TestMarketModel:
    """Test Market Pydantic model."""

    def test_all_fields_optional_except_id(self):
        """Test that only id is required."""
        minimal_market = {"id": 999}

        market = Market(**minimal_market)

        assert market.id == 999
        assert market.question is None
        assert market.liquidity is None

    def test_full_market_object(self, sample_market):
        """Test creating a full Market object."""
        market = Market(**sample_market)

        assert market.id == sample_market["id"]
        assert market.question == sample_market["question"]
        assert market.liquidity == sample_market["liquidity"]
        assert market.active == sample_market["active"]


@pytest.mark.unit
class TestPolymarketEventModel:
    """Test PolymarketEvent Pydantic model."""

    def test_minimal_event(self):
        """Test creating event with only required field (id)."""
        event = PolymarketEvent(id="12345")

        assert event.id == "12345"
        assert event.title is None
        assert event.active is None

    def test_full_event(self):
        """Test creating full event object."""
        # PolymarketEvent expects markets as list, not string
        event_data = {
            "id": "67890",
            "title": "Cryptocurrency Markets 2026",
            "active": True,
            "closed": False,
            "featured": True,
        }
        
        event = PolymarketEvent(**event_data)

        assert event.id == "67890"
        assert event.title == "Cryptocurrency Markets 2026"
        assert event.active is True


@pytest.mark.unit
class TestArticleModel:
    """Test Article Pydantic model."""

    def test_article_with_source(self):
        """Test creating article with source."""
        source = Source(id="source1", name="Test News")
        article_data = {
            "source": source,
            "author": "John Doe",
            "title": "Test Article",
            "description": "Article description",
            "url": "https://example.com/article",
            "urlToImage": "https://example.com/image.jpg",
            "publishedAt": "2026-01-01T00:00:00Z",
            "content": "Article content here",
        }

        article = Article(**article_data)

        assert article.source.name == "Test News"
        assert article.author == "John Doe"
        assert article.title == "Test Article"

    def test_article_all_optional(self):
        """Test that all Article fields are optional."""
        # Article fields are actually Optional, so we need to check the model definition
        # For now, create with None values explicitly
        article = Article(
            source=None,
            author=None,
            title=None,
            description=None,
            url=None,
            urlToImage=None,
            publishedAt=None,
            content=None,
        )

        assert article.source is None
        assert article.author is None
        assert article.title is None


@pytest.mark.unit
class TestSourceModel:
    """Test Source Pydantic model."""

    def test_source_creation(self):
        """Test creating a Source object."""
        source = Source(id="src123", name="News Source")

        assert source.id == "src123"
        assert source.name == "News Source"

    def test_source_all_optional(self):
        """Test that all Source fields are optional."""
        source = Source(id=None, name=None)

        assert source.id is None
        assert source.name is None
