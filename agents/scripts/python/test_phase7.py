#!/usr/bin/env python
"""
Test script for new TradingHub architecture (Phase 7)
Run this to verify the architecture switch works correctly.
"""
import os
import asyncio
import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_legacy_architecture():
    """Test legacy architecture initialization."""
    print("\n" + "="*60)
    print("TEST 1: Legacy Architecture (USE_NEW_ARCHITECTURE=false)")
    print("="*60)
    
    os.environ['USE_NEW_ARCHITECTURE'] = 'false'
    os.environ['TRADING_MODE'] = 'dry_run'
    
    from agents.application.runner import AgentRunner
    
    runner = AgentRunner(interval_minutes=60)
    
    # Verify legacy mode
    assert runner.use_new_architecture == False, "Should be using legacy architecture"
    assert runner.hub is None, "Hub should be None in legacy mode"
    assert runner.research_agent is None, "Research agent should be None"
    assert runner.trading_agent is None, "Trading agent should be None"
    
    status = runner.get_status()
    assert status['architecture'] == 'legacy', "Status should show legacy"
    assert 'hub_status' not in status, "Hub status should not be present"
    
    print("✅ Legacy architecture initialized correctly")
    print(f"   - Architecture: {status['architecture']}")
    print(f"   - Hub: {runner.hub}")
    print(f"   - Running: {status['running']}")
    
    return True


async def test_new_architecture():
    """Test new architecture initialization."""
    print("\n" + "="*60)
    print("TEST 2: New Architecture (USE_NEW_ARCHITECTURE=true)")
    print("="*60)
    
    os.environ['USE_NEW_ARCHITECTURE'] = 'true'
    os.environ['TRADING_MODE'] = 'dry_run'
    os.environ['ANTHROPIC_API_KEY'] = 'test_key_for_initialization'
    
    # Need to reload module to pick up new env var
    import importlib
    from agents.application import runner as runner_module
    importlib.reload(runner_module)
    from agents.application.runner import AgentRunner
    
    runner = AgentRunner(interval_minutes=60)
    
    # Verify new mode
    assert runner.use_new_architecture == True, "Should be using new architecture"
    assert runner.hub is not None, "Hub should be initialized"
    assert runner.research_agent is not None, "Research agent should be initialized"
    assert runner.trading_agent is not None, "Trading agent should be initialized"
    
    status = runner.get_status()
    assert status['architecture'] == 'new', "Status should show new"
    assert 'hub_status' in status, "Hub status should be present"
    
    print("✅ New architecture initialized correctly")
    print(f"   - Architecture: {status['architecture']}")
    print(f"   - Hub: {runner.hub}")
    print(f"   - Research Agent: {runner.research_agent}")
    print(f"   - Trading Agent: {runner.trading_agent}")
    print(f"   - Hub Status: {status['hub_status']['running']}")
    
    return True


async def test_hub_lifecycle():
    """Test TradingHub start/stop lifecycle."""
    print("\n" + "="*60)
    print("TEST 3: Hub Lifecycle (start/stop)")
    print("="*60)
    
    os.environ['USE_NEW_ARCHITECTURE'] = 'true'
    os.environ['ANTHROPIC_API_KEY'] = 'test_key'
    
    from agents.application.runner import AgentRunner
    
    runner = AgentRunner(interval_minutes=60)
    
    # Start runner (should start hub)
    print("   Starting runner...")
    await runner.start()
    
    assert runner.hub._running == True, "Hub should be running"
    print(f"   ✅ Hub started: {runner.hub._running}")
    
    # Check status
    status = runner.get_status()
    assert status['hub_status']['running'] == True, "Hub status should show running"
    print(f"   ✅ Hub status reports running: {status['hub_status']['running']}")
    
    # Stop runner (should stop hub)
    print("   Stopping runner...")
    await runner.stop()
    
    assert runner.hub._running == False, "Hub should be stopped"
    print(f"   ✅ Hub stopped: {runner.hub._running}")
    
    return True


