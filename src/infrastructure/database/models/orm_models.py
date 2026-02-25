from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from src.infrastructure.database.connection import Base


class Timeframe(Base):
    __tablename__ = "timeframes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(10), unique=True, nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    ohlcv_data = relationship("OHLCV", back_populates="timeframe")


class Symbol(Base):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))
    exchange = Column(String(20))
    currency = Column(String(3), default="USD")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ohlcv_data = relationship("OHLCV", back_populates="symbol")
    backtests = relationship("Backtest", back_populates="symbol")
    trades = relationship("Trade", back_populates="symbol")


class OHLCV(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    timeframe_id = Column(Integer, ForeignKey("timeframes.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(String(20), default="yahoo")
    validated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    symbol = relationship("Symbol", back_populates="ohlcv_data")
    timeframe = relationship("Timeframe", back_populates="ohlcv_data")

    __table_args__ = (
        Index(
            "ix_ohlcv_symbol_timeframe_timestamp",
            "symbol_id",
            "timeframe_id",
            "timestamp",
            unique=True,
        ),
    )


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(20), default="1.0.0")
    strategy_type = Column(String(50), nullable=False)
    description = Column(Text)
    parameters_schema = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    backtests = relationship("Backtest", back_populates="strategy")


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float)
    total_return = Column(Float)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    config_json = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    symbol = relationship("Symbol", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest")
    signals = relationship("Signal", back_populates="backtest")
    equity_curve = relationship("EquityCurvePoint", back_populates="backtest")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)
    pnl = Column(Float)
    pnl_pct = Column(Float)
    commission = Column(Float, default=0)
    slippage = Column(Float, default=0)
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    backtest = relationship("Backtest", back_populates="trades")
    symbol = relationship("Symbol", back_populates="trades")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    signal_type = Column(String(20), nullable=False)
    strength = Column(Float)
    price = Column(Float, nullable=False)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    backtest = relationship("Backtest", back_populates="signals")


class EquityCurvePoint(Base):
    __tablename__ = "equity_curve"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    equity = Column(Float, nullable=False)
    returns = Column(Float)
    drawdown = Column(Float)

    backtest = relationship("Backtest", back_populates="equity_curve")


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)
    params_json = Column(Text, nullable=False)
    sharpe = Column(Float)
    sortino = Column(Float)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)
    feature_columns_json = Column(Text)
    target_column = Column(String(50))
    trained_at = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float)
    f1_score = Column(Float)
    sharpe = Column(Float)
    model_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text)


class WalkForwardResult(Base):
    __tablename__ = "walk_forward_results"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    train_start = Column(DateTime, nullable=False)
    train_end = Column(DateTime, nullable=False)
    test_start = Column(DateTime, nullable=False)
    test_end = Column(DateTime, nullable=False)
    train_sharpe = Column(Float)
    test_sharpe = Column(Float)
    train_return = Column(Float)
    test_return = Column(Float)
    train_drawdown = Column(Float)
    test_drawdown = Column(Float)
    params_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
