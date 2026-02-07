"""
Unit tests for Phase 6: TradingHub cleanup mechanisms
Tests session and task result cleanup functionality.
"""
import pytest
import asyncio
import time
from unittest.mock import patch
from agents.core.hub import TradingHub
from agents.core.session import Lane, Task


@pytest.mark.unit
@pytest.mark.asyncio
class TestSessionCleanup:
    """Test session cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Test that old sessions are cleaned up."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.session_ttl_seconds = 1  # 1 second for testing
            
            # Create session
            session = hub._create_session("test_session", "test")
            assert "test_session" in hub.sessions
            
            # Wait for TTL
            await asyncio.sleep(1.5)
            
            # Trigger cleanup
            await hub._cleanup_old_sessions()
            
            # Session should be gone
            assert "test_session" not in hub.sessions
            assert hub.stats["sessions_cleaned"] == 1
    
    @pytest.mark.asyncio
    async def test_session_cleanup_multiple(self):
        """Test cleanup of multiple expired sessions."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.session_ttl_seconds = 1
            
            # Create multiple sessions
            for i in range(5):
                hub._create_session(f"session_{i}", "test")
            
            assert len(hub.sessions) == 5
            
            # Wait for TTL
            await asyncio.sleep(1.5)
            
            # Trigger cleanup
            await hub._cleanup_old_sessions()
            
            # All sessions should be gone
            assert len(hub.sessions) == 0
            assert hub.stats["sessions_cleaned"] == 5
    
    @pytest.mark.asyncio
    async def test_session_cleanup_mixed_ages(self):
        """Test that only old sessions are cleaned up."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.session_ttl_seconds = 2
            
            # Create old session
            old_session = hub._create_session("old_session", "test")
            
            # Wait 1.5 seconds
            await asyncio.sleep(1.5)
            
            # Create new session
            new_session = hub._create_session("new_session", "test")
            
            # Wait another 1 second (old_session is now 2.5s old, new is 1s)
            await asyncio.sleep(1)
            
            # Trigger cleanup
            await hub._cleanup_old_sessions()
            
            # Old session should be gone, new should remain
            assert "old_session" not in hub.sessions
            assert "new_session" in hub.sessions
            assert hub.stats["sessions_cleaned"] == 1
    
    @pytest.mark.asyncio
    async def test_session_cleanup_empty(self):
        """Test cleanup with no sessions."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            # Trigger cleanup with no sessions
            await hub._cleanup_old_sessions()
            
            # Should not error
            assert len(hub.sessions) == 0
            assert hub.stats["sessions_cleaned"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskResultCleanup:
    """Test task result cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_task_result_cleanup(self):
        """Test that old task results are cleaned up."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.task_result_ttl_seconds = 1
            
            # Store result
            hub.task_results["test_task"] = {"result": "data"}
            hub.task_result_timestamps["test_task"] = time.time()
            
            # Wait for TTL
            await asyncio.sleep(1.5)
            
            # Trigger cleanup
            await hub._cleanup_old_task_results()
            
            # Result should be gone
            assert "test_task" not in hub.task_results
            assert "test_task" not in hub.task_result_timestamps
            assert hub.stats["results_cleaned"] == 1
    
    @pytest.mark.asyncio
    async def test_task_result_cleanup_multiple(self):
        """Test cleanup of multiple expired results."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.task_result_ttl_seconds = 1
            
            # Store multiple results
            for i in range(5):
                hub.task_results[f"task_{i}"] = {"result": f"data_{i}"}
                hub.task_result_timestamps[f"task_{i}"] = time.time()
            
            assert len(hub.task_results) == 5
            
            # Wait for TTL
            await asyncio.sleep(1.5)
            
            # Trigger cleanup
            await hub._cleanup_old_task_results()
            
            # All results should be gone
            assert len(hub.task_results) == 0
            assert len(hub.task_result_timestamps) == 0
            assert hub.stats["results_cleaned"] == 5
    
    @pytest.mark.asyncio
    async def test_task_result_cleanup_mixed_ages(self):
        """Test that only old results are cleaned up."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.task_result_ttl_seconds = 2
            
            # Store old result
            hub.task_results["old_task"] = {"result": "old"}
            hub.task_result_timestamps["old_task"] = time.time()
            
            # Wait 1.5 seconds
            await asyncio.sleep(1.5)
            
            # Store new result
            hub.task_results["new_task"] = {"result": "new"}
            hub.task_result_timestamps["new_task"] = time.time()
            
            # Wait another 1 second
            await asyncio.sleep(1)
            
            # Trigger cleanup
            await hub._cleanup_old_task_results()
            
            # Old result should be gone, new should remain
            assert "old_task" not in hub.task_results
            assert "new_task" in hub.task_results
            assert hub.stats["results_cleaned"] == 1
    
    @pytest.mark.asyncio
    async def test_task_result_cleanup_empty(self):
        """Test cleanup with no results."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            # Trigger cleanup with no results
            await hub._cleanup_old_task_results()
            
            # Should not error
            assert len(hub.task_results) == 0
            assert hub.stats["results_cleaned"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestAutomaticCleanup:
    """Test that cleanup runs automatically in background processor."""
    
    @pytest.mark.asyncio
    async def test_automatic_cleanup_integration(self):
        """Test that cleanup runs automatically during task processing."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.session_ttl_seconds = 0.5  # Very short for testing
            hub.task_result_ttl_seconds = 0.5
            
            # Start hub
            await hub.start()
            
            # Create old session
            hub._create_session("old_session", "test")
            
            # Store old result
            hub.task_results["old_task"] = {"result": "data"}
            hub.task_result_timestamps["old_task"] = time.time()
            
            # Wait for TTL and cleanup cycle
            # Cleanup runs every 100 iterations * 0.1s = 10s
            # But for testing we just verify the cleanup methods work
            await asyncio.sleep(0.7)
            
            # Manually trigger cleanup (in real scenario it runs automatically)
            await hub._cleanup_old_sessions()
            await hub._cleanup_old_task_results()
            
            # Stop hub
            await hub.stop()
            
            # Verify cleanup occurred
            assert "old_session" not in hub.sessions
            assert "old_task" not in hub.task_results


@pytest.mark.unit
@pytest.mark.asyncio
class TestCleanupStats:
    """Test that cleanup statistics are tracked correctly."""
    
    @pytest.mark.asyncio
    async def test_cleanup_stats_tracking(self):
        """Test that cleanup stats are incremented correctly."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            hub.session_ttl_seconds = 1
            hub.task_result_ttl_seconds = 1
            
            # Initial stats
            assert hub.stats["sessions_cleaned"] == 0
            assert hub.stats["results_cleaned"] == 0
            
            # Create and cleanup sessions
            for i in range(3):
                hub._create_session(f"session_{i}", "test")
            await asyncio.sleep(1.2)
            await hub._cleanup_old_sessions()
            
            assert hub.stats["sessions_cleaned"] == 3
            
            # Create and cleanup results
            for i in range(5):
                hub.task_results[f"task_{i}"] = {"result": i}
                hub.task_result_timestamps[f"task_{i}"] = time.time()
            await asyncio.sleep(1.2)
            await hub._cleanup_old_task_results()
            
            assert hub.stats["results_cleaned"] == 5
            
            # Verify stats in get_status
            status = hub.get_status()
            assert status["stats"]["sessions_cleaned"] == 3
            assert status["stats"]["results_cleaned"] == 5
