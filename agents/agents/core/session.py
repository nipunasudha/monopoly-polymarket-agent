"""Session and Task management for TradingHub."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time


class Lane(Enum):
    """Task execution lanes with concurrency limits."""
    MAIN = "main"       # Trading decisions (concurrency: 1)
    RESEARCH = "research"  # Background research (concurrency: 3)
    MONITOR = "monitor"    # Position monitoring (concurrency: 2)
    CRON = "cron"          # Scheduled tasks (concurrency: 1)


@dataclass
class Session:
    """Session state for maintaining conversation context."""
    id: str
    agent_type: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: Any):
        """Add a message to the session."""
        if isinstance(content, str):
            message = {"role": role, "content": content}
        else:
            message = {"role": role, "content": content}
        self.messages.append(message)
        self.updated_at = time.time()
    
    def get_messages_for_claude(self) -> List[Dict[str, Any]]:
        """Get messages in Claude SDK format."""
        return self.messages.copy()


@dataclass
class Task:
    """Task to be executed in a specific lane."""
    id: str
    lane: Lane
    prompt: str
    tools: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    session_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """Compare tasks by priority (higher priority first)."""
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority > other.priority  # Higher priority first
