from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.domain.entities.trade import Trade, TradeSide, TradeStatus
from src.domain.entities.position import Position, PositionSide
from src.domain.entities.metrics import RiskMetrics


@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_per_trade: float = 0.02
    max_position_size: float = 0.2
    allow_shorting: bool = True
    verbose: bool = False


@dataclass
class BacktestResult:
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    metrics: RiskMetrics = field(default_factory=RiskMetrics)
    final_capital: float = 0.0
    total_return: float = 0.0
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trades": [t.to_dict() for t in self.trades],
            "equity_curve": self.equity_curve.to_dict() if not self.equity_curve.empty else {},
            "metrics": self.metrics.to_dict(),
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "execution_time_ms": self.execution_time_ms,
        }


class BacktestEngine:
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        config: Optional[BacktestConfig] = None,
    ) -> BacktestResult:
        start_time = datetime.now()

        cfg = config or self.config
        data = strategy.before_backtest(data)

        signals = strategy.generate_signals(data)

        trades = self._execute_signals(
            signals=signals,
            data=data,
            strategy=strategy,
            config=cfg,
        )

        equity_curve = self._calculate_equity_curve(trades, cfg.initial_capital, data)

        metrics = RiskMetrics.from_trades(
            trades=[t.to_dict() for t in trades],
            initial_capital=cfg.initial_capital,
            returns=equity_curve["returns"] if "returns" in equity_curve.columns else pd.Series(),
        )

        final_capital = cfg.initial_capital + sum(t.pnl for t in trades if t.pnl is not None)
        total_return = (final_capital - cfg.initial_capital) / cfg.initial_capital

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            final_capital=final_capital,
            total_return=total_return,
            execution_time_ms=execution_time,
        )

    def _execute_signals(
        self,
        signals: pd.DataFrame,
        data: pd.DataFrame,
        strategy: BaseStrategy,
        config: BacktestConfig,
    ) -> List[Trade]:
        trades = []
        position: Optional[Position] = None
        running_capital = config.initial_capital
        pending_signal: Optional[int] = None  # Track signal for next bar entry

        for idx in range(len(signals)):
            current_bar = data.iloc[idx]
            signal = signals.iloc[idx].get("signal", 0)
            timestamp = current_bar.name if hasattr(current_bar, "name") else data.index[idx]
            close_price = current_bar["close"]

            # First, check if we have a pending entry from previous bar's exit
            if pending_signal is not None and position is None:
                # Execute the pending entry at this bar's open (simulated as close for simplicity)
                if pending_signal == 1:
                    position = self._open_position(
                        symbol=strategy.name,
                        timestamp=timestamp,
                        price=close_price,
                        side=PositionSide.LONG,
                        data=data,
                        idx=idx,
                        config=config,
                        capital=running_capital,
                    )
                elif pending_signal == -1 and config.allow_shorting:
                    position = self._open_position(
                        symbol=strategy.name,
                        timestamp=timestamp,
                        price=close_price,
                        side=PositionSide.SHORT,
                        data=data,
                        idx=idx,
                        config=config,
                        capital=running_capital,
                    )
                pending_signal = None

            if position is None and pending_signal is None:
                # No position and no pending entry - check for new signal
                if signal == 1:
                    position = self._open_position(
                        symbol=strategy.name,
                        timestamp=timestamp,
                        price=close_price,
                        side=PositionSide.LONG,
                        data=data,
                        idx=idx,
                        config=config,
                        capital=running_capital,
                    )
                elif signal == -1 and config.allow_shorting:
                    position = self._open_position(
                        symbol=strategy.name,
                        timestamp=timestamp,
                        price=close_price,
                        side=PositionSide.SHORT,
                        data=data,
                        idx=idx,
                        config=config,
                        capital=running_capital,
                    )
            elif position is not None:
                exit_trade = False

                if position.side == PositionSide.LONG and signal == -1:
                    exit_trade = True
                elif position.side == PositionSide.SHORT and signal == 1:
                    exit_trade = True

                if exit_trade:
                    trade = self._close_position(
                        position=position,
                        exit_price=close_price,
                        exit_timestamp=timestamp,
                        config=config,
                    )
                    trades.append(trade)
                    if trade.pnl is not None:
                        running_capital += trade.pnl
                    position = None

                    # Set pending signal for next bar - DO NOT enter immediately
                    # This fixes look-ahead bias: signal is known at close,
                    # but entry happens at next bar's open
                    pending_signal = signal

        if position is not None:
            last_close = data.iloc[-1]["close"]
            last_timestamp = data.index[-1]
            trade = self._close_position(
                position=position,
                exit_price=last_close,
                exit_timestamp=last_timestamp,
                config=config,
            )
            trades.append(trade)

        return trades

    def _open_position(
        self,
        symbol: str,
        timestamp: datetime,
        price: float,
        side: PositionSide,
        data: pd.DataFrame,
        idx: int,
        config: BacktestConfig,
        capital: Optional[float] = None,
    ) -> Position:
        adjusted_price = self._apply_slippage(
            price, config.slippage, "buy" if side == PositionSide.LONG else "sell"
        )

        available_capital = capital if capital is not None else config.initial_capital
        max_shares = int((available_capital * config.max_position_size) / adjusted_price)
        quantity = max(1, max_shares)

        position = Position(
            symbol=symbol,
            entry_time=timestamp,
            entry_price=adjusted_price,
            quantity=quantity,
            side=side,
            current_price=adjusted_price,
        )

        return position

    def _close_position(
        self,
        position: Position,
        exit_price: float,
        exit_timestamp: datetime,
        config: BacktestConfig,
    ) -> Trade:
        adjusted_exit_price = self._apply_slippage(
            exit_price, config.slippage, "sell" if position.side == PositionSide.LONG else "buy"
        )

        commission = (
            position.entry_price * position.quantity + adjusted_exit_price * position.quantity
        ) * config.commission

        slippage_cost = abs(exit_price - adjusted_exit_price) * position.quantity

        trade = Trade(
            symbol=position.symbol,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            quantity=position.quantity,
            side=TradeSide.LONG if position.side == PositionSide.LONG else TradeSide.SHORT,
            exit_time=exit_timestamp,
            exit_price=adjusted_exit_price,
            status=TradeStatus.CLOSED,
            commission=commission,
            slippage=slippage_cost,
        )

        return trade

    def _apply_slippage(self, price: float, slippage_pct: float, side: str) -> float:
        if side == "buy":
            return price * (1 + slippage_pct)
        return price * (1 - slippage_pct)

    def _calculate_equity_curve(
        self,
        trades: List[Trade],
        initial_capital: float,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        if not trades:
            return pd.DataFrame(columns=["timestamp", "equity", "returns", "drawdown"])

        equity_data = []
        current_capital = initial_capital

        timestamps = data.index.tolist()

        trade_idx = 0
        for timestamp in timestamps:
            while trade_idx < len(trades) and trades[trade_idx].exit_time <= timestamp:
                current_capital += trades[trade_idx].pnl if trades[trade_idx].pnl else 0
                trade_idx += 1

            equity_data.append(
                {
                    "timestamp": timestamp,
                    "equity": current_capital,
                }
            )

        df = pd.DataFrame(equity_data)
        df = df.set_index("timestamp")

        df["returns"] = df["equity"].pct_change().fillna(0)

        cumulative_returns = (1 + df["returns"]).cumprod()
        running_max = cumulative_returns.cummax()
        df["drawdown"] = (cumulative_returns - running_max) / running_max

        return df


class VectorizedBacktestEngine(BacktestEngine):
    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        config: Optional[BacktestConfig] = None,
    ) -> BacktestResult:
        start_time = datetime.now()

        cfg = config or self.config

        signals = strategy.generate_signals(data)

        positions = (signals["signal"] != 0).astype(int)
        position_changes = signals["signal"].diff().fillna(0)

        returns = data["close"].pct_change().fillna(0)

        strategy_returns = positions.shift(1).fillna(0) * returns

        commission_cost = abs(position_changes) * cfg.commission
        strategy_returns = strategy_returns - commission_cost

        capital = cfg.initial_capital
        equity = (1 + strategy_returns).cumprod() * capital

        final_capital = equity.iloc[-1] if not equity.empty else capital
        total_return = (final_capital - capital) / capital

        equity_curve = pd.DataFrame(
            {
                "timestamp": data.index,
                "equity": equity.values,
                "returns": strategy_returns.values,
            }
        ).set_index("timestamp")

        equity_curve["cumulative"] = (1 + equity_curve["returns"]).cumprod()
        equity_curve["running_max"] = equity_curve["cumulative"].cummax()
        equity_curve["drawdown"] = (
            equity_curve["cumulative"] - equity_curve["running_max"]
        ) / equity_curve["running_max"]

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        trades = self._extract_trades_from_signals(signals, data, cfg)

        metrics = RiskMetrics.from_trades(
            trades=[t.to_dict() for t in trades],
            initial_capital=cfg.initial_capital,
            returns=equity_curve["returns"],
        )

        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            final_capital=final_capital,
            total_return=total_return,
            execution_time_ms=execution_time,
        )

    def _extract_trades_from_signals(
        self,
        signals: pd.DataFrame,
        data: pd.DataFrame,
        config: BacktestConfig,
    ) -> List[Trade]:
        trades = []
        position_side = None
        entry_price = None
        entry_time = None
        pending_signal = None  # Track signal for next bar entry to avoid look-ahead bias

        for idx in range(len(signals)):
            signal = signals.iloc[idx]["signal"]
            timestamp = signals.index[idx]
            close_price = data.iloc[idx]["close"]

            # First, check if we have a pending entry from previous bar's exit
            if pending_signal is not None and position_side is None:
                # Execute the pending entry at this bar
                if pending_signal == 1:
                    position_side = "LONG"
                    entry_price = close_price
                    entry_time = timestamp
                elif pending_signal == -1:
                    position_side = "SHORT"
                    entry_price = close_price
                    entry_time = timestamp
                pending_signal = None

            if position_side is None and pending_signal is None:
                # No position and no pending entry - check for new signal
                if signal == 1:
                    position_side = "LONG"
                    entry_price = close_price
                    entry_time = timestamp
                elif signal == -1:
                    position_side = "SHORT"
                    entry_price = close_price
                    entry_time = timestamp
            elif position_side is not None:
                should_exit = False
                if position_side == "LONG" and signal == -1:
                    should_exit = True
                elif position_side == "SHORT" and signal == 1:
                    should_exit = True

                if should_exit:
                    trade_value = close_price * 1
                    commission = trade_value * config.commission

                    pnl = (
                        (close_price - entry_price) - commission
                        if position_side == "LONG"
                        else (entry_price - close_price) - commission
                    )

                    trade = Trade(
                        symbol="strategy",
                        entry_time=entry_time,
                        entry_price=entry_price,
                        quantity=1,
                        side=TradeSide[position_side],
                        exit_time=timestamp,
                        exit_price=close_price,
                        status=TradeStatus.CLOSED,
                        commission=commission,
                    )
                    trades.append(trade)
                    position_side = None

                    # Set pending signal for next bar - DO NOT enter immediately
                    # This fixes look-ahead bias: signal is known at close,
                    # but entry happens at next bar's open
                    pending_signal = signal

        return trades
