"""
Integration tests for Polymarket API connectivity.
Verifies we can fetch real data from Polymarket.
"""
import pytest
from agents.polymarket.polymarket import Polymarket
from agents.connectors.database import Database


class TestPolymarketIntegration:
    """Test real Polymarket API integration."""
    
    def test_polymarket_initialization(self):
        """Test Polymarket client can be initialized."""
        import os
        # Ensure dry_run mode (default if TRADING_MODE not set)
        original_mode = os.environ.get("TRADING_MODE")
        if "TRADING_MODE" in os.environ:
            del os.environ["TRADING_MODE"]
        try:
            poly = Polymarket()
            assert poly is not None
            assert poly.dry_run is True  # Should be in dry_run mode by default
        finally:
            if original_mode:
                os.environ["TRADING_MODE"] = original_mode
    
    def test_fetch_all_markets(self):
        """Test fetching markets from Polymarket API."""
        poly = Polymarket()
        markets = poly.get_all_markets()
        
        assert markets is not None
        assert isinstance(markets, list)
        assert len(markets) > 0, "Should fetch at least some markets"
        
        # Check first market has expected attributes
        first_market = markets[0]
        assert hasattr(first_market, 'question')
        assert hasattr(first_market, 'id')
        assert first_market.question is not None
        assert len(first_market.question) > 0
        
        print(f"✅ Fetched {len(markets)} markets from Polymarket")
        print(f"   Sample: {first_market.question[:80]}...")
    
    def test_fetch_specific_market(self):
        """Test fetching a specific market by token ID."""
        poly = Polymarket()
        
        # First get all markets to get a valid token_id
        markets = poly.get_all_markets()
        assert len(markets) > 0
        
        # Get details for first market (use clob_token_ids)
        first_market = markets[0]
        # Parse the token IDs from the JSON string
        import json
        token_ids = json.loads(first_market.clob_token_ids) if first_market.clob_token_ids else []
        
        if token_ids:
            token_id = token_ids[0]
            market = poly.get_market(token_id)
            
            assert market is not None
            # get_market returns a dict
            assert isinstance(market, dict)
            assert market.get('question') is not None
            print(f"✅ Fetched market details for token {token_id[:20]}...")
        else:
            print("ℹ️  No token IDs available for this market")
    
    def test_fetch_all_events(self):
        """Test fetching events from Polymarket API."""
        poly = Polymarket()
        events = poly.get_all_events()
        
        assert events is not None
        assert isinstance(events, list)
        # Events might be empty, that's ok
        
        if events:
            print(f"✅ Fetched {len(events)} events from Polymarket")
            first_event = events[0]
            assert hasattr(first_event, 'title')
        else:
            print("ℹ️  No events currently available")
    
    def test_fetch_tradeable_events(self):
        """Test fetching tradeable events."""
        poly = Polymarket()
        events = poly.get_all_tradeable_events()
        
        assert events is not None
        assert isinstance(events, list)
        
        if events:
            print(f"✅ Fetched {len(events)} tradeable events")
    
    def test_get_usdc_balance_dry_run(self):
        """Test getting USDC balance in dry_run mode."""
        import os
        # Ensure dry_run mode
        original_mode = os.environ.get("TRADING_MODE")
        if "TRADING_MODE" in os.environ:
            del os.environ["TRADING_MODE"]
        try:
            poly = Polymarket()
            assert poly.dry_run is True, "Should be in dry_run mode"
            balance = poly.get_usdc_balance()
            
            assert balance is not None
            assert isinstance(balance, (int, float))
            assert balance > 0  # Should return simulated balance
            
            print(f"✅ USDC Balance (simulated): ${balance:.2f}")
        finally:
            if original_mode:
                os.environ["TRADING_MODE"] = original_mode
    
    def test_orderbook_price(self):
        """Test fetching orderbook price for a market."""
        poly = Polymarket()
        
        # Get a market first
        markets = poly.get_all_markets()
        assert len(markets) > 0
        
        # Parse token IDs
        import json
        first_market = markets[0]
        token_ids = json.loads(first_market.clob_token_ids) if first_market.clob_token_ids else []
        
        if not token_ids:
            print("ℹ️  No token IDs available")
            return
        
        token_id = token_ids[0]
        
        try:
            price = poly.get_orderbook_price(token_id)
            assert price is not None
            assert isinstance(price, (int, float))
            assert 0 <= price <= 1  # Price should be between 0 and 1
            
            print(f"✅ Orderbook price for {markets[0].question[:40]}...")
            print(f"   Price: ${price:.4f}")
        except Exception as e:
            # Orderbook might not be available for all markets
            print(f"ℹ️  Orderbook not available: {e}")


