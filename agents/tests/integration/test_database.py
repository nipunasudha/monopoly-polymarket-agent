"""
Integration tests for database persistence layer.
"""
import pytest
import json
from datetime import datetime
from agents.connectors.database import (
    Database,
    ForecastRecord,
    TradeRecord,
    PortfolioSnapshot,
)


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    db = Database("sqlite:///:memory:")
    db.create_tables()
    yield db
    # Cleanup happens automatically with in-memory database


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing."""
    return {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "probability": 0.35,
        "confidence": 0.70,
        "base_rate": 0.30,
        "reasoning": "Based on historical trends and current market conditions...",
        "evidence_for": json.dumps(["Institutional adoption", "ETF approvals"]),
        "evidence_against": json.dumps(["Regulatory uncertainty", "Market volatility"]),
        "key_factors": json.dumps(["Bitcoin price history", "Adoption trends"]),
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "side": "BUY",
        "size": 250.0,
        "price": 0.45,
        "forecast_probability": 0.60,
        "edge": 0.15,
        "status": "pending",
        "execution_enabled": False,
    }


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "balance": 1000.0,
        "total_value": 1250.0,
        "open_positions": 3,
        "total_pnl": 250.0,
        "win_rate": 0.65,
        "total_trades": 10,
        "extra_data": json.dumps({"last_updated": "2026-02-07"}),
    }


@pytest.mark.integration
class TestDatabaseInitialization:
    """Test database initialization and table creation."""

    def test_database_creates_tables(self, test_db):
        """Test that database creates all required tables."""
        # Tables should be created by fixture
        with test_db.get_session() as session:
            # Query should not raise an error
            result = session.query(ForecastRecord).count()
            assert result == 0

    def test_database_session_context_manager(self, test_db):
        """Test that session context manager works correctly."""
        with test_db.get_session() as session:
            assert session is not None
            # Session should be active
            assert session.is_active

    def test_database_rollback_on_error(self, test_db):
        """Test that database rolls back on error."""
        try:
            with test_db.get_session() as session:
                forecast = ForecastRecord(
                    market_id="test",
                    market_question="Test?",
                    outcome="Yes",
                    probability=0.5,
                    confidence=0.7,
                )
                session.add(forecast)
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify nothing was committed
        with test_db.get_session() as session:
            count = session.query(ForecastRecord).count()
            assert count == 0


@pytest.mark.integration
class TestForecastOperations:
    """Test forecast CRUD operations."""

    def test_save_forecast(self, test_db, sample_forecast_data):
        """Test saving a forecast to database."""
        forecast = test_db.save_forecast(sample_forecast_data)

        assert forecast.id is not None
        assert forecast.market_id == "12345"
        assert forecast.probability == 0.35
        assert forecast.confidence == 0.70
        assert forecast.created_at is not None

    def test_get_forecast_by_id(self, test_db, sample_forecast_data):
        """Test retrieving a forecast by ID."""
        saved = test_db.save_forecast(sample_forecast_data)

        retrieved = test_db.get_forecast(saved.id)

        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.market_question == sample_forecast_data["market_question"]

    def test_get_forecast_nonexistent(self, test_db):
        """Test retrieving a non-existent forecast returns None."""
        result = test_db.get_forecast(99999)
        assert result is None

    def test_get_forecasts_by_market(self, test_db, sample_forecast_data):
        """Test retrieving all forecasts for a market."""
        # Save multiple forecasts for same market
        test_db.save_forecast(sample_forecast_data)
        test_db.save_forecast({**sample_forecast_data, "outcome": "No", "probability": 0.65})

        forecasts = test_db.get_forecasts_by_market("12345")

        assert len(forecasts) == 2
        assert all(f.market_id == "12345" for f in forecasts)

    def test_get_recent_forecasts(self, test_db, sample_forecast_data):
        """Test retrieving recent forecasts."""
        # Save multiple forecasts
        for i in range(5):
            test_db.save_forecast({
                **sample_forecast_data,
                "market_id": f"market_{i}",
            })

        recent = test_db.get_recent_forecasts(limit=3)

        assert len(recent) == 3
        # Should be ordered by created_at desc (most recent first)
        assert recent[0].created_at >= recent[1].created_at
        assert recent[1].created_at >= recent[2].created_at

    def test_forecast_to_dict(self, test_db, sample_forecast_data):
        """Test converting forecast to dictionary."""
        forecast = test_db.save_forecast(sample_forecast_data)

        forecast_dict = forecast.to_dict()

        assert isinstance(forecast_dict, dict)
        assert forecast_dict["id"] == forecast.id
        assert forecast_dict["market_id"] == "12345"
        assert forecast_dict["probability"] == 0.35
        assert "created_at" in forecast_dict


@pytest.mark.integration
class TestTradeOperations:
    """Test trade CRUD operations."""

    def test_save_trade(self, test_db, sample_trade_data):
        """Test saving a trade to database."""
        trade = test_db.save_trade(sample_trade_data)

        assert trade.id is not None
        assert trade.market_id == "12345"
        assert trade.side == "BUY"
        assert trade.size == 250.0
        assert trade.status == "pending"
        assert trade.created_at is not None

    def test_get_trade_by_id(self, test_db, sample_trade_data):
        """Test retrieving a trade by ID."""
        saved = test_db.save_trade(sample_trade_data)

        retrieved = test_db.get_trade(saved.id)

        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.market_question == sample_trade_data["market_question"]

    def test_get_trades_by_market(self, test_db, sample_trade_data):
        """Test retrieving all trades for a market."""
        # Save multiple trades for same market
        test_db.save_trade(sample_trade_data)
        test_db.save_trade({**sample_trade_data, "side": "SELL", "size": 150.0})

        trades = test_db.get_trades_by_market("12345")

        assert len(trades) == 2
        assert all(t.market_id == "12345" for t in trades)

    def test_get_recent_trades(self, test_db, sample_trade_data):
        """Test retrieving recent trades."""
        # Save multiple trades
        for i in range(5):
            test_db.save_trade({
                **sample_trade_data,
                "market_id": f"market_{i}",
            })

        recent = test_db.get_recent_trades(limit=3)

        assert len(recent) == 3
        # Should be ordered by created_at desc
        assert recent[0].created_at >= recent[1].created_at

    def test_update_trade_status(self, test_db, sample_trade_data):
        """Test updating trade status."""
        trade = test_db.save_trade(sample_trade_data)
        assert trade.status == "pending"

        executed_at = datetime.utcnow()
        updated = test_db.update_trade_status(
            trade.id,
            status="executed",
            executed_at=executed_at,
            transaction_hash="0xabc123",
        )

        assert updated.status == "executed"
        assert updated.executed_at is not None
        assert updated.transaction_hash == "0xabc123"

    def test_update_trade_status_with_error(self, test_db, sample_trade_data):
        """Test updating trade status with error message."""
        trade = test_db.save_trade(sample_trade_data)

        updated = test_db.update_trade_status(
            trade.id,
            status="failed",
            error_message="Insufficient balance",
        )

        assert updated.status == "failed"
        assert updated.error_message == "Insufficient balance"

    def test_trade_to_dict(self, test_db, sample_trade_data):
        """Test converting trade to dictionary."""
        trade = test_db.save_trade(sample_trade_data)

        trade_dict = trade.to_dict()

        assert isinstance(trade_dict, dict)
        assert trade_dict["id"] == trade.id
        assert trade_dict["market_id"] == "12345"
        assert trade_dict["side"] == "BUY"
        assert "created_at" in trade_dict


@pytest.mark.integration
class TestPortfolioOperations:
    """Test portfolio snapshot operations."""

    def test_save_portfolio_snapshot(self, test_db, sample_portfolio_data):
        """Test saving a portfolio snapshot."""
        snapshot = test_db.save_portfolio_snapshot(sample_portfolio_data)

        assert snapshot.id is not None
        assert snapshot.balance == 1000.0
        assert snapshot.total_value == 1250.0
        assert snapshot.total_pnl == 250.0
        assert snapshot.win_rate == 0.65
        assert snapshot.created_at is not None

    def test_get_latest_portfolio_snapshot(self, test_db, sample_portfolio_data):
        """Test retrieving the latest portfolio snapshot."""
        # Save multiple snapshots
        test_db.save_portfolio_snapshot(sample_portfolio_data)
        test_db.save_portfolio_snapshot({
            **sample_portfolio_data,
            "balance": 1100.0,
            "total_value": 1350.0,
        })

        latest = test_db.get_latest_portfolio_snapshot()

        assert latest is not None
        assert latest.balance == 1100.0  # Should be the most recent

    def test_get_portfolio_history(self, test_db, sample_portfolio_data):
        """Test retrieving portfolio history."""
        # Save multiple snapshots
        for i in range(5):
            test_db.save_portfolio_snapshot({
                **sample_portfolio_data,
                "balance": 1000.0 + (i * 100),
            })

        history = test_db.get_portfolio_history(limit=3)

        assert len(history) == 3
        # Should be ordered by created_at desc
        assert history[0].created_at >= history[1].created_at

    def test_portfolio_snapshot_to_dict(self, test_db, sample_portfolio_data):
        """Test converting portfolio snapshot to dictionary."""
        snapshot = test_db.save_portfolio_snapshot(sample_portfolio_data)

        snapshot_dict = snapshot.to_dict()

        assert isinstance(snapshot_dict, dict)
        assert snapshot_dict["id"] == snapshot.id
        assert snapshot_dict["balance"] == 1000.0
        assert snapshot_dict["total_pnl"] == 250.0
        assert "created_at" in snapshot_dict


@pytest.mark.integration
class TestDatabaseMigration:
    """Test database migration and idempotency."""

    def test_create_tables_idempotent(self, test_db):
        """Test that creating tables multiple times is safe."""
        # Create tables again (already created by fixture)
        test_db.create_tables()
        test_db.create_tables()

        # Should not raise an error
        with test_db.get_session() as session:
            count = session.query(ForecastRecord).count()
            assert count == 0

    def test_drop_and_recreate_tables(self, test_db, sample_forecast_data):
        """Test dropping and recreating tables."""
        # Save some data
        test_db.save_forecast(sample_forecast_data)

        # Drop tables
        test_db.drop_tables()

        # Recreate tables
        test_db.create_tables()

        # Data should be gone
        with test_db.get_session() as session:
            count = session.query(ForecastRecord).count()
            assert count == 0


@pytest.mark.integration
class TestDatabaseEdgeCases:
    """Test edge cases and error handling."""

    def test_save_forecast_with_minimal_data(self, test_db):
        """Test saving forecast with only required fields."""
        minimal_data = {
            "market_id": "test",
            "market_question": "Test?",
            "outcome": "Yes",
            "probability": 0.5,
            "confidence": 0.7,
        }

        forecast = test_db.save_forecast(minimal_data)

        assert forecast.id is not None
        assert forecast.base_rate is None
        assert forecast.reasoning is None

    def test_save_trade_with_minimal_data(self, test_db):
        """Test saving trade with only required fields."""
        minimal_data = {
            "market_id": "test",
            "market_question": "Test?",
            "outcome": "Yes",
            "side": "BUY",
            "size": 100.0,
            "forecast_probability": 0.6,
        }

        trade = test_db.save_trade(minimal_data)

        assert trade.id is not None
        assert trade.price is None
        assert trade.edge is None

    def test_update_nonexistent_trade(self, test_db):
        """Test updating a non-existent trade returns None."""
        result = test_db.update_trade_status(99999, "executed")
        assert result is None

    def test_get_recent_with_empty_database(self, test_db):
        """Test getting recent records from empty database."""
        forecasts = test_db.get_recent_forecasts()
        trades = test_db.get_recent_trades()
        snapshots = test_db.get_portfolio_history()

        assert forecasts == []
        assert trades == []
        assert snapshots == []
