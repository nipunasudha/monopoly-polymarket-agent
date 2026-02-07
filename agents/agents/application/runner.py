"""
Background agent runner for automated trading.
Integrates with FastAPI's async event loop.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from enum import Enum

from agents.application.trade import Trader
from agents.connectors.database import Database

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent running states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AgentRunner:
    """Background agent runner with async support."""
    
    def __init__(
        self,
        interval_minutes: int = 60,
        database: Optional[Database] = None,
    ):
        """Initialize agent runner.
        
        Args:
            interval_minutes: Minutes between agent runs (default: 60)
            database: Database instance for logging
        """
        self.interval_minutes = interval_minutes
        self.trader = Trader()
        self.db = database or Database()
        
        self.state = AgentState.STOPPED
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        
    def get_status(self) -> dict:
        """Get current agent status.
        
        Returns:
            Dictionary with status information including total_forecasts and total_trades.
        """
        forecasts = self.db.get_recent_forecasts(limit=1000)
        trades = self.db.get_recent_trades(limit=1000)
        return {
            "state": self.state.value,
            "running": self.state == AgentState.RUNNING,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "interval_minutes": self.interval_minutes,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "total_forecasts": len(forecasts),
            "total_trades": len(trades),
        }
    
    async def run_agent_cycle(self) -> dict:
        """Run a single agent cycle.
        
        Returns:
            Dictionary with cycle results
        """
        cycle_start = datetime.utcnow()
        
        try:
            logger.info("Starting agent cycle...")
            
            # Run the trader
            self.trader.one_best_trade()
            
            self.run_count += 1
            self.last_run = cycle_start
            
            logger.info("Agent cycle completed successfully")
            
            return {
                "success": True,
                "started_at": cycle_start.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error": None,
            }
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Agent cycle failed: {e}")
            
            return {
                "success": False,
                "started_at": cycle_start.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def _run_loop(self):
        """Internal run loop."""
        logger.info(f"Agent runner started (interval: {self.interval_minutes} minutes)")
        
        # Emit initial status before first run
        await self._emit_status_changed()
        
        # Give a brief moment for the status to be broadcast
        await asyncio.sleep(0.1)
        
        while self.state == AgentState.RUNNING:
            try:
                # Calculate next run time
                self.next_run = datetime.utcnow() + timedelta(minutes=self.interval_minutes)
                
                # Emit status with next_run time
                await self._emit_status_changed()
                
                # Run agent cycle
                result = await self.run_agent_cycle()
                
                # Log result
                if result["success"]:
                    logger.info(f"Cycle {self.run_count} completed. Next run: {self.next_run}")
                else:
                    logger.error(f"Cycle {self.run_count} failed: {result['error']}")
                
                # Wait for next cycle
                await asyncio.sleep(self.interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("Agent runner cancelled")
                break
            except Exception as e:
                logger.error(f"Error in run loop: {e}")
                self.state = AgentState.ERROR
                self.last_error = str(e)
                await self._emit_status_changed()
                break
        
        logger.info("Agent runner stopped")
    
    async def start(self):
        """Start the agent runner."""
        if self.state == AgentState.RUNNING:
            logger.warning("Agent is already running")
            return
        
        self.state = AgentState.RUNNING
        self.task = asyncio.create_task(self._run_loop())
        
        # Emit status change event immediately
        await self._emit_status_changed()
        
        logger.info("Agent runner started")
    
    async def stop(self):
        """Stop the agent runner from any state (running or paused)."""
        if self.state == AgentState.STOPPED:
            logger.warning("Agent is already stopped")
            return
        
        was_paused = self.state == AgentState.PAUSED
        self.state = AgentState.STOPPED
        
        # Emit status change event
        await self._emit_status_changed()
        
        # Cancel task if it exists (only exists when running, not when paused)
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        self.next_run = None
        logger.info(f"Agent runner stopped (was {'paused' if was_paused else 'running'})")
    
    async def pause(self):
        """Pause the agent runner."""
        if self.state != AgentState.RUNNING:
            logger.warning("Agent is not running")
            return
        
        self.state = AgentState.PAUSED
        logger.info("Agent runner paused")
        
        # Emit status change event
        await self._emit_status_changed()
    
    async def resume(self):
        """Resume the agent runner."""
        if self.state != AgentState.PAUSED:
            logger.warning("Agent is not paused")
            return
        
        self.state = AgentState.RUNNING
        logger.info("Agent runner resumed")
        
        # Emit status change event
        await self._emit_status_changed()
    
    async def run_once(self) -> dict:
        """Run agent once immediately (manual trigger).
        
        Returns:
            Dictionary with run results
        """
        logger.info("Manual agent run triggered")
        return await self.run_agent_cycle()
    
    def set_interval(self, minutes: int):
        """Update the run interval.
        
        Args:
            minutes: New interval in minutes
        """
        self.interval_minutes = minutes
        logger.info(f"Interval updated to {minutes} minutes")
    
    async def _emit_status_changed(self):
        """Emit agent status changed event."""
        try:
            from agents.connectors.events import get_broadcaster
            broadcaster = get_broadcaster()
            await broadcaster.emit_agent_status_changed(self.get_status())
        except Exception as e:
            logger.warning(f"Failed to emit status change event: {e}")


# Global agent runner instance
_agent_runner: Optional[AgentRunner] = None


def get_agent_runner() -> AgentRunner:
    """Get or create the global agent runner instance.
    
    Returns:
        AgentRunner instance
    """
    global _agent_runner
    if _agent_runner is None:
        _agent_runner = AgentRunner()
    return _agent_runner