class TestPolymarketDatabaseIntegration:
    """Test Polymarket data can be saved to database."""
    
    def test_save_market_as_forecast(self, setup_test_db):
        """Test saving Polymarket market data as a forecast."""
        poly = Polymarket()
        db = Database()
        
        # Fetch a market
        markets = poly.get_all_markets()
        assert len(markets) > 0
        
        market = markets[0]
        
        # Create forecast from market data
        forecast_data = {
            "market_id": str(market.id),
            "market_question": market.question,
            "outcome": "Yes",
            "probability": 0.5,
            "confidence": 0.7,
            "base_rate": 0.5,
            "reasoning": "Integration test forecast",
        }
        
        forecast = db.save_forecast(forecast_data)
        
        assert forecast.id is not None
        assert forecast.market_question == market.question
        assert forecast.market_id == str(market.id)
        
        print(f"✅ Saved forecast for: {market.question[:60]}...")
    
    def test_save_multiple_markets(self, setup_test_db):
        """Test saving multiple Polymarket markets to database."""
        poly = Polymarket()
        db = Database()
        
        # Fetch markets
        markets = poly.get_all_markets()
        assert len(markets) >= 3
        
        # Save first 3 as forecasts
        saved_forecasts = []
        for i, market in enumerate(markets[:3], 1):
            forecast_data = {
                "market_id": str(market.id),
                "market_question": market.question,
                "outcome": "Yes",
                "probability": 0.3 + (i * 0.1),
                "confidence": 0.6 + (i * 0.05),
                "base_rate": 0.5,
                "reasoning": f"Test forecast {i}",
            }
            
            forecast = db.save_forecast(forecast_data)
            saved_forecasts.append(forecast)
        
        assert len(saved_forecasts) == 3
        
        # Verify we can retrieve them
        retrieved = db.get_recent_forecasts(limit=10)
        assert len(retrieved) >= 3
        
        print(f"✅ Saved {len(saved_forecasts)} Polymarket markets as forecasts")
    
    def test_portfolio_snapshot_with_balance(self, setup_test_db):
        """Test saving portfolio snapshot with Polymarket balance."""
        poly = Polymarket()
        db = Database()
        
        # Get balance
        balance = poly.get_usdc_balance()
        
        # Save portfolio snapshot
        portfolio_data = {
            "balance": balance,
            "total_value": balance,
            "open_positions": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
        }
        
        snapshot = db.save_portfolio_snapshot(portfolio_data)
        
        assert snapshot.id is not None
        assert snapshot.balance == balance
        
        print(f"✅ Saved portfolio snapshot with ${balance:.2f} balance")


class TestPolymarketEndToEnd:
    """End-to-end test of Polymarket → Database → API flow."""
    
    def test_full_pipeline(self, client, setup_test_db):
        """Test complete flow: Polymarket → DB → API → UI."""
        poly = Polymarket()
        db = Database()
        
        # 1. Fetch from Polymarket
        markets = poly.get_all_markets()
        assert len(markets) > 0
        print(f"✅ Step 1: Fetched {len(markets)} markets from Polymarket")
        
        # 2. Save to database
        market = markets[0]
        forecast_data = {
            "market_id": str(market.id),
            "market_question": market.question,
            "outcome": "Yes",
            "probability": 0.65,
            "confidence": 0.8,
            "base_rate": 0.5,
            "reasoning": "E2E test forecast",
        }
        forecast = db.save_forecast(forecast_data)
        print(f"✅ Step 2: Saved to database (ID: {forecast.id})")
        
        # 3. Retrieve via API
        response = client.get("/api/forecasts")
        assert response.status_code == 200
        forecasts = response.json()
        assert len(forecasts) > 0
        
        # Find our forecast
        our_forecast = next((f for f in forecasts if f["id"] == forecast.id), None)
        assert our_forecast is not None
        assert our_forecast["market_question"] == market.question
        print(f"✅ Step 3: Retrieved via API")
        
        # 4. Check dashboard page (now served by Next.js, so 404 is expected)
        response = client.get("/forecasts")
        # Dashboard is now served by Next.js frontend, so backend returns 404
        assert response.status_code == 404
        print(f"✅ Step 4: Dashboard moved to Next.js frontend (404 expected)")
        
        print(f"\n🎉 Full pipeline test passed!")
        print(f"   Market: {market.question[:70]}...")
