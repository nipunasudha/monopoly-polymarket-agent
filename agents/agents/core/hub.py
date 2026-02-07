"""TradingHub - Lane-based task queue manager for OpenClaw architecture."""

import os
import asyncio
import logging
from collections import deque
from typing import Dict, Set, Optional, Any
from datetime import datetime
import time

from anthropic import Anthropic
from dotenv import load_dotenv

from agents.core.session import Lane, Session, Task
from agents.core.tools import ToolRegistry

# Phase 8: Structured logging
try:
    from agents.core.structured_logging import get_logger, PerformanceMetrics
    logger = get_logger(__name__)
    USE_STRUCTLOG = True
except ImportError:
    logger = logging.getLogger(__name__)
    USE_STRUCTLOG = False

load_dotenv()


class TradingHub:
    """Single control plane managing all agent sessions with lane-based concurrency.
    
    Features:
    - Lane-based task queuing (MAIN, RESEARCH, MONITOR, CRON)
    - Concurrency limits per lane
    - Session management for multi-turn conversations
    - Claude SDK tool use loop for task execution
    - Automatic task processing
    """
    
    # Lane concurrency limits
    LANE_LIMITS = {
        Lane.MAIN: 1,        # Trading decisions serialized
        Lane.RESEARCH: 3,    # Background research parallel
        Lane.MONITOR: 2,     # Position monitoring parallel
        Lane.CRON: 1,       # Scheduled tasks serialized
    }
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize TradingHub.
        
        Args:
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        
        # Session management
        self.sessions: Dict[str, Session] = {}
        
        # Lane queues (priority queues using deque with sorted insertion)
        self.lanes: Dict[Lane, deque] = {
            lane: deque() for lane in Lane
        }
        
        # Active tasks per lane (tracking concurrency)
        self.active_tasks: Dict[Lane, Set[str]] = {
            lane: set() for lane in Lane
        }
        
        # Task results storage
        self.task_results: Dict[str, Any] = {}
        self.task_result_timestamps: Dict[str, float] = {}
        
        # Tool registry
        self.tool_registry = ToolRegistry()
        
        # Background task processor
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Cleanup configuration
        self.session_ttl_seconds = 3600  # 1 hour
        self.task_result_ttl_seconds = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "tasks_enqueued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "sessions_created": 0,
            "sessions_cleaned": 0,
            "results_cleaned": 0,
        }
        
        # Phase 8: Performance metrics
        if USE_STRUCTLOG:
            self.metrics = PerformanceMetrics(logger)
        else:
            self.metrics = None
    
    async def start(self):
        """Start the background task processor."""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_lanes())
    
    async def stop(self):
        """Stop the background task processor."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
    
    async def enqueue(self, task: Task) -> str:
        """Add task to appropriate lane queue.
        
        Args:
            task: Task to enqueue
            
        Returns:
            Task ID
        """
        # Ensure session exists if session_id is provided
        if task.session_id and task.session_id not in self.sessions:
            agent_type = task.context.get("agent_type", "task")
            self._create_session(task.session_id, agent_type)
        
        # Add to lane queue (insert sorted by priority)
        lane_queue = self.lanes[task.lane]
        
        # Simple insertion sort by priority
        inserted = False
        for i, queued_task in enumerate(lane_queue):
            if task.priority > queued_task.priority:
                lane_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            lane_queue.append(task)
        
        self.stats["tasks_enqueued"] += 1
        
        # Phase 8: Record queue metrics
        if self.metrics:
            self.metrics.increment("tasks_enqueued", 1, lane=task.lane.value)
            self.metrics.record("queue_size", len(lane_queue), lane=task.lane.value)
        
        return task.id
    
    async def enqueue_and_wait(self, task: Task, timeout: Optional[float] = None) -> Any:
        """Enqueue task and wait for result.
        
        Args:
            task: Task to enqueue
            timeout: Optional timeout in seconds
            
        Returns:
            Task result
        """
        task_id = await self.enqueue(task)
        
        # Wait for result
        start_time = time.time()
        while task_id not in self.task_results:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
            await asyncio.sleep(0.1)
        
        result = self.task_results.pop(task_id)
        if isinstance(result, Exception):
            raise result
        return result
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def _create_session(self, session_id: str, agent_type: str) -> Session:
        """Create a new session."""
        session = Session(id=session_id, agent_type=agent_type)
        self.sessions[session_id] = session
        self.stats["sessions_created"] += 1
        return session
    
    async def _process_lanes(self):
        """Background processor that executes tasks from all lanes."""
        cleanup_counter = 0
        while self._running:
            try:
                # Process each lane
                for lane in Lane:
                    await self._process_lane(lane)
                
                # Cleanup every 100 iterations (~10 seconds)
                cleanup_counter += 1
                if cleanup_counter >= 100:
                    await self._cleanup_old_sessions()
                    await self._cleanup_old_task_results()
                    cleanup_counter = 0
                
                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lane processor: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_lane(self, lane: Lane):
        """Process tasks in a specific lane up to concurrency limit."""
        lane_queue = self.lanes[lane]
        active = self.active_tasks[lane]
        limit = self.LANE_LIMITS[lane]
        
        # Start new tasks if under limit
        while len(active) < limit and lane_queue:
            task = lane_queue.popleft()
            active.add(task.id)
            
            # Execute task in background
            asyncio.create_task(self._execute_task(task, lane))
    
    async def _execute_task(self, task: Task, lane: Lane):
        """Execute a task with Claude SDK tool use loop.
        
        Args:
            task: Task to execute
            lane: Lane the task belongs to
        """
        # Phase 8: Track execution time
        start_time = time.time()
        
        try:
            # Get or create session
            if task.session_id:
                session = self.sessions.get(task.session_id)
                if not session:
                    session = self._create_session(task.session_id, "task")
            else:
                # Create temporary session for this task
                session = self._create_session(f"temp_{task.id}", "task")
            
            # Get tool schemas for requested tools
            all_tools = self.tool_registry.get_tool_schemas()
            requested_tools = [
                tool for tool in all_tools 
                if not task.tools or tool["name"] in task.tools
            ]
            
            # Add user message
            session.add_message("user", task.prompt)
            
            # Execute Claude SDK tool use loop
            result = await self._claude_tool_use_loop(
                session=session,
                tools=requested_tools,
                system_prompt=self._get_system_prompt(lane)
            )
            
            # Store result with timestamp
            self.task_results[task.id] = result
            self.task_result_timestamps[task.id] = time.time()
            self.stats["tasks_completed"] += 1
            
            # Phase 8: Record performance metrics
            duration_ms = (time.time() - start_time) * 1000
            if self.metrics:
                self.metrics.timing(
                    "task_execution",
                    duration_ms,
                    task_id=task.id,
                    lane=lane.value,
                    success=True
                )
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            self.task_results[task.id] = e
            self.task_result_timestamps[task.id] = time.time()
            self.stats["tasks_failed"] += 1
            
            # Phase 8: Record failure metrics
            duration_ms = (time.time() - start_time) * 1000
            if self.metrics:
                self.metrics.timing(
                    "task_execution",
                    duration_ms,
                    task_id=task.id,
                    lane=lane.value,
                    success=False,
                    error=str(e)
                )
        finally:
            # Remove from active tasks
            self.active_tasks[lane].discard(task.id)
    
    async def _claude_tool_use_loop(
        self,
        session: Session,
        tools: list,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Execute Claude SDK tool use loop.
        
        Args:
            session: Session with message history
            tools: List of tool schemas
            system_prompt: Optional system prompt
            max_iterations: Maximum tool use iterations
            
        Returns:
            Final result dictionary
        """
        messages = session.get_messages_for_claude()
        
        for iteration in range(max_iterations):
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tools if tools else None,
            )
            
            # Add assistant response to messages
            assistant_message = {
                "role": "assistant",
                "content": []
            }
            
            tool_results = []
            has_tool_use = False
            
            # Process content blocks
            for block in response.content:
                if block.type == "text":
                    assistant_message["content"].append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    has_tool_use = True
                    assistant_message["content"].append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            messages.append(assistant_message)
            
            # If no tool use, return final response
            if not has_tool_use:
                # Extract text from response
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                
                return {
                    "success": True,
                    "response": text_content,
                    "iterations": iteration + 1,
                    "session_id": session.id
                }
            
            # Execute tool calls
            tool_result_content = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    
                    # Execute tool
                    try:
                        tool_result = await self.tool_registry.execute_tool(
                            tool_name, **tool_input
                        )
                        
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(tool_result)
                        })
                    except Exception as e:
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })
            
            # Add tool results to messages
            if tool_result_content:
                messages.append({
                    "role": "user",
                    "content": tool_result_content
                })
        
        # Max iterations reached
        return {
            "success": False,
            "error": "Max tool use iterations reached",
            "iterations": max_iterations,
            "session_id": session.id
        }
    
    def _get_system_prompt(self, lane: Lane) -> str:
        """Get system prompt for a lane."""
        prompts = {
            Lane.MAIN: """You are a quantitative trading agent specializing in prediction markets.
            Analyze market data, calculate expected value, and make trading decisions.
            Be precise, risk-aware, and data-driven.""",
            
            Lane.RESEARCH: """You are a research analyst specializing in market research.
            Use available tools to gather information, analyze trends, and provide insights.
            Be thorough and cite sources when possible.""",
            
            Lane.MONITOR: """You are a position monitoring agent.
            Track open positions, analyze performance, and identify risks.
            Provide clear status updates and alerts.""",
            
            Lane.CRON: """You are a scheduled task agent.
            Execute routine tasks, generate reports, and maintain system health.
            Be efficient and reliable.""",
        }
        return prompts.get(lane, "You are a helpful AI assistant.")
    
    async def _cleanup_old_sessions(self):
        """Remove sessions inactive for > session_ttl_seconds."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if (current_time - session.updated_at) > self.session_ttl_seconds
        ]
        
        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)
            self.stats["sessions_cleaned"] += 1
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _cleanup_old_task_results(self):
        """Remove task results older than task_result_ttl_seconds."""
        current_time = time.time()
        expired_tasks = [
            task_id for task_id, timestamp in self.task_result_timestamps.items()
            if (current_time - timestamp) > self.task_result_ttl_seconds
        ]
        
        for task_id in expired_tasks:
            self.task_results.pop(task_id, None)
            self.task_result_timestamps.pop(task_id, None)
            self.stats["results_cleaned"] += 1
        
        if expired_tasks:
            logger.info(f"Cleaned up {len(expired_tasks)} expired task results")
    
    def get_status(self) -> Dict[str, Any]:
        """Get hub status information."""
        status = {
            "running": self._running,
            "sessions": len(self.sessions),
            "lane_status": {
                lane.value: {
                    "queued": len(self.lanes[lane]),
                    "active": len(self.active_tasks[lane]),
                    "limit": self.LANE_LIMITS[lane]
                }
                for lane in Lane
            },
            "stats": self.stats.copy(),
            "pending_results": len(self.task_results)
        }
        
        # Phase 8: Add performance metrics
        if self.metrics:
            status["metrics"] = self.metrics.get_all()
        
        return status
