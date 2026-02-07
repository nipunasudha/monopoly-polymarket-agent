"""
Unit tests for Phase 2: TradingHub and Session management
Tests lane-based queuing, concurrency limits, and task execution.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.core.hub import TradingHub
from agents.core.session import Lane, Session, Task


@pytest.mark.unit
class TestLane:
    """Test Lane enum."""
    
    def test_lane_values(self):
        """Test that lanes have correct values."""
        assert Lane.MAIN.value == "main"
        assert Lane.RESEARCH.value == "research"
        assert Lane.MONITOR.value == "monitor"
        assert Lane.CRON.value == "cron"


@pytest.mark.unit
class TestSession:
    """Test Session dataclass."""
    
    def test_session_creation(self):
        """Test creating a session."""
        session = Session(id="test_123", agent_type="research")
        assert session.id == "test_123"
        assert session.agent_type == "research"
        assert len(session.messages) == 0
        assert isinstance(session.state, dict)
    
    def test_session_add_message(self):
        """Test adding messages to session."""
        session = Session(id="test_123", agent_type="research")
        session.add_message("user", "Hello")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"
    
    def test_session_get_messages_for_claude(self):
        """Test getting messages in Claude format."""
        session = Session(id="test_123", agent_type="research")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")
        
        messages = session.get_messages_for_claude()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


@pytest.mark.unit
class TestTask:
    """Test Task dataclass."""
    
    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            id="task_123",
            lane=Lane.RESEARCH,
            prompt="Test prompt",
            tools=["tool1", "tool2"]
        )
        assert task.id == "task_123"
        assert task.lane == Lane.RESEARCH
        assert task.prompt == "Test prompt"
        assert len(task.tools) == 2
        assert task.priority == 0
    
    def test_task_priority_comparison(self):
        """Test task priority comparison."""
        task1 = Task(id="t1", lane=Lane.MAIN, prompt="p1", priority=5)
        task2 = Task(id="t2", lane=Lane.MAIN, prompt="p2", priority=10)
        
        # Higher priority should be "less than" (for max heap)
        # task2 has higher priority (10), so task2 < task1 should be True
        assert task2 < task1  # task2 has higher priority, so it's "less than" task1
        assert not (task1 < task2)  # task1 has lower priority


@pytest.mark.unit
@pytest.mark.asyncio
class TestTradingHub:
    """Test TradingHub functionality."""
    
    @pytest.mark.asyncio
    async def test_hub_initialization(self):
        """Test TradingHub initialization."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            assert hub is not None
            assert hub.model == "claude-sonnet-4-20250514"
            assert len(hub.lanes) == len(Lane)
            assert len(hub.active_tasks) == len(Lane)
            assert hub.tool_registry is not None
    
    @pytest.mark.asyncio
    async def test_hub_lane_limits(self):
        """Test that lane limits are set correctly."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            assert hub.LANE_LIMITS[Lane.MAIN] == 1
            assert hub.LANE_LIMITS[Lane.RESEARCH] == 3
            assert hub.LANE_LIMITS[Lane.MONITOR] == 2
            assert hub.LANE_LIMITS[Lane.CRON] == 1
    
    @pytest.mark.asyncio
    async def test_enqueue_task(self):
        """Test enqueueing a task."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            task = Task(
                id="test_task",
                lane=Lane.RESEARCH,
                prompt="Test prompt"
            )
            
            task_id = await hub.enqueue(task)
            assert task_id == "test_task"
            
            status = hub.get_status()
            assert status['lane_status']['research']['queued'] == 1
    
    @pytest.mark.asyncio
    async def test_enqueue_with_session(self):
        """Test enqueueing a task with session."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            task = Task(
                id="test_task",
                lane=Lane.MAIN,
                prompt="Test",
                session_id="session_123"
            )
            
            await hub.enqueue(task)
            
            session = hub.get_session("session_123")
            assert session is not None
            assert session.id == "session_123"
    
    @pytest.mark.asyncio
    async def test_task_priority_ordering(self):
        """Test that tasks are ordered by priority."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            # Enqueue tasks with different priorities
            task1 = Task(id="t1", lane=Lane.RESEARCH, prompt="p1", priority=1)
            task2 = Task(id="t2", lane=Lane.RESEARCH, prompt="p2", priority=5)
            task3 = Task(id="t3", lane=Lane.RESEARCH, prompt="p3", priority=3)
            
            await hub.enqueue(task1)
            await hub.enqueue(task2)
            await hub.enqueue(task3)
            
            # Check order (higher priority first)
            lane_queue = hub.lanes[Lane.RESEARCH]
            assert lane_queue[0].priority == 5  # Highest priority first
            assert lane_queue[1].priority == 3
            assert lane_queue[2].priority == 1
    
    @pytest.mark.asyncio
    async def test_hub_status(self):
        """Test hub status reporting."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            status = hub.get_status()
            assert 'running' in status
            assert 'sessions' in status
            assert 'lane_status' in status
            assert 'stats' in status
            
            # Check lane status structure
            for lane in Lane:
                lane_status = status['lane_status'][lane.value]
                assert 'queued' in lane_status
                assert 'active' in lane_status
                assert 'limit' in lane_status
    
    @pytest.mark.asyncio
    async def test_hub_start_stop(self):
        """Test starting and stopping the hub."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            await hub.start()
            status = hub.get_status()
            assert status['running'] == True
            
            await hub.stop()
            status = hub.get_status()
            assert status['running'] == False
    
    @pytest.mark.asyncio
    async def test_concurrency_limits(self):
        """Test that concurrency limits are respected."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            await hub.start()
            
            # Enqueue more tasks than the limit
            for i in range(5):
                task = Task(
                    id=f"task_{i}",
                    lane=Lane.RESEARCH,  # Limit is 3
                    prompt=f"Task {i}"
                )
                await hub.enqueue(task)
            
            # Give processor time to start tasks
            await asyncio.sleep(0.5)
            
            status = hub.get_status()
            research_status = status['lane_status']['research']
            
            # Should have at most 3 active (the limit)
            assert research_status['active'] <= 3
            
            await hub.stop()
    
    @pytest.mark.asyncio
    async def test_session_creation_automatic(self):
        """Test that sessions are created automatically."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            
            task = Task(
                id="test_task",
                lane=Lane.MAIN,
                prompt="Test",
                session_id="auto_session"
            )
            
            await hub.enqueue(task)
            
            session = hub.get_session("auto_session")
            assert session is not None
            assert session.agent_type in ["task", "unknown"]  # Default type
