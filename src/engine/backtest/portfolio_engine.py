import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.engine.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class PortfolioConfig:
    initial_capital: float = 100000.0
    max_position_size: float = 0.2
    max_positions: int = 5
    commission: float = 0.001
    slippage: float = 0.0005
    rebalance_frequency: str = "daily"


@dataclass
class PortfolioResult:
    symbols: list[str] = field(default_factory=list)
    results: dict[str, BacktestResult] = field(default_factory=dict)
    combined_equity: pd.DataFrame = field(default_factory=pd.DataFrame)
    total_return: float = 0.0
    total_trades: int = 0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    execution_time_ms: float = 0.0


class PortfolioMetricsMixin:
    """Shared metrics calculations for portfolio engines."""

    def _combine_equity_curves(self, results: dict[str, BacktestResult]) -> pd.DataFrame:
        if not results:
            return pd.DataFrame()

        equity_dfs = []
        for name, result in results.items():
            if not result.equity_curve.empty:
                df = result.equity_curve.copy()
                df = df.rename(columns={"equity": name})
                equity_dfs.append(df[[name]])

        if not equity_dfs:
            return pd.DataFrame()

        combined = pd.concat(equity_dfs, axis=1).ffill()
        combined["total"] = combined.sum(axis=1)

        return combined

    def _calculate_total_return(self, equity_curve: pd.DataFrame, initial_capital: float) -> float:
        if equity_curve.empty or "total" not in equity_curve.columns:
            return 0.0
        return (equity_curve["total"].iloc[-1] - initial_capital) / initial_capital

    def _calculate_sharpe(self, equity_curve: pd.DataFrame) -> float:
        if equity_curve.empty or "total" not in equity_curve.columns:
            return 0.0
        returns = equity_curve["total"].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        return np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else 0.0

    def _calculate_max_drawdown(self, equity_curve: pd.DataFrame) -> float:
        if equity_curve.empty or "total" not in equity_curve.columns:
            return 0.0
        cumulative = equity_curve["total"]
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min()) if len(drawdown) > 0 else 0.0

    def _calculate_win_rate(self, trades: list) -> float:
        if not trades:
            return 0.0
        winning = sum(1 for t in trades if t.pnl and t.pnl > 0)
        return winning / len(trades) if trades else 0.0


class PortfolioBacktestEngine(PortfolioMetricsMixin):
    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()

    def run(
        self,
        strategy: BaseStrategy,
        symbols_data: dict[str, pd.DataFrame],
        config: Optional[PortfolioConfig] = None,
    ) -> PortfolioResult:
        cfg = config or self.config
        start_time = datetime.now()

        results = {}
        all_trades = []

        for symbol, data in symbols_data.items():
            logger.info(f"Running backtest for {symbol}")

            bt_config = BacktestConfig(
                initial_capital=cfg.initial_capital / len(symbols_data),
                commission=cfg.commission,
                slippage=cfg.slippage,
                max_position_size=cfg.max_position_size,
            )

            engine = BacktestEngine(bt_config)
            result = engine.run(strategy, data)

            results[symbol] = result

            for trade in result.trades:
                trade.symbol = symbol
                all_trades.append(trade)

        combined_equity = self._combine_equity_curves(results)

        total_return = self._calculate_total_return(combined_equity, cfg.initial_capital)
        sharpe = self._calculate_sharpe(combined_equity)
        max_dd = self._calculate_max_drawdown(combined_equity)
        win_rate = self._calculate_win_rate(all_trades)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return PortfolioResult(
            symbols=list(symbols_data.keys()),
            results=results,
            combined_equity=combined_equity,
            total_return=total_return,
            total_trades=len(all_trades),
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            execution_time_ms=execution_time,
        )


class MultiStrategyPortfolioEngine(PortfolioMetricsMixin):
    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()

    def run(
        self,
        strategies: dict[str, BaseStrategy],
        symbols_data: dict[str, pd.DataFrame],
    ) -> PortfolioResult:
        start_time = datetime.now()
        cfg = self.config

        results = {}
        all_trades = []

        for symbol, data in symbols_data.items():
            for strategy_name, strategy in strategies.items():
                logger.info(f"Running {strategy_name} for {symbol}")

                bt_config = BacktestConfig(
                    initial_capital=cfg.initial_capital / (len(symbols_data) * len(strategies)),
                    commission=cfg.commission,
                    slippage=cfg.slippage,
                    max_position_size=cfg.max_position_size / len(strategies),
                )

                engine = BacktestEngine(bt_config)
                result = engine.run(strategy, data)

                results[f"{strategy_name}_{symbol}"] = result

                for trade in result.trades:
                    trade.symbol = f"{strategy_name}_{symbol}"
                    all_trades.append(trade)

        combined_equity = self._combine_equity_curves(results)

        total_return = self._calculate_total_return(combined_equity, cfg.initial_capital)
        sharpe = self._calculate_sharpe(combined_equity)
        max_dd = self._calculate_max_drawdown(combined_equity)
        win_rate = self._calculate_win_rate(all_trades)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return PortfolioResult(
            symbols=list(symbols_data.keys()),
            results=results,
            combined_equity=combined_equity,
            total_return=total_return,
            total_trades=len(all_trades),
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            execution_time_ms=execution_time,
        )
