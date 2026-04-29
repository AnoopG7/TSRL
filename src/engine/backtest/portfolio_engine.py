"""
Portfolio Engine
Responsibilities:
- Multi-symbol portfolio backtesting with capital allocation
- Position sizing and allocation across multiple strategies
- Rebalancing logic (daily, weekly, monthly, quarterly)
- Portfolio-level metrics calculation (correlation, risk contribution)
- Benchmark comparison (beta, alpha calculation)

Used by:
- BacktestService (for portfolio backtests)
- CLI portfolio command
- API /backtest/portfolio endpoint

Notes:
- PortfolioConfig extends BacktestConfig with allocation weights
- PortfolioBacktestEngine handles single-strategy multi-symbol
- MultiStrategyPortfolioEngine handles multiple strategies
- RebalanceEvent tracks when and why rebalancing occurred
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.engine.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from src.domain.entities.rebalance_event import RebalanceEvent
from src.domain.entities.portfolio_metrics import PortfolioMetrics

logger = logging.getLogger(__name__)


class RebalanceFrequency(str, Enum):
    """Rebalancing frequency options."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PortfolioConfig:
    initial_capital: float = 100000.0
    max_position_size: float = 0.2
    max_positions: int = 5
    commission: float = 0.001
    slippage: float = 0.0005

    # Allocation weights - if None, use equal weighting (backward compatible)
    weights: Optional[dict[str, float]] = None

    # Rebalancing settings
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.NONE
    rebalance_threshold: Optional[float] = None  # e.g., 0.05 = 5% drift triggers rebalance

    # Benchmark for beta/alpha calculation
    benchmark_symbol: Optional[str] = None

    def __post_init__(self):
        """Validate weights sum to 1.0 if provided."""
        if self.weights is not None:
            total = sum(self.weights.values())
            if not (0.99 <= total <= 1.01):  # Allow small float tolerance
                raise ValueError(f"Weights must sum to 1.0, got {total}")

        # Convert string to enum if needed
        if isinstance(self.rebalance_frequency, str):
            self.rebalance_frequency = RebalanceFrequency(self.rebalance_frequency)


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

    # Weights used for allocation
    weights: dict[str, float] = field(default_factory=dict)

    # Rebalancing history
    rebalance_events: list[RebalanceEvent] = field(default_factory=list)
    total_rebalance_cost: float = 0.0

    # Portfolio-specific metrics
    portfolio_metrics: Optional[PortfolioMetrics] = None

    # Per-asset equity curves (for visualization)
    asset_equity_curves: dict[str, pd.DataFrame] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbols": self.symbols,
            "weights": self.weights,
            "total_return": round(self.total_return, 4),
            "total_trades": self.total_trades,
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "win_rate": round(self.win_rate, 4),
            "execution_time_ms": round(self.execution_time_ms, 2),
            "rebalance_events": [e.to_dict() for e in self.rebalance_events],
            "total_rebalance_cost": round(self.total_rebalance_cost, 2),
            "portfolio_metrics": self.portfolio_metrics.to_dict() if self.portfolio_metrics else None,
        }


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


