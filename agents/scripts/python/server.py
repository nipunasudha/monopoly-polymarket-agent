# Monopoly Polymarket Agent System — metarunelabs.dev
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import logging

from agents.connectors.database import Database
from agents.application.runner import get_agent_runner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Monopoly Agents API",
    description="API for Polymarket prediction agent system",
    version="0.1.0",
)

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "dashboard" / "templates"))

# Initialize database
# Note: Database file is created in the agents/ directory
# It's ignored by git (see .gitignore)
db = Database()  # Default: sqlite:///monopoly_agents.db
db.create_tables()

# Initialize agent runner
agent_runner = get_agent_runner()


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Application starting up...")
    logger.info("Agent runner initialized (not started)")
    logger.info("Use POST /api/agent/start to begin automated trading")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Application shutting down...")
    if agent_runner.state.value == "running":
        await agent_runner.stop()
    logger.info("Agent runner stopped")


# Pydantic models for API
class ForecastResponse(BaseModel):
    id: int
    market_id: str
    market_question: str
    outcome: str
    probability: float
    confidence: float
    base_rate: Optional[float]
    reasoning: Optional[str]
    created_at: str


class TradeResponse(BaseModel):
    id: int
    market_id: str
    market_question: str
    outcome: str
    side: str
    size: float
    price: Optional[float]
    forecast_probability: float
    edge: Optional[float]
    status: str
    created_at: str
    executed_at: Optional[str]


class PortfolioResponse(BaseModel):
    balance: float
    total_value: float
    open_positions: int
    total_pnl: float
    win_rate: Optional[float]
    total_trades: int
    created_at: str


class AgentStatus(BaseModel):
    state: str
    running: bool
    last_run: Optional[str]
    next_run: Optional[str]
    interval_minutes: int
    run_count: int
    error_count: int
    last_error: Optional[str]
    total_forecasts: int
    total_trades: int


class AgentRunResult(BaseModel):
    success: bool
    started_at: str
    completed_at: str
    error: Optional[str]


class IntervalUpdate(BaseModel):
    interval_minutes: int


