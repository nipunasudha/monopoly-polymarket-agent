"""
SQLite database persistence layer for Monopoly agents.
Stores forecasts, trades, and portfolio snapshots.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import asyncio

Base = declarative_base()


class ForecastRecord(Base):
    """Store forecast predictions."""
    
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, nullable=False, index=True)
    market_question = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    base_rate = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    evidence_for = Column(Text, nullable=True)  # JSON string
    evidence_against = Column(Text, nullable=True)  # JSON string
    key_factors = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "market_id": self.market_id,
            "market_question": self.market_question,
            "outcome": self.outcome,
            "probability": self.probability,
            "confidence": self.confidence,
            "base_rate": self.base_rate,
            "reasoning": self.reasoning,
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "key_factors": self.key_factors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TradeRecord(Base):
    """Store trade execution records."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, nullable=False, index=True)
    market_question = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY or SELL
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    forecast_probability = Column(Float, nullable=False)
    edge = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, executed, failed
    execution_enabled = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    transaction_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "market_id": self.market_id,
            "market_question": self.market_question,
            "outcome": self.outcome,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "forecast_probability": self.forecast_probability,
            "edge": self.edge,
            "status": self.status,
            "execution_enabled": self.execution_enabled,
            "error_message": self.error_message,
            "transaction_hash": self.transaction_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class PortfolioSnapshot(Base):
    """Store portfolio state snapshots."""
    
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    open_positions = Column(Integer, nullable=False, default=0)
    total_pnl = Column(Float, nullable=False, default=0.0)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=False, default=0)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "balance": self.balance,
            "total_value": self.total_value,
            "open_positions": self.open_positions,
            "total_pnl": self.total_pnl,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Database:
    """Database manager for agent persistence."""
    
    def __init__(self, database_url: str = None):
        """Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite file in project root.
        """
        if database_url is None:
            # Use absolute path to project root (agents/../monopoly_agents.db)
            from pathlib import Path
            # From agents/agents/connectors/database.py go up 3 levels to project root
            db_path = Path(__file__).parent.parent.parent.parent / "monopoly_agents.db"
            database_url = f"sqlite:///{db_path}"
        
        # For SQLite, we need to allow same thread to be False for async usage
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, echo=False, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        
    def drop_tables(self):
        """Drop all tables. Use with caution!"""
        Base.metadata.drop_all(self.engine)
        
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Forecast operations
    
    def save_forecast(self, forecast_data: dict) -> ForecastRecord:
        """Save a forecast to the database.
        
        Args:
            forecast_data: Dictionary with forecast data
            
        Returns:
            ForecastRecord: Saved forecast record
        """
        with self.get_session() as session:
            forecast = ForecastRecord(**forecast_data)
            session.add(forecast)
            session.flush()
            session.refresh(forecast)
            # Expunge to detach from session so it can be used after session closes
            session.expunge(forecast)
            
            # Emit event for realtime updates
            self._emit_forecast_created(forecast)
            
            return forecast
    
    def _emit_forecast_created(self, forecast: ForecastRecord):
        """Emit forecast created event (non-blocking)."""
        try:
            from agents.connectors.events import get_broadcaster
            broadcaster = get_broadcaster()
            asyncio.create_task(broadcaster.emit_forecast_created(forecast.to_dict()))
        except Exception:
            # Don't fail database operation if event emission fails
            pass
    
    def get_forecast(self, forecast_id: int) -> Optional[ForecastRecord]:
        """Get a forecast by ID.
        
        Args:
            forecast_id: Forecast ID
            
        Returns:
            ForecastRecord or None
        """
        with self.get_session() as session:
            forecast = session.query(ForecastRecord).filter_by(id=forecast_id).first()
            if forecast:
                session.expunge(forecast)
            return forecast
    
    def get_forecasts_by_market(self, market_id: str) -> List[ForecastRecord]:
        """Get all forecasts for a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            List of ForecastRecord
        """
        with self.get_session() as session:
            forecasts = session.query(ForecastRecord).filter_by(market_id=market_id).all()
            for forecast in forecasts:
                session.expunge(forecast)
            return forecasts
    
    def get_recent_forecasts(self, limit: int = 10) -> List[ForecastRecord]:
        """Get most recent forecasts.
        
        Args:
            limit: Maximum number of forecasts to return
            
        Returns:
            List of ForecastRecord
        """
        with self.get_session() as session:
            forecasts = (
                session.query(ForecastRecord)
                .order_by(ForecastRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            for forecast in forecasts:
                session.expunge(forecast)
            return forecasts
    
    # Trade operations
    
    def save_trade(self, trade_data: dict) -> TradeRecord:
        """Save a trade to the database.
        
        Args:
            trade_data: Dictionary with trade data
            
        Returns:
            TradeRecord: Saved trade record
        """
        with self.get_session() as session:
            trade = TradeRecord(**trade_data)
            session.add(trade)
            session.flush()
            session.refresh(trade)
            session.expunge(trade)
            
            # Emit event for realtime updates
            self._emit_trade_executed(trade)
            
            return trade
    
    def _emit_trade_executed(self, trade: TradeRecord):
        """Emit trade executed event (non-blocking)."""
        try:
            from agents.connectors.events import get_broadcaster
            broadcaster = get_broadcaster()
            asyncio.create_task(broadcaster.emit_trade_executed(trade.to_dict()))
        except Exception:
            pass
    
    def get_trade(self, trade_id: int) -> Optional[TradeRecord]:
        """Get a trade by ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            TradeRecord or None
        """
        with self.get_session() as session:
            trade = session.query(TradeRecord).filter_by(id=trade_id).first()
            if trade:
                session.expunge(trade)
            return trade
    
    def get_trades_by_market(self, market_id: str) -> List[TradeRecord]:
        """Get all trades for a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            List of TradeRecord
        """
        with self.get_session() as session:
            trades = session.query(TradeRecord).filter_by(market_id=market_id).all()
            for trade in trades:
                session.expunge(trade)
            return trades
    
    def get_recent_trades(self, limit: int = 10) -> List[TradeRecord]:
        """Get most recent trades.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of TradeRecord
        """
        with self.get_session() as session:
            trades = (
                session.query(TradeRecord)
                .order_by(TradeRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            for trade in trades:
                session.expunge(trade)
            return trades
    
    def update_trade_status(
        self, trade_id: int, status: str, executed_at: Optional[datetime] = None,
        transaction_hash: Optional[str] = None, error_message: Optional[str] = None
    ) -> Optional[TradeRecord]:
        """Update trade status.
        
        Args:
            trade_id: Trade ID
            status: New status
            executed_at: Execution timestamp
            transaction_hash: Transaction hash if executed
            error_message: Error message if failed
            
        Returns:
            Updated TradeRecord or None
        """
        with self.get_session() as session:
            trade = session.query(TradeRecord).filter_by(id=trade_id).first()
            if trade:
                trade.status = status
                if executed_at:
                    trade.executed_at = executed_at
                if transaction_hash:
                    trade.transaction_hash = transaction_hash
                if error_message:
                    trade.error_message = error_message
                session.flush()
                session.refresh(trade)
                session.expunge(trade)
            return trade
    
    # Portfolio operations
    
    def save_portfolio_snapshot(self, snapshot_data: dict) -> PortfolioSnapshot:
        """Save a portfolio snapshot.
        
        Args:
            snapshot_data: Dictionary with portfolio data
            
        Returns:
            PortfolioSnapshot: Saved snapshot
        """
        with self.get_session() as session:
            snapshot = PortfolioSnapshot(**snapshot_data)
            session.add(snapshot)
            session.flush()
            session.refresh(snapshot)
            session.expunge(snapshot)
            
            # Emit event for realtime updates
            self._emit_portfolio_updated(snapshot)
            
            return snapshot
    
    def _emit_portfolio_updated(self, snapshot: PortfolioSnapshot):
        """Emit portfolio updated event (non-blocking)."""
        try:
            from agents.connectors.events import get_broadcaster
            broadcaster = get_broadcaster()
            asyncio.create_task(broadcaster.emit_portfolio_updated(snapshot.to_dict()))
        except Exception:
            pass
    
    def get_latest_portfolio_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Get the most recent portfolio snapshot.
        
        Returns:
            PortfolioSnapshot or None
        """
        with self.get_session() as session:
            snapshot = (
                session.query(PortfolioSnapshot)
                .order_by(PortfolioSnapshot.created_at.desc())
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot
    
    def get_portfolio_history(self, limit: int = 30) -> List[PortfolioSnapshot]:
        """Get portfolio history.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of PortfolioSnapshot
        """
        with self.get_session() as session:
            snapshots = (
                session.query(PortfolioSnapshot)
                .order_by(PortfolioSnapshot.created_at.desc())
                .limit(limit)
                .all()
            )
            for snapshot in snapshots:
                session.expunge(snapshot)
            return snapshots
