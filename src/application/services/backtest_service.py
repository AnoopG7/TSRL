import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.application.services.data_service import DataService
from src.engine.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from src.strategies.registry import StrategyRegistry
from src.infrastructure.database.connection import get_session_factory
from src.infrastructure.database.repositories.backtest_repository import (
    BacktestRepository,
    TradeRepository,
)

logger = logging.getLogger(__name__)


@dataclass
class BacktestResponse:
    """Serializable backtest result for API responses."""

    backtest_id: Optional[int] = None
    strategy: str = ""
    symbol: str = ""
    data_source: str = "live"
    final_capital: float = 0.0
    total_return: float = 0.0
    total_trades: int = 0
    metrics: dict = field(default_factory=dict)
    execution_time_ms: float = 0.0
    equity_curve: list = field(default_factory=list)
    drawdown_series: list = field(default_factory=list)
    monthly_returns: list = field(default_factory=list)
    trades: list = field(default_factory=list)


class BacktestService:
    """Orchestrates backtesting: data fetch → strategy → engine → persistence → response."""

    def __init__(self):
        self.data_service = DataService()

    def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1d",
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        parameters: Optional[dict] = None,
    ) -> BacktestResponse:
        """Run a single backtest and return full results including chart data."""

        # Create strategy
        strategy = StrategyRegistry.create(strategy_name, **(parameters or {}))
        if strategy is None:
            raise ValueError(f"Strategy '{strategy_name}' not found")

        # Fetch data
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        df, data_source = self.data_service.fetch_data(symbol, start_dt, end_dt, timeframe)

        # Configure and run engine
        config = BacktestConfig(
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage,
        )
        engine = BacktestEngine(config)
        result = engine.run(strategy, df)

        # Extract chart data
        equity_curve = self._extract_equity_curve(result)
        drawdown_series = self._extract_drawdown(result)
        monthly_returns = self._extract_monthly_returns(result)

        # Persist to database
        backtest_id = self._persist_result(
            result, strategy_name, symbol, start_dt, end_dt,
            initial_capital, timeframe, commission, slippage,
        )

        # Build response
        trades_list = [t.to_dict() for t in result.trades[:50]]

        return BacktestResponse(
            backtest_id=backtest_id,
            strategy=strategy_name,
            symbol=symbol,
            data_source=data_source,
            final_capital=result.final_capital,
            total_return=result.total_return,
            total_trades=len(result.trades),
            metrics=result.metrics.to_dict(),
            execution_time_ms=result.execution_time_ms,
            equity_curve=equity_curve,
            drawdown_series=drawdown_series,
            monthly_returns=monthly_returns,
            trades=trades_list,
        )

    def compare_strategies(
        self,
        strategy_names: list[str],
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1d",
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ) -> dict:
        """Run backtests for multiple strategies on the same data and return comparison."""

        # Fetch data once
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        df, data_source = self.data_service.fetch_data(symbol, start_dt, end_dt, timeframe)

        config = BacktestConfig(
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage,
        )

        results = {}
        for name in strategy_names:
            strategy = StrategyRegistry.create(name)
            if strategy is None:
                logger.warning(f"Strategy '{name}' not found, skipping")
                continue

            engine = BacktestEngine(config)
            result = engine.run(strategy, df)

            results[name] = {
                "strategy": name,
                "final_capital": result.final_capital,
                "total_return": result.total_return,
                "total_trades": len(result.trades),
                "metrics": result.metrics.to_dict(),
                "execution_time_ms": result.execution_time_ms,
                "equity_curve": self._extract_equity_curve(result),
                "drawdown_series": self._extract_drawdown(result),
            }

        return {
            "symbol": symbol,
            "data_source": data_source,
            "initial_capital": initial_capital,
            "strategies": results,
        }

    def _extract_equity_curve(self, result: BacktestResult) -> list[dict]:
        """Extract equity curve as list of {date, equity} dicts."""
        if result.equity_curve is None or result.equity_curve.empty:
            return []

        ec = result.equity_curve
        points = []
        for idx, row in ec.iterrows():
            date_str = str(idx)
            if hasattr(idx, "isoformat"):
                date_str = idx.isoformat()
            equity_val = row.get("equity", row.get("total", 0))
            if pd.notna(equity_val):
                points.append({"date": date_str, "equity": round(float(equity_val), 2)})
        return points

    def _extract_drawdown(self, result: BacktestResult) -> list[dict]:
        """Extract drawdown series as list of {date, drawdown} dicts."""
        if result.equity_curve is None or result.equity_curve.empty:
            return []

        ec = result.equity_curve
        equity_col = "equity" if "equity" in ec.columns else "total"
        if equity_col not in ec.columns:
            return []

        equity = ec[equity_col]
        running_max = equity.cummax()
        drawdown = ((equity - running_max) / running_max * 100)

        points = []
        for idx, dd_val in drawdown.items():
            date_str = str(idx)
            if hasattr(idx, "isoformat"):
                date_str = idx.isoformat()
            if pd.notna(dd_val):
                points.append({"date": date_str, "drawdown": round(float(dd_val), 2)})
        return points

    def _extract_monthly_returns(self, result: BacktestResult) -> list[dict]:
        """Extract monthly returns as list of {year, month, return_pct} dicts."""
        if result.equity_curve is None or result.equity_curve.empty:
            return []

        ec = result.equity_curve
        equity_col = "equity" if "equity" in ec.columns else "total"
        if equity_col not in ec.columns:
            return []

        equity = ec[equity_col]
        try:
            monthly = equity.resample("ME").last()
            monthly_ret = monthly.pct_change().dropna()
        except Exception:
            return []

        points = []
        for idx, ret in monthly_ret.items():
            if pd.notna(ret):
                points.append({
                    "year": idx.year,
                    "month": idx.month,
                    "return_pct": round(float(ret * 100), 2),
                })
        return points

    def _persist_result(
        self,
        result: BacktestResult,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        timeframe: str,
        commission: float,
        slippage: float,
    ) -> Optional[int]:
        """Persist backtest result to database. Returns backtest_id or None."""
        try:
            session_factory = get_session_factory()
            session = session_factory()
            backtest_repo = BacktestRepository(session=session)
            trade_repo = TradeRepository(session=session)

            try:
                backtest = backtest_repo.create(
                    name=f"{strategy_name}_{symbol}",
                    symbol=symbol,
                    strategy_name=strategy_name,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    config={
                        "timeframe": timeframe,
                        "commission": commission,
                        "slippage": slippage,
                    },
                )

                winning = sum(1 for t in result.trades if t.pnl is not None and t.pnl > 0)
                losing = sum(1 for t in result.trades if t.pnl is not None and t.pnl <= 0)

                backtest_repo.update_results(
                    backtest_id=backtest.id,
                    final_capital=result.final_capital,
                    total_return=result.total_return,
                    total_trades=len(result.trades),
                    winning_trades=winning,
                    losing_trades=losing,
                    metrics=result.metrics.to_dict(),
                )

                for trade in result.trades:
                    trade_repo.create(
                        backtest_id=backtest.id,
                        symbol=symbol,
                        entry_time=trade.entry_time,
                        entry_price=trade.entry_price,
                        quantity=trade.quantity,
                        side=trade.side.value if hasattr(trade.side, "value") else str(trade.side),
                    )

                return backtest.id

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to persist backtest: {e}")
                return None
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
