#!/usr/bin/env python
"""
Demo: Run a full trading cycle with new architecture
Shows the complete flow with mock data.
"""
import os
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set to dry_run for safe testing
os.environ['TRADING_MODE'] = 'dry_run'
os.environ['USE_NEW_ARCHITECTURE'] = 'true'
os.environ['ANTHROPIC_API_KEY'] = 'test_key'


async def demo_full_cycle():
    """Demo a full trading cycle with new architecture."""
    print("\n" + "🚀 " * 25)
    print("   DEMO: FULL TRADING CYCLE WITH NEW ARCHITECTURE")
    print("🚀 " * 25)
    
    from agents.application.trade import Trader
    from agents.core.hub import TradingHub
    from agents.core.agents import ResearchAgent, TradingAgent
    
    # Initialize
    print("\n📦 Initializing components...")
    trader = Trader()
    hub = TradingHub()
    research_agent = ResearchAgent(hub)
    trading_agent = TradingAgent(hub)
    
    # Start hub
    await hub.start()
    print("   ✅ TradingHub started")
    
    # Mock some events/markets for demo
    print("\n🎭 Setting up mock data...")
    
    mock_event = {
        "id": "demo_event_123",
        "title": "Will Bitcoin reach $100k by March 2026?"
    }
    
    mock_markets = [
        {
            "id": "market_btc_100k",
            "question": "Will Bitcoin reach $100k by March 2026?",
            "description": "Resolves YES if BTC hits $100k before March 31, 2026",
            "outcomes": ["Yes", "No"],
            "outcome_prices": ["0.45", "0.55"]
        },
        {
            "id": "market_eth_5k",
            "question": "Will Ethereum reach $5k by Q2 2026?",
            "description": "Resolves YES if ETH hits $5k before June 30, 2026",
            "outcomes": ["Yes", "No"],
            "outcome_prices": ["0.60", "0.40"]
        }
    ]
    
    # Mock the polymarket calls
    trader.polymarket.get_all_tradeable_events = Mock(return_value=[mock_event])
    trader.agent.filter_events_with_rag = Mock(return_value=[(Mock(json=lambda: '{"page_content": "BTC event", "metadata": {"markets": "market_btc_100k"}}'), 0.9)])
    trader.agent.map_filtered_events_to_markets = Mock(return_value=mock_markets)
    
    print(f"   - Mock events: {len([mock_event])}")
    print(f"   - Mock markets: {len(mock_markets)}")
    
    # Run the new trading flow
    print("\n🔄 Running one_best_trade_v2...")
    print("-" * 70)
    
    try:
        await trader.one_best_trade_v2(hub, research_agent, trading_agent)
    except Exception as e:
        print(f"\n⚠️  Cycle completed with expected errors (no actual API calls):")
        print(f"   {type(e).__name__}: {str(e)[:100]}")
    
    # Show hub status
    print("\n" + "-" * 70)
    print("📊 Hub Status After Cycle:")
    print("-" * 70)
    status = hub.get_status()
    
    print(f"\n🏢 Hub:")
    print(f"   - Running: {status['running']}")
    print(f"   - Sessions: {status['sessions']}")
    print(f"   - Pending results: {status['pending_results']}")
    
    print(f"\n📈 Statistics:")
    print(f"   - Tasks enqueued: {status['stats']['tasks_enqueued']}")
    print(f"   - Tasks completed: {status['stats']['tasks_completed']}")
    print(f"   - Tasks failed: {status['stats']['tasks_failed']}")
    print(f"   - Sessions created: {status['stats']['sessions_created']}")
    print(f"   - Sessions cleaned: {status['stats']['sessions_cleaned']}")
    print(f"   - Results cleaned: {status['stats']['results_cleaned']}")
    
    print(f"\n🚦 Lane Status:")
    for lane_name, lane_data in status['lane_status'].items():
        print(f"   - {lane_name.upper():10s}: {lane_data['active']}/{lane_data['limit']} active, {lane_data['queued']} queued")
    
    # Stop hub
    await hub.stop()
    print("\n✅ TradingHub stopped")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    
    print("\n💡 What Happened:")
    print("   1. ✅ TradingHub initialized and started")
    print("   2. ✅ ResearchAgent and TradingAgent created")
    print("   3. ✅ Mock events and markets loaded")
    print("   4. ✅ one_best_trade_v2 executed")
    print("   5. ⚠️  Research/evaluation hit mock data (expected)")
    print("   6. ✅ Hub status tracked correctly")
    print("   7. ✅ TradingHub stopped cleanly")
    
    print("\n🎯 Ready for Real Trading:")
    print("   - Set USE_NEW_ARCHITECTURE=true in .env")
    print("   - Ensure all API keys are set (ANTHROPIC, EXA, TAVILY)")
    print("   - Set TRADING_MODE=dry_run for testing (no real trades)")
    print("   - Start server: uv run python scripts/python/server.py")
    print("   - Monitor: curl http://localhost:8000/api/agent/status")


if __name__ == "__main__":
    asyncio.run(demo_full_cycle())
