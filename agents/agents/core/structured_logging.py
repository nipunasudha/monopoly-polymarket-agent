"""
Structured logging configuration for Monopoly Agents (Phase 8).

Provides JSON-formatted, contextual logging with performance metrics.
"""
import structlog
import logging
import sys
from typing import Any, Dict


def configure_structlog(
    level: str = "INFO",
    json_output: bool = False
) -> None:
    """
    Configure structlog for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON. If False, use console-friendly format.
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Choose processors based on output format
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if json_output:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console-friendly output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class PerformanceMetrics:
    """Helper class for tracking performance metrics."""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger
        self.metrics: Dict[str, Any] = {}
    
    def record(self, metric_name: str, value: Any, **context):
        """Record a performance metric."""
        self.metrics[metric_name] = value
        self.logger.info(
            "metric_recorded",
            metric=metric_name,
            value=value,
            **context
        )
    
    def increment(self, metric_name: str, amount: int = 1, **context):
        """Increment a counter metric."""
        current = self.metrics.get(metric_name, 0)
        self.metrics[metric_name] = current + amount
        self.logger.debug(
            "metric_incremented",
            metric=metric_name,
            new_value=self.metrics[metric_name],
            **context
        )
    
    def timing(self, metric_name: str, duration_ms: float, **context):
        """Record a timing metric."""
        self.logger.info(
            "timing_metric",
            metric=metric_name,
            duration_ms=duration_ms,
            **context
        )
    
    def get_all(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return self.metrics.copy()