class EnhancedPortfolioBacktestEngine(PortfolioMetricsMixin):
    """Portfolio backtest engine with weighted allocation and rebalancing."""

    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()

    def run(
        self,
        strategy: BaseStrategy,
        symbols_data: dict[str, pd.DataFrame],
        benchmark_data: Optional[pd.DataFrame] = None,
        config: Optional[PortfolioConfig] = None,
    ) -> PortfolioResult:
        """
        Run portfolio backtest with weighted allocation and optional rebalancing.

        Args:
            strategy: Strategy to apply to all symbols
            symbols_data: Dict mapping symbol -> OHLCV DataFrame
            benchmark_data: Optional benchmark data for beta/alpha calculation
            config: Portfolio configuration (overrides instance config)

        Returns:
            PortfolioResult with detailed metrics and rebalancing history
        """
        cfg = config or self.config
        start_time = datetime.now()

        # 1. Determine weights
        weights = self._get_weights(cfg, list(symbols_data.keys()))

        # 2. Align all data to common date range
        aligned_data = self._align_data(symbols_data)

        # 3. Run backtests with weighted capital allocation
        results, all_trades = self._run_weighted_backtests(strategy, aligned_data, weights, cfg)

        # 4. Apply rebalancing if configured
        combined_equity, rebalance_events = self._apply_rebalancing(
            results, aligned_data, weights, cfg
        )

        # 5. Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            results, aligned_data, benchmark_data, weights
        )

        # 6. Calculate aggregate metrics
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
            weights=weights,
            rebalance_events=rebalance_events,
            total_rebalance_cost=sum(e.total_cost for e in rebalance_events),
            portfolio_metrics=portfolio_metrics,
            asset_equity_curves={s: r.equity_curve for s, r in results.items()},
        )

    def _get_weights(self, cfg: PortfolioConfig, symbols: list[str]) -> dict[str, float]:
        """Get allocation weights - use provided or equal weight."""
        if cfg.weights:
            missing = set(symbols) - set(cfg.weights.keys())
            if missing:
                raise ValueError(f"Missing weights for symbols: {missing}")
            return {s: cfg.weights[s] for s in symbols}
        else:
            weight = 1.0 / len(symbols)
            return {s: weight for s in symbols}

    def _align_data(self, symbols_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Align all symbol data to common date range."""
        common_dates = None
        for symbol, data in symbols_data.items():
            if common_dates is None:
                common_dates = set(data.index)
            else:
                common_dates &= set(data.index)

        if not common_dates:
            # No common dates - try to align by date range instead
            # Find overlapping date range
            min_dates = [data.index.min() for data in symbols_data.values()]
            max_dates = [data.index.max() for data in symbols_data.values()]
            start_date = max(min_dates)
            end_date = min(max_dates)

            if start_date >= end_date:
                raise ValueError("No overlapping date range found across symbols")

            # Filter each dataset to the common range
            aligned = {}
            for symbol, data in symbols_data.items():
                mask = (data.index >= start_date) & (data.index <= end_date)
                aligned[symbol] = data.loc[mask].copy()

            # Find common dates after filtering
            common_dates = None
            for symbol, data in aligned.items():
                if common_dates is None:
                    common_dates = set(data.index)
                else:
                    common_dates &= set(data.index)

            if not common_dates:
                # Still no common dates - just use all data as-is (may have gaps)
                logger.warning("No common dates found, using full data ranges")
                return symbols_data

            common_dates = sorted(common_dates)
            return {symbol: data.loc[common_dates].copy() for symbol, data in aligned.items()}

        common_dates = sorted(common_dates)
        return {symbol: data.loc[common_dates].copy() for symbol, data in symbols_data.items()}

    def _run_weighted_backtests(
        self,
        strategy: BaseStrategy,
        aligned_data: dict[str, pd.DataFrame],
        weights: dict[str, float],
        cfg: PortfolioConfig,
    ) -> tuple[dict[str, BacktestResult], list]:
        """Run backtests with weighted capital allocation."""
        results = {}
        all_trades = []

        for symbol, data in aligned_data.items():
            weight = weights[symbol]
            allocated_capital = cfg.initial_capital * weight

            bt_config = BacktestConfig(
                initial_capital=allocated_capital,
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

        return results, all_trades

    def _apply_rebalancing(
        self,
        results: dict[str, BacktestResult],
        aligned_data: dict[str, pd.DataFrame],
        target_weights: dict[str, float],
        cfg: PortfolioConfig,
    ) -> tuple[pd.DataFrame, list[RebalanceEvent]]:
        """Apply rebalancing logic and return adjusted equity curve."""
        if cfg.rebalance_frequency == RebalanceFrequency.NONE and cfg.rebalance_threshold is None:
            return self._combine_equity_curves(results), []

        rebalance_dates = self._get_rebalance_dates(aligned_data, cfg.rebalance_frequency)
        rebalance_events = []

        all_dates = sorted(
            set().union(*[set(r.equity_curve.index) for r in results.values() if not r.equity_curve.empty])
        )

        if not all_dates:
            return pd.DataFrame(), []

        holdings = {s: cfg.initial_capital * target_weights[s] for s in results.keys()}
        equity_history = []

        for i, date in enumerate(all_dates):
            current_values = {}
            for symbol, result in results.items():
                if not result.equity_curve.empty and date in result.equity_curve.index:
                    eq_col = "equity" if "equity" in result.equity_curve.columns else "total"
                    current_values[symbol] = result.equity_curve.loc[date, eq_col]
                else:
                    current_values[symbol] = holdings[symbol]

            total_value = sum(current_values.values())
            if total_value <= 0:
                continue

            current_weights = {s: v / total_value for s, v in current_values.items()}
            should_rebalance = False
            reason = ""

            if date in rebalance_dates:
                should_rebalance = True
                reason = "periodic"

            if cfg.rebalance_threshold:
                max_drift = max(
                    abs(current_weights.get(s, 0) - target_weights.get(s, 0)) for s in current_weights
                )
                if max_drift > cfg.rebalance_threshold:
                    should_rebalance = True
                    reason = f"threshold ({max_drift:.2%} drift)"

            if should_rebalance and i > 0:
                new_values = {s: total_value * target_weights[s] for s in holdings}
                trades_needed = sum(
                    1 for s in holdings if abs(new_values[s] - current_values.get(s, 0)) > 0.01
                )
                value_traded = sum(abs(new_values[s] - current_values.get(s, 0)) for s in holdings)
                rebalance_cost = value_traded * cfg.commission

                rebalance_events.append(
                    RebalanceEvent(
                        timestamp=date,
                        reason=reason,
                        pre_weights=current_weights.copy(),
                        pre_values=current_values.copy(),
                        target_weights=target_weights.copy(),
                        post_values=new_values.copy(),
                        trades_executed=trades_needed,
                        total_cost=rebalance_cost,
                    )
                )
                holdings = new_values
                total_value -= rebalance_cost
            else:
                holdings = current_values

            equity_history.append({"timestamp": date, "total": total_value, **holdings})

        if not equity_history:
            return pd.DataFrame(), rebalance_events

        equity_df = pd.DataFrame(equity_history).set_index("timestamp")
        return equity_df, rebalance_events

    def _get_rebalance_dates(
        self,
        aligned_data: dict[str, pd.DataFrame],
        frequency: RebalanceFrequency,
    ) -> set:
        """Get dates when periodic rebalancing should occur."""
        if frequency == RebalanceFrequency.NONE:
            return set()

        sample_data = next(iter(aligned_data.values()))
        dates = pd.DatetimeIndex(sample_data.index)

        if frequency == RebalanceFrequency.DAILY:
            return set(dates)
        elif frequency == RebalanceFrequency.WEEKLY:
            return set(dates.to_series().groupby(dates.isocalendar().week).first())
        elif frequency == RebalanceFrequency.MONTHLY:
            return set(dates.to_series().groupby([dates.year, dates.month]).first())
        elif frequency == RebalanceFrequency.QUARTERLY:
            return set(dates.to_series().groupby([dates.year, dates.quarter]).first())
        elif frequency == RebalanceFrequency.YEARLY:
            return set(dates.to_series().groupby(dates.year).first())
        return set()

    def _calculate_portfolio_metrics(
        self,
        results: dict[str, BacktestResult],
        aligned_data: dict[str, pd.DataFrame],
        benchmark_data: Optional[pd.DataFrame],
        weights: dict[str, float],
    ) -> Optional[PortfolioMetrics]:
        """Calculate portfolio-specific metrics."""
        try:
            from src.analytics.portfolio_metrics import PortfolioMetricsCalculator

            # Calculate returns for each asset
            asset_returns_dict = {}
            for symbol, data in aligned_data.items():
                asset_returns_dict[symbol] = data["close"].pct_change().dropna()

            # Align returns to common dates using DataFrame
            returns_df = pd.DataFrame(asset_returns_dict)

            # Drop rows where any asset has NaN (keep only dates with all assets)
            returns_df = returns_df.dropna()

            if returns_df.empty or len(returns_df) < 2:
                logger.warning("Insufficient aligned returns data for portfolio metrics")
                return None

            # Convert back to dict of Series for calculator
            asset_returns = {col: returns_df[col] for col in returns_df.columns}

            benchmark_returns = None
            if benchmark_data is not None and "close" in benchmark_data.columns:
                bench_ret = benchmark_data["close"].pct_change().dropna()
                # Align benchmark to same dates
                if not returns_df.empty:
                    common_dates = returns_df.index.intersection(bench_ret.index)
                    if len(common_dates) > 20:
                        benchmark_returns = bench_ret.loc[common_dates]

            return PortfolioMetricsCalculator.calculate_all(
                asset_returns=asset_returns,
                weights=weights,
                benchmark_returns=benchmark_returns,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate portfolio metrics: {e}")
            return None