async def test_trader_methods():
    """Test that Trader has both old and new methods."""
    print("\n" + "="*60)
    print("TEST 4: Trader Methods (old and new)")
    print("="*60)
    
    from agents.application.trade import Trader
    import inspect
    
    trader = Trader()
    
    # Check both methods exist
    assert hasattr(trader, 'one_best_trade'), "Should have one_best_trade"
    assert hasattr(trader, 'one_best_trade_v2'), "Should have one_best_trade_v2"
    
    # Check one_best_trade is sync
    is_sync = not inspect.iscoroutinefunction(trader.one_best_trade)
    assert is_sync, "one_best_trade should be synchronous"
    print("   ✅ one_best_trade is synchronous (legacy)")
    
    # Check one_best_trade_v2 is async
    is_async = inspect.iscoroutinefunction(trader.one_best_trade_v2)
    assert is_async, "one_best_trade_v2 should be asynchronous"
    print("   ✅ one_best_trade_v2 is asynchronous (new)")
    
    return True


async def test_new_trade_flow():
    """Test new trade flow with mocked data."""
    print("\n" + "="*60)
    print("TEST 5: New Trade Flow (one_best_trade_v2)")
    print("="*60)
    
    os.environ['USE_NEW_ARCHITECTURE'] = 'true'
    os.environ['TRADING_MODE'] = 'dry_run'
    os.environ['ANTHROPIC_API_KEY'] = 'test_key'
    
    from agents.application.trade import Trader
    from agents.core.hub import TradingHub
    from agents.core.agents import ResearchAgent, TradingAgent
    from unittest.mock import Mock
    
    # Initialize
    trader = Trader()
    hub = TradingHub()
    research_agent = ResearchAgent(hub)
    trading_agent = TradingAgent(hub)
    
    # Mock to return no events (safe test)
    trader.polymarket.get_all_tradeable_events = Mock(return_value=[])
    
    print("   Running one_best_trade_v2 with no events...")
    try:
        await trader.one_best_trade_v2(hub, research_agent, trading_agent)
        print("   ✅ one_best_trade_v2 completed without errors")
        print("   ✅ Gracefully handled empty events")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


async def test_environment_flag():
    """Test environment flag parsing."""
    print("\n" + "="*60)
    print("TEST 6: Environment Flag Parsing")
    print("="*60)
    
    from agents.application.runner import AgentRunner
    
    test_cases = [
        ('false', False, "false"),
        ('true', True, "true"),
        ('FALSE', False, "FALSE"),
        ('TRUE', True, "TRUE"),
        ('', False, "empty string"),
        ('0', False, "0"),
        ('1', False, "1 (not 'true')"),
    ]
    
    for value, expected, description in test_cases:
        os.environ['USE_NEW_ARCHITECTURE'] = value
        os.environ['ANTHROPIC_API_KEY'] = 'test_key'
        
        # Need fresh import
        import importlib
        from agents.application import runner as runner_module
        importlib.reload(runner_module)
        from agents.application.runner import AgentRunner
        
        runner = AgentRunner()
        result = runner.use_new_architecture
        
        if result == expected:
            print(f"   ✅ '{description}' -> {result} (correct)")
        else:
            print(f"   ❌ '{description}' -> {result}, expected {expected}")
            return False
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "🧪 " * 20)
    print("   PHASE 7 ARCHITECTURE INTEGRATION TESTS")
    print("🧪 " * 20)
    
    tests = [
        ("Legacy Architecture", test_legacy_architecture),
        ("New Architecture", test_new_architecture),
        ("Hub Lifecycle", test_hub_lifecycle),
        ("Trader Methods", test_trader_methods),
        ("New Trade Flow", test_new_trade_flow),
        ("Environment Flag", test_environment_flag),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result, None))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False, str(e)))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if error:
            print(f"       Error: {error}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 7 integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
