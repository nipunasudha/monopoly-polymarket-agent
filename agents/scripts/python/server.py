# Monopoly Polymarket Agent System — metarunelabs.dev
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
import json
import httpx

from agents.connectors.database import Database
from agents.application.runner import get_agent_runner
from agents.connectors.events import get_broadcaster
from agents.polymarket.polymarket import Polymarket
from agents.connectors.news import News

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Monopoly Agents API",
    description="API for Polymarket prediction agent system",
    version="0.1.0",
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Old UI (HTMX/Alpine.js/Jinja2) and SSE removed - using Next.js + WebSocket only

# Initialize database
# Note: Database file is created in the agents/ directory
# It's ignored by git (see .gitignore)
db = Database()  # Default: sqlite:///monopoly_agents.db
db.create_tables()

# Initialize Polymarket client
poly = Polymarket()

# Initialize News client
news_client = News()

# Initialize agent runner
agent_runner = get_agent_runner()

# Initialize event broadcaster
broadcaster = get_broadcaster()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

ws_manager = ConnectionManager()


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Application starting up...")
    logger.info("Agent runner initialized (not started)")
    logger.info("Use POST /api/agent/start to begin automated trading")
    
    # Connect broadcaster to WebSocket manager
    broadcaster.set_ws_manager(ws_manager)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("=" * 60)
    logger.info("Application shutdown initiated")
    logger.info("=" * 60)
    
    # Stop agent runner
    if agent_runner.state.value == "running":
        logger.info("Stopping agent runner...")
        await agent_runner.stop()
        logger.info("Agent runner stopped")
    
    logger.info("Shutdown complete")
    logger.info("=" * 60)


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
    trading_mode: str  # "dry_run" or "live"


class AgentRunResult(BaseModel):
    success: bool
    started_at: str
    completed_at: str
    error: Optional[str]


class IntervalUpdate(BaseModel):
    interval_minutes: int


# Dashboard Routes (HTML)