# Dashboard Routes (HTML)

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Portfolio overview dashboard."""
    # Get latest portfolio snapshot
    portfolio = db.get_latest_portfolio_snapshot()
    
    # Get portfolio history for chart
    history = db.get_portfolio_history(limit=30)
    
    # Get recent trades
    recent_trades = db.get_recent_trades(limit=5)
    
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "portfolio": portfolio.to_dict() if portfolio else {},
        "history": [h.to_dict() for h in history],
        "recent_trades": [t.to_dict() for t in recent_trades],
    })


@app.get("/markets", response_class=HTMLResponse)
async def dashboard_markets(request: Request):
    """Markets scanner dashboard."""
    return templates.TemplateResponse("markets.html", {
        "request": request,
    })


@app.get("/trades", response_class=HTMLResponse)
async def dashboard_trades(request: Request):
    """Trade history dashboard."""
    trades = db.get_recent_trades(limit=50)
    
    return templates.TemplateResponse("trades.html", {
        "request": request,
        "trades": [t.to_dict() for t in trades],
    })


@app.get("/forecasts", response_class=HTMLResponse)
async def dashboard_forecasts(request: Request):
    """Forecasts dashboard."""
    forecasts = db.get_recent_forecasts(limit=20)
    
    return templates.TemplateResponse("forecasts.html", {
        "request": request,
        "forecasts": [f.to_dict() for f in forecasts],
    })


# API Root endpoint
@app.get("/api")
def read_root():
    return {
        "name": "Monopoly Agents API",
        "version": "0.1.0",
        "status": "running",
    }


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Forecast endpoints
@app.get("/api/forecasts", response_model=List[ForecastResponse])
def get_forecasts(limit: int = 10):
    """Get recent forecasts."""
    forecasts = db.get_recent_forecasts(limit=limit)
    return [
        ForecastResponse(
            id=f.id,
            market_id=f.market_id,
            market_question=f.market_question,
            outcome=f.outcome,
            probability=f.probability,
            confidence=f.confidence,
            base_rate=f.base_rate,
            reasoning=f.reasoning,
            created_at=f.created_at.isoformat(),
        )
        for f in forecasts
    ]


@app.get("/api/forecasts/{forecast_id}", response_model=ForecastResponse)
def get_forecast(forecast_id: int):
    """Get a specific forecast by ID."""
    forecast = db.get_forecast(forecast_id)
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast {forecast_id} not found",
        )
    return ForecastResponse(
        id=forecast.id,
        market_id=forecast.market_id,
        market_question=forecast.market_question,
        outcome=forecast.outcome,
        probability=forecast.probability,
        confidence=forecast.confidence,
        base_rate=forecast.base_rate,
        reasoning=forecast.reasoning,
        created_at=forecast.created_at.isoformat(),
    )


@app.get("/api/markets/{market_id}/forecasts", response_model=List[ForecastResponse])
def get_market_forecasts(market_id: str):
    """Get all forecasts for a specific market."""
    forecasts = db.get_forecasts_by_market(market_id)
    return [
        ForecastResponse(
            id=f.id,
            market_id=f.market_id,
            market_question=f.market_question,
            outcome=f.outcome,
            probability=f.probability,
            confidence=f.confidence,
            base_rate=f.base_rate,
            reasoning=f.reasoning,
            created_at=f.created_at.isoformat(),
        )
        for f in forecasts
    ]


# Trade endpoints
@app.get("/api/trades", response_model=List[TradeResponse])
def get_trades(limit: int = 10):
    """Get recent trades."""
    trades = db.get_recent_trades(limit=limit)
    return [
        TradeResponse(
            id=t.id,
            market_id=t.market_id,
            market_question=t.market_question,
            outcome=t.outcome,
            side=t.side,
            size=t.size,
            price=t.price,
            forecast_probability=t.forecast_probability,
            edge=t.edge,
            status=t.status,
            created_at=t.created_at.isoformat(),
            executed_at=t.executed_at.isoformat() if t.executed_at else None,
        )
        for t in trades
    ]


@app.get("/api/trades/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: int):
    """Get a specific trade by ID."""
    trade = db.get_trade(trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade {trade_id} not found",
        )
    return TradeResponse(
        id=trade.id,
        market_id=trade.market_id,
        market_question=trade.market_question,
        outcome=trade.outcome,
        side=trade.side,
        size=trade.size,
        price=trade.price,
        forecast_probability=trade.forecast_probability,
        edge=trade.edge,
        status=trade.status,
        created_at=trade.created_at.isoformat(),
        executed_at=trade.executed_at.isoformat() if trade.executed_at else None,
    )


# Portfolio endpoints
@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio():
    """Get current portfolio state."""
    snapshot = db.get_latest_portfolio_snapshot()
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio data available",
        )
    return PortfolioResponse(
        balance=snapshot.balance,
        total_value=snapshot.total_value,
        open_positions=snapshot.open_positions,
        total_pnl=snapshot.total_pnl,
        win_rate=snapshot.win_rate,
        total_trades=snapshot.total_trades,
        created_at=snapshot.created_at.isoformat(),
    )


@app.get("/api/portfolio/history", response_model=List[PortfolioResponse])
def get_portfolio_history(limit: int = 30):
    """Get portfolio history."""
    snapshots = db.get_portfolio_history(limit=limit)
    return [
        PortfolioResponse(
            balance=s.balance,
            total_value=s.total_value,
            open_positions=s.open_positions,
            total_pnl=s.total_pnl,
            win_rate=s.win_rate,
            total_trades=s.total_trades,
            created_at=s.created_at.isoformat(),
        )
        for s in snapshots
    ]


# Agent control endpoints
@app.get("/api/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """Get agent status."""
    # Get runner status
    runner_status = agent_runner.get_status()
    
    # Get counts from database
    forecasts = db.get_recent_forecasts(limit=1000)
    trades = db.get_recent_trades(limit=1000)
    
    return AgentStatus(
        state=runner_status["state"],
        running=runner_status["running"],
        last_run=runner_status["last_run"],
        next_run=runner_status["next_run"],
        interval_minutes=runner_status["interval_minutes"],
        run_count=runner_status["run_count"],
        error_count=runner_status["error_count"],
        last_error=runner_status["last_error"],
        total_forecasts=len(forecasts),
        total_trades=len(trades),
    )


@app.post("/api/agent/start")
async def start_agent():
    """Start the agent background runner."""
    if agent_runner.state.value == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is already running"
        )
    
    await agent_runner.start()
    
    return {
        "status": "started",
        "message": f"Agent started with {agent_runner.interval_minutes} minute interval",
        "next_run": agent_runner.next_run.isoformat() if agent_runner.next_run else None,
    }


@app.post("/api/agent/stop")
async def stop_agent():
    """Stop the agent background runner."""
    if agent_runner.state.value != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not running"
        )
    
    await agent_runner.stop()
    
    return {
        "status": "stopped",
        "message": "Agent stopped successfully",
    }


@app.post("/api/agent/pause")
async def pause_agent():
    """Pause the agent background runner."""
    await agent_runner.pause()
    return {"status": "paused", "message": "Agent paused"}


@app.post("/api/agent/resume")
async def resume_agent():
    """Resume the agent background runner."""
    await agent_runner.resume()
    return {"status": "resumed", "message": "Agent resumed"}


@app.post("/api/agent/run-once", response_model=AgentRunResult)
async def run_agent_once():
    """Manually trigger a single agent run."""
    result = await agent_runner.run_once()
    return AgentRunResult(**result)


@app.put("/api/agent/interval")
async def update_interval(interval: IntervalUpdate):
    """Update agent run interval.
    
    Args:
        interval: New interval in minutes
    """
    if interval.interval_minutes < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interval must be at least 1 minute"
        )
    
    agent_runner.set_interval(interval.interval_minutes)
    
    return {
        "status": "updated",
        "interval_minutes": interval.interval_minutes,
        "message": f"Interval updated to {interval.interval_minutes} minutes",
    }


# Market analysis endpoint
@app.post("/api/markets/{market_id}/analyze")
def analyze_market(market_id: str):
    """Trigger analysis for a specific market."""
    # TODO: Implement market analysis logic
    return {
        "status": "analyzing",
        "market_id": market_id,
        "message": "Market analysis not yet implemented",
    }
