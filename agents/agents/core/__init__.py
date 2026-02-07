"""Core module for OpenClaw-inspired architecture."""

from agents.core.tools import ToolRegistry
from agents.core.session import Lane, Session, Task
from agents.core.hub import TradingHub
from agents.core.agents import ResearchAgent, TradingAgent
from agents.core.approvals import ApprovalManager, ApprovalStatus, ApprovalRequest

__all__ = [
    "ToolRegistry",
    "Lane",
    "Session",
    "Task",
    "TradingHub",
    "ResearchAgent",
    "TradingAgent",
    "ApprovalManager",
    "ApprovalStatus",
    "ApprovalRequest",
]