@app.get("/api/markets")
async def get_markets(
    closed: Optional[bool] = None,
    end_date_min: Optional[str] = None,
    end_date_max: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Get available markets using Polymarket's actual API parameters.
    
    Args:
        closed: Filter by closed status (false for open markets)
        end_date_min: Minimum end date in ISO format (e.g., '2026-02-07T00:00:00Z')
        end_date_max: Maximum end date in ISO format
        limit: Number of markets to return (default: 50)
        offset: Pagination offset (default: 0)
    """
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    
    if dry_run:
        # Return fixture data instantly - filter by date if specified
        from datetime import datetime, timedelta
        
        all_fixture_markets = [
            {
                "id": "21742633621281841065619472033692432265820606149693301024636724346570693356136",
                "question": "Will Elon and DOGE cut between $200-250b in federal spending in 2025?",
                "end": "2026-01-01T00:00:00Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.007", "0.993"],
                "description": "This market will resolve to 'Yes' if verified government reports show spending cuts between $200-250 billion in 2025.",
                "volume": 1250000.0,
                "liquidity": 85000.0,
                "spread": 0.02,
                "funded": True,
                "clob_token_ids": ["token1", "token2"],
            },
            {
                "id": "mock_trump_approval_q1",
                "question": "Will Trump's approval rating be above 50% by end of Q1 2025?",
                "end": "2025-03-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.62", "0.38"],
                "description": "Resolves based on RealClearPolitics average on March 31, 2025.",
                "volume": 850000.0,
                "liquidity": 42000.0,
                "spread": 0.015,
                "funded": True,
                "clob_token_ids": ["token3", "token4"],
            },
            {
                "id": "mock_btc_100k",
                "question": "Will Bitcoin reach $100,000 in 2025?",
                "end": "2025-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.73", "0.27"],
                "description": "This market resolves to 'Yes' if Bitcoin trades at or above $100,000 at any point in 2025.",
                "volume": 3200000.0,
                "liquidity": 150000.0,
                "spread": 0.01,
                "funded": True,
                "clob_token_ids": ["token5", "token6"],
            },
            {
                "id": "mock_ai_agi",
                "question": "Will AGI be achieved by end of 2026?",
                "end": "2026-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.15", "0.85"],
                "description": "Resolves based on consensus of AI researchers and demonstration of general intelligence.",
                "volume": 620000.0,
                "liquidity": 28000.0,
                "spread": 0.03,
                "funded": False,
                "clob_token_ids": [],
            },
            {
                "id": "mock_fed_rate",
                "question": "Will the Fed cut rates below 4% in 2025?",
                "end": "2025-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.58", "0.42"],
                "description": "Resolves to 'Yes' if the Federal Reserve's target rate goes below 4.00%.",
                "volume": 980000.0,
                "liquidity": 55000.0,
                "spread": 0.018,
                "funded": True,
                "clob_token_ids": ["token7", "token8"],
            },
            {
                "id": "mock_spacex_starship",
                "question": "Will SpaceX land Starship on Mars in 2026?",
                "end": "2026-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.08", "0.92"],
                "description": "Resolves to 'Yes' if SpaceX successfully lands a Starship on Mars.",
                "volume": 450000.0,
                "liquidity": 22000.0,
                "spread": 0.025,
                "funded": True,
                "clob_token_ids": ["token9", "token10"],
            },
            {
                "id": "mock_recession_2025",
                "question": "Will the US enter a recession in 2025?",
                "end": "2025-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.32", "0.68"],
                "description": "Resolves based on NBER official recession dating.",
                "volume": 1100000.0,
                "liquidity": 68000.0,
                "spread": 0.012,
                "funded": True,
                "clob_token_ids": ["token11", "token12"],
            },
            {
                "id": "mock_ai_regulation",
                "question": "Will major AI regulation pass in the US in 2025?",
                "end": "2025-12-31T23:59:59Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.45", "0.55"],
                "description": "Resolves to 'Yes' if comprehensive AI regulation is signed into law.",
                "volume": 380000.0,
                "liquidity": 19000.0,
                "spread": 0.022,
                "funded": False,
                "clob_token_ids": [],
            },
            # Esports markets
            {
                "id": "mock_esports_cs2_major",
                "question": "Will Team Liquid win the CS2 Major Championship this week?",
                "end": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.35", "0.65"],
                "description": "Resolves to 'Yes' if Team Liquid wins the CS2 Major Championship.",
                "volume": 250000.0,
                "liquidity": 15000.0,
                "spread": 0.015,
                "funded": True,
                "clob_token_ids": ["token13", "token14"],
            },
            {
                "id": "mock_esports_valorant",
                "question": "Will Fnatic win the Valorant Champions Tour match today?",
                "end": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.48", "0.52"],
                "description": "Resolves based on today's VCT match result.",
                "volume": 180000.0,
                "liquidity": 12000.0,
                "spread": 0.012,
                "funded": True,
                "clob_token_ids": ["token15", "token16"],
            },
            {
                "id": "mock_esports_lol",
                "question": "Will T1 win the League of Legends World Championship finals?",
                "end": (datetime.utcnow() + timedelta(days=5)).isoformat() + "Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.42", "0.58"],
                "description": "Resolves to 'Yes' if T1 wins the LoL Worlds finals.",
                "volume": 320000.0,
                "liquidity": 18000.0,
                "spread": 0.018,
                "funded": True,
                "clob_token_ids": ["token17", "token18"],
            },
            {
                "id": "mock_esports_dota",
                "question": "Will Team Spirit win The International Dota 2 tournament?",
                "end": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
                "active": True,
                "outcomes": ["Yes", "No"],
                "outcome_prices": ["0.28", "0.72"],
                "description": "Resolves based on The International tournament results.",
                "volume": 450000.0,
                "liquidity": 25000.0,
                "spread": 0.020,
                "funded": True,
                "clob_token_ids": ["token19", "token20"],
            },
        ]
        
        # Filter fixture markets by date and closed status
        filtered_fixtures = []
        
        for market in all_fixture_markets:
            # Filter by closed status
            if closed is not None and market.get("active") == closed:
                continue
            
            # Filter by date range
            if end_date_min or end_date_max:
                try:
                    market_end = datetime.fromisoformat(market["end"].replace('Z', '+00:00'))
                    
                    if end_date_min:
                        min_dt = datetime.fromisoformat(end_date_min.replace('Z', '+00:00'))
                        if market_end < min_dt:
                            continue
                    
                    if end_date_max:
                        max_dt = datetime.fromisoformat(end_date_max.replace('Z', '+00:00'))
                        if market_end > max_dt:
                            continue
                except Exception as e:
                    logger.warning(f"Date parsing error: {e}")
                    pass
            
            filtered_fixtures.append(market)
        
        return {"markets": filtered_fixtures, "dry_run": True}
    
    # Live mode - fetch real markets using correct API parameters
    try:
        # Build query parameters matching Polymarket's API
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if closed is not None:
            params["closed"] = "true" if closed else "false"
        
        if end_date_min:
            params["end_date_min"] = end_date_min
        
        if end_date_max:
            params["end_date_max"] = end_date_max
        
        # Fetch markets from Polymarket API
        raw_response = httpx.get(poly.gamma_markets_endpoint, params=params, timeout=10.0)
        raw_markets = raw_response.json() if raw_response.status_code == 200 else []
        
        markets_data = []
        for market in raw_markets:
            # Parse outcomes and outcome_prices from strings to arrays
            outcomes = market.get("outcomes", "")
            outcome_prices = market.get("outcomePrices", "")
            
            # Try to parse as JSON first, then as comma-separated
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except (json.JSONDecodeError, ValueError):
                    outcomes = [o.strip() for o in outcomes.split(',')] if outcomes else []
            
            if isinstance(outcome_prices, str):
                try:
                    outcome_prices = json.loads(outcome_prices)
                except (json.JSONDecodeError, ValueError):
                    outcome_prices = [p.strip() for p in outcome_prices.split(',')] if outcome_prices else []
            
            # Extract volume/liquidity
            volume = float(market.get("volume", 0)) if market.get("volume") else 0.0
            liquidity = float(market.get("liquidity", 0)) if market.get("liquidity") else 0.0
            
            # Parse clob_token_ids if it's a string
            clob_token_ids = market.get("clobTokenIds", "")
            if isinstance(clob_token_ids, str):
                try:
                    clob_token_ids = json.loads(clob_token_ids)
                except (json.JSONDecodeError, ValueError):
                    clob_token_ids = [t.strip() for t in clob_token_ids.split(',')] if clob_token_ids else []
            
            markets_data.append({
                "id": str(market.get("id", "")),
                "question": market.get("question", ""),
                "end": market.get("endDate", ""),
                "active": market.get("active", True),
                "outcomes": outcomes if isinstance(outcomes, list) else [],
                "outcome_prices": outcome_prices if isinstance(outcome_prices, list) else [],
                "description": market.get("description", ""),
                "volume": volume,
                "liquidity": liquidity,
                "spread": float(market.get("spread", 0)) if market.get("spread") else 0.0,
                "funded": bool(market.get("funded", False)),
                "clob_token_ids": clob_token_ids if isinstance(clob_token_ids, list) else [],
            })
        
        return {"markets": markets_data, "dry_run": False}
    except Exception as e:
        logger.error(f"Could not fetch markets: {e}")
        return {"markets": [], "dry_run": False, "error": str(e)}


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


def _get_realtime_state():
    """Build the full realtime state sent to clients (init and optional state_update).
    Add new realtime fields here; then add the same keys to frontend RealtimeState and patchRealtime."""
    portfolio = db.get_latest_portfolio_snapshot()
    portfolio_data = (
        portfolio.to_dict()
        if portfolio
        else {
            "id": 0,
            "balance": 0.0,
            "total_value": 0.0,
            "open_positions": 0,
            "total_pnl": 0.0,
            "win_rate": None,
            "total_trades": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    agent_status = agent_runner.get_status()
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    trading_mode = "dry_run" if dry_run else "live"
    if dry_run and agent_status.get("total_forecasts", 0) == 0 and agent_status.get("total_trades", 0) == 0:
        agent_status["total_forecasts"] = 3
        agent_status["total_trades"] = 4
    agent_status["trading_mode"] = trading_mode
    return {"agent": agent_status, "portfolio": portfolio_data}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates and bidirectional communication."""
    await ws_manager.connect(websocket)

    try:
        await websocket.send_json({"type": "init", "data": _get_realtime_state()})
        
        # Listen for commands
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            logger.info(f"WebSocket command received: {action}")
            
            if action == "start":
                if agent_runner.state.value != "running":
                    await agent_runner.start()
                    await websocket.send_json({
                        "type": "agent_status_changed",
                        "data": agent_runner.get_status(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif action == "stop":
                if agent_runner.state.value != "stopped":
                    await agent_runner.stop()
                    await websocket.send_json({
                        "type": "agent_status_changed",
                        "data": agent_runner.get_status(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif action == "pause":
                if agent_runner.state.value == "running":
                    await agent_runner.pause()
                    await websocket.send_json({
                        "type": "agent_status_changed",
                        "data": agent_runner.get_status(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif action == "resume":
                if agent_runner.state.value == "paused":
                    await agent_runner.resume()
                    await websocket.send_json({
                        "type": "agent_status_changed",
                        "data": agent_runner.get_status(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif action == "run_once":
                result = await agent_runner.run_once()
                await websocket.send_json({
                    "type": "agent_run_result",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Refresh status after run
                await websocket.send_json({
                    "type": "agent_status_changed",
                    "data": agent_runner.get_status(),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# Forecast endpoints
@app.get("/api/forecasts", response_model=List[ForecastResponse])
def get_forecasts(limit: int = 10):
    """Get recent forecasts (with fixture data in dry_run mode)."""
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    
    forecasts = db.get_recent_forecasts(limit=limit)
    
    # If no data and in dry_run mode, return fixture data
    if not forecasts and dry_run:
        from datetime import timedelta
        now = datetime.utcnow()
        fixture_forecasts = [
            ForecastResponse(
                id=1,
                market_id="mock_btc_100k",
                market_question="Will Bitcoin reach $100,000 in 2025?",
                outcome="YES",
                probability=0.73,
                confidence=0.82,
                base_rate=0.65,
                reasoning="Strong institutional adoption and halving cycle support bullish momentum.",
                created_at=(now - timedelta(hours=2)).isoformat(),
            ),
            ForecastResponse(
                id=2,
                market_id="mock_trump_approval_q1",
                market_question="Will Trump's approval rating be above 50% by end of Q1 2025?",
                outcome="YES",
                probability=0.62,
                confidence=0.75,
                base_rate=0.55,
                reasoning="Historical honeymoon period for new administrations suggests sustained approval.",
                created_at=(now - timedelta(hours=4)).isoformat(),
            ),
            ForecastResponse(
                id=3,
                market_id="mock_fed_rate",
                market_question="Will the Fed cut rates below 4% in 2025?",
                outcome="YES",
                probability=0.58,
                confidence=0.68,
                base_rate=0.50,
                reasoning="Economic indicators suggest gradual easing policy likely in late 2025.",
                created_at=(now - timedelta(hours=6)).isoformat(),
            ),
        ]
        return fixture_forecasts[:limit]
    
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
    """Get recent trades (with fixture data in dry_run mode)."""
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    
    trades = db.get_recent_trades(limit=limit)
    
    # If no data and in dry_run mode, return fixture data
    if not trades and dry_run:
        from datetime import timedelta
        now = datetime.utcnow()
        fixture_trades = [
            TradeResponse(
                id=1,
                market_id="mock_btc_100k",
                market_question="Will Bitcoin reach $100,000 in 2025?",
                outcome="YES",
                side="BUY",
                size=75.00,
                price=0.73,
                forecast_probability=0.73,
                edge=0.08,
                status="simulated",
                created_at=(now - timedelta(hours=2)).isoformat(),
                executed_at=(now - timedelta(hours=2, minutes=1)).isoformat(),
            ),
            TradeResponse(
                id=2,
                market_id="mock_trump_approval_q1",
                market_question="Will Trump's approval rating be above 50% by end of Q1 2025?",
                outcome="YES",
                side="BUY",
                size=120.00,
                price=0.62,
                forecast_probability=0.62,
                edge=0.05,
                status="simulated",
                created_at=(now - timedelta(hours=4)).isoformat(),
                executed_at=(now - timedelta(hours=4, minutes=1)).isoformat(),
            ),
            TradeResponse(
                id=3,
                market_id="mock_recession_2025",
                market_question="Will the US enter a recession in 2025?",
                outcome="NO",
                side="BUY",
                size=85.00,
                price=0.68,
                forecast_probability=0.68,
                edge=0.12,
                status="simulated",
                created_at=(now - timedelta(hours=8)).isoformat(),
                executed_at=(now - timedelta(hours=8, minutes=1)).isoformat(),
            ),
            TradeResponse(
                id=4,
                market_id="mock_ai_regulation",
                market_question="Will major AI regulation pass in the US in 2025?",
                outcome="YES",
                side="BUY",
                size=60.00,
                price=0.45,
                forecast_probability=0.45,
                edge=0.03,
                status="simulated",
                created_at=(now - timedelta(hours=12)).isoformat(),
                executed_at=(now - timedelta(hours=12, minutes=1)).isoformat(),
            ),
        ]
        return fixture_trades[:limit]
    
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
    """Get current portfolio state (with fixture data in dry_run mode)."""
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    
    snapshot = db.get_latest_portfolio_snapshot()
    
    # If no real data exists or snapshot has all zeros, use fixture data in dry_run mode
    if dry_run and (not snapshot or (snapshot.balance == 0 and snapshot.total_trades == 0)):
        return PortfolioResponse(
            balance=875.42,
            total_value=1243.67,
            open_positions=3,
            total_pnl=368.25,
            win_rate=0.667,
            total_trades=12,
            created_at=datetime.utcnow().isoformat(),
        )
    
    # If no data exists, return zeros
    if not snapshot:
        return PortfolioResponse(
            balance=0.0,
            total_value=0.0,
            open_positions=0,
            total_pnl=0.0,
            win_rate=None,
            total_trades=0,
            created_at=datetime.utcnow().isoformat(),
        )
    
    # Return real data
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
    """Get portfolio history (with fixture data in dry_run mode)."""
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    
    snapshots = db.get_portfolio_history(limit=limit)
    
    # If no data and in dry_run mode, return fixture history
    if not snapshots and dry_run:
        from datetime import timedelta
        now = datetime.utcnow()
        fixture_history = []
        
        # Generate 10 days of fixture data showing growth
        for i in range(10):
            days_ago = 9 - i
            balance = 500.0 + (i * 37.5)  # Growing from 500 to 837.5
            pnl = balance - 500.0
            trades = i + 1
            win_rate = 0.6 + (i * 0.007)  # Improving from 0.6 to 0.667
            
            fixture_history.append(PortfolioResponse(
                balance=balance,
                total_value=balance + (i * 40),  # Additional value from positions
                open_positions=min(i // 2, 3),
                total_pnl=pnl,
                win_rate=win_rate if trades > 0 else None,
                total_trades=trades,
                created_at=(now - timedelta(days=days_ago)).isoformat(),
            ))
        
        return fixture_history
    
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
    """Get agent status (with fixture counts in dry_run mode when DB is empty)."""
    runner_status = agent_runner.get_status()
    dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
    trading_mode = "dry_run" if dry_run else "live"
    
    total_forecasts = runner_status.get("total_forecasts", 0)
    total_trades = runner_status.get("total_trades", 0)
    if dry_run and total_forecasts == 0 and total_trades == 0:
        total_forecasts = 3
        total_trades = 4
    
    return AgentStatus(
        state=runner_status["state"],
        running=runner_status["running"],
        last_run=runner_status["last_run"],
        next_run=runner_status["next_run"],
        interval_minutes=runner_status["interval_minutes"],
        run_count=runner_status["run_count"],
        error_count=runner_status["error_count"],
        last_error=runner_status["last_error"],
        total_forecasts=total_forecasts,
        total_trades=total_trades,
        trading_mode=trading_mode,
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
    """Stop the agent background runner from any state (running or paused)."""
    if agent_runner.state.value == "stopped":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is already stopped"
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


@app.post("/api/agent/interval")
async def update_interval_post(interval: IntervalUpdate):
    """Update agent run interval (POST version for HTMX).
    
    Args:
        interval: New interval in minutes
    """
    if interval.interval_minutes < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interval must be at least 1 minute"
        )
    
    agent_runner.set_interval(interval.interval_minutes)
    await agent_runner._emit_status_changed()
    
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


# Polymarket sync endpoint
@app.post("/api/sync/balance")
def sync_balance():
    """Sync USDC balance from Polymarket."""
    try:
        balance = poly.get_usdc_balance()
        
        # Save portfolio snapshot
        portfolio_data = {
            "balance": balance,
            "total_value": balance,
            "open_positions": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
        }
        
        snapshot = db.save_portfolio_snapshot(portfolio_data)
        
        return {
            "status": "success",
            "balance": balance,
            "snapshot_id": snapshot.id,
            "message": f"Balance synced: ${balance:.2f}",
        }
    except Exception as e:
        logger.error(f"Failed to sync balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync balance: {str(e)}"
        )


@app.post("/api/sync/markets")
def sync_markets():
    """Sync markets from Polymarket and create forecasts."""
    try:
        markets = poly.get_all_markets()
        
        synced_count = 0
        for market in markets[:10]:  # Sync first 10 markets
            # Check if we already have a forecast for this market
            existing = db.get_forecasts_by_market(str(market.id))
            if existing:
                continue
            
            # Create a basic forecast
            forecast_data = {
                "market_id": str(market.id),
                "market_question": market.question,
                "outcome": "Yes",
                "probability": 0.5,  # Neutral starting point
                "confidence": 0.5,
                "base_rate": 0.5,
                "reasoning": "Market synced from Polymarket API",
            }
            
            db.save_forecast(forecast_data)
            synced_count += 1
        
        return {
            "status": "success",
            "total_markets": len(markets),
            "synced_count": synced_count,
            "message": f"Synced {synced_count} new markets",
        }
    except Exception as e:
        logger.error(f"Failed to sync markets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync markets: {str(e)}"
        )


# News endpoints
@app.get("/api/news/search")
def search_news(keywords: str):
    """Search for news articles by keywords.
    
    Args:
        keywords: Comma-separated keywords to search for
    """
    try:
        dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
        
        # In dry_run mode, return mock news articles
        if dry_run:
            import random
            from datetime import timedelta
            
            keyword_list = [k.strip().lower() for k in keywords.split(",")]
            now = datetime.utcnow()
            
            # Generate realistic mock articles based on keywords
            mock_articles = []
            num_articles = random.randint(5, 12)
            
            # Create articles with content related to keywords
            for i in range(num_articles):
                keyword = random.choice(keyword_list) if keyword_list else "market"
                
                # Generate realistic titles and descriptions based on keyword
                titles = {
                    "xrp": [
                        f"XRP Price Analysis: {keyword.upper()} Shows Strong Momentum",
                        f"{keyword.upper()} Adoption Increases as Major Exchanges Add Support",
                        f"Ripple's {keyword.upper()} Gains Regulatory Clarity",
                        f"{keyword.upper()} Trading Volume Surges Amid Market Optimism",
                    ],
                    "bitcoin": [
                        f"Bitcoin Reaches New Highs as {keyword.upper()} Demand Grows",
                        f"{keyword.upper()} Institutional Adoption Accelerates",
                        f"Bitcoin {keyword.upper()} Market Shows Resilience",
                    ],
                    "crypto": [
                        f"Crypto Market Update: {keyword.upper()} Trends",
                        f"{keyword.upper()} Cryptocurrency Regulation Developments",
                        f"Major {keyword.upper()} Crypto Projects Announce Updates",
                    ],
                }
                
                # Find matching title templates
                title_templates = []
                for k, templates in titles.items():
                    if k in keyword_list:
                        title_templates.extend(templates)
                
                if not title_templates:
                    title_templates = [
                        f"{keyword.upper()} Market Analysis: Key Trends and Developments",
                        f"Latest Updates on {keyword.upper()} Trading and Investment",
                        f"{keyword.upper()} Shows Promising Growth Potential",
                    ]
                
                title = random.choice(title_templates)
                
                descriptions = [
                    f"Recent developments in {keyword} markets show significant activity and investor interest.",
                    f"Analysis of {keyword} trends reveals interesting patterns and potential opportunities.",
                    f"Market experts weigh in on the future of {keyword} and its impact on trading.",
                    f"Breaking news: {keyword} sees major developments that could affect market dynamics.",
                ]
                
                sources = [
                    {"id": "reuters", "name": "Reuters"},
                    {"id": "bloomberg", "name": "Bloomberg"},
                    {"id": "coindesk", "name": "CoinDesk"},
                    {"id": "cointelegraph", "name": "Cointelegraph"},
                    {"id": "the-block", "name": "The Block"},
                    {"id": "decrypt", "name": "Decrypt"},
                ]
                
                source = random.choice(sources)
                authors = ["John Smith", "Sarah Johnson", "Michael Chen", "Emily Davis", "David Wilson"]
                
                # Generate random publish date (within last 7 days)
                hours_ago = random.randint(1, 168)  # 1 hour to 7 days ago
                published_at = (now - timedelta(hours=hours_ago)).isoformat()
                
                article_dict = {
                    "source": source,
                    "author": random.choice(authors),
                    "title": title,
                    "description": random.choice(descriptions),
                    "url": f"https://example.com/news/{keyword}-{i}",
                    "urlToImage": f"https://picsum.photos/400/300?random={i}",
                    "publishedAt": published_at,
                    "content": f"Full article content about {keyword} and related market developments. This is mock content for testing purposes in dry_run mode.",
                }
                mock_articles.append(article_dict)
            
            return {
                "articles": mock_articles,
                "count": len(mock_articles),
                "keywords": keywords,
                "dry_run": True,
            }
        
        # Live mode - use real NewsAPI
        # Check if NewsAPI key is configured
        if not os.getenv("NEWSAPI_API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NewsAPI API key not configured. Set NEWSAPI_API_KEY in .env file."
            )
        
        articles = news_client.get_articles_for_cli_keywords(keywords)
        
        # Convert Article objects to dictionaries
        articles_data = []
        for article in articles:
            article_dict = {
                "source": {
                    "id": article.source.id if article.source else None,
                    "name": article.source.name if article.source else None,
                } if article.source else None,
                "author": article.author,
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "urlToImage": article.urlToImage,
                "publishedAt": article.publishedAt,
                "content": article.content,
            }
            articles_data.append(article_dict)
        
        return {
            "articles": articles_data,
            "count": len(articles_data),
            "keywords": keywords,
            "dry_run": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search news: {str(e)}"
        )


@app.post("/api/debug/clear-all")
async def clear_all_records():
    """Clear all records from the database. Use with caution!
    
    This will delete all forecasts, trades, and portfolio snapshots.
    """
    try:
        result = db.clear_all_records()
        logger.warning(f"All records cleared: {result}")
        
        # Broadcast to all WebSocket clients that data was cleared
        # Send empty portfolio
        await broadcaster.broadcast("portfolio_updated", {
            "balance": 0.0,
            "total_value": 0.0,
            "open_positions": 0,
            "total_pnl": 0.0,
            "win_rate": None,
            "total_trades": 0,
            "created_at": datetime.utcnow().isoformat(),
        })
        
        # Also send a reset message
        await broadcaster.broadcast("data_cleared", result)
        
        return {
            "status": "success",
            "message": "All records cleared successfully",
            **result,
        }
    except Exception as e:
        logger.error(f"Failed to clear records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear records: {str(e)}"
        )


def main():
    """Start the FastAPI server (production mode)."""
    import uvicorn
    import signal
    import sys
    
    # Custom logging filter to suppress shutdown-related errors
    class ShutdownErrorFilter(logging.Filter):
        def filter(self, record):
            # Suppress CancelledError and timeout exceeded messages
            msg = str(record.msg)
            if "CancelledError" in msg or "timeout graceful shutdown exceeded" in msg:
                return False
            if "Exception in ASGI application" in msg and hasattr(record, 'exc_info') and record.exc_info:
                exc_type = record.exc_info[0] if record.exc_info[0] else None
                if exc_type and exc_type.__name__ == "CancelledError":
                    return False
            return True
    
    # Apply filter to uvicorn error logger
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(ShutdownErrorFilter())
    
    # Configure uvicorn with timeout settings for faster shutdown
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        timeout_graceful_shutdown=2,  # Wait max 2 seconds for graceful shutdown
        log_level="info",
    )
    server = uvicorn.Server(config)
    
    # Handle SIGINT (Ctrl+C) to ensure clean shutdown
    shutdown_initiated = False
    def handle_sigint(signum, frame):
        nonlocal shutdown_initiated
        if not shutdown_initiated:
            logger.info("Received SIGINT (Ctrl+C), initiating shutdown...")
            shutdown_initiated = True
            server.should_exit = True
        else:
            # Force quit on second Ctrl+C
            logger.warning("Force quit...")
            sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_sigint)
    
    server.run()


def dev():
    """Start the FastAPI server with hot reload (development mode)."""
    import uvicorn
    
    # Custom logging filter to suppress shutdown-related errors
    class ShutdownErrorFilter(logging.Filter):
        def filter(self, record):
            # Suppress CancelledError and timeout exceeded messages
            msg = str(record.msg)
            if "CancelledError" in msg or "timeout graceful shutdown exceeded" in msg:
                return False
            if "Exception in ASGI application" in msg and hasattr(record, 'exc_info') and record.exc_info:
                exc_type = record.exc_info[0] if record.exc_info[0] else None
                if exc_type and exc_type.__name__ == "CancelledError":
                    return False
            return True
    
    # Apply filter to uvicorn error logger
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(ShutdownErrorFilter())
    
    uvicorn.run(
        "scripts.python.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["agents/"],
        timeout_graceful_shutdown=2,  # Wait max 2 seconds for graceful shutdown
        log_level="info",
    )


if __name__ == "__main__":
    main()
