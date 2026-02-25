from dataclasses import dataclass
from typing import Optional, List
import pandas as pd


@dataclass
class RiskMetrics:
    total_return: float = 0.0
    cagr: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade_duration: Optional[float] = None
    volatility: float = 0.0
    downside_deviation: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0

    @property
    def is_profitable(self) -> bool:
        return self.total_return > 0

    @property
    def avg_win_pct(self) -> float:
        if self.winning_trades == 0:
            return 0.0
        return self.avg_win

    @property
    def avg_loss_pct(self) -> float:
        if self.losing_trades == 0:
            return 0.0
        return self.avg_loss

    @property
    def risk_of_ruin(self) -> float:
        if self.win_rate == 0 or self.profit_factor == 0:
            return 1.0
        if self.win_rate == 1.0:
            return 0.0
        loss_rate = 1 - self.win_rate
        if self.profit_factor <= 1:
            return 1.0
        return (loss_rate / self.win_rate) ** self.total_trades if self.total_trades > 0 else 0.0

    @property
    def return_to_drawdown(self) -> float:
        if self.max_drawdown == 0:
            return 0.0
        return self.total_return / abs(self.max_drawdown)

    @property
    def recovery_factor(self) -> float:
        if self.max_drawdown == 0:
            return 0.0
        return self.total_return / abs(self.max_drawdown) if self.max_drawdown != 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "total_return": self.total_return,
            "cagr": self.cagr,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_pct": self.max_drawdown_pct,
            "calmar_ratio": self.calmar_ratio,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "avg_trade_duration": self.avg_trade_duration,
            "volatility": self.volatility,
            "risk_of_ruin": self.risk_of_ruin,
            "recovery_factor": self.recovery_factor,
            "return_to_drawdown": self.return_to_drawdown,
        }

    @classmethod
    def from_trades(
        cls, trades: List[dict], initial_capital: float, returns: pd.Series
    ) -> "RiskMetrics":
        metrics = cls()
        if not trades:
            return metrics

        closed_trades = [t for t in trades if t.get("pnl") is not None]
        if not closed_trades:
            return metrics

        metrics.total_trades = len(closed_trades)
        metrics.winning_trades = len([t for t in closed_trades if t["pnl"] > 0])
        metrics.losing_trades = len([t for t in closed_trades if t["pnl"] < 0])

        if metrics.total_trades > 0:
            metrics.win_rate = metrics.winning_trades / metrics.total_trades

        if metrics.winning_trades > 0:
            wins = [t["pnl"] for t in closed_trades if t["pnl"] > 0]
            metrics.avg_win = sum(wins) / metrics.winning_trades
            metrics.largest_win = max(wins)

        if metrics.losing_trades > 0:
            losses = [abs(t["pnl"]) for t in closed_trades if t["pnl"] < 0]
            metrics.avg_loss = sum(losses) / metrics.losing_trades
            metrics.largest_loss = max(losses)

        if metrics.avg_loss > 0:
            metrics.profit_factor = (
                metrics.avg_win / metrics.avg_loss if metrics.avg_loss > 0 else 0
            )

        metrics.expectancy = (metrics.win_rate * metrics.avg_win) - (
            (1 - metrics.win_rate) * metrics.avg_loss
        )

        if len(returns) > 1:
            metrics.volatility = returns.std() * (252**0.5)
            daily_returns = returns.dropna()
            if len(daily_returns) > 0:
                metrics.sharpe_ratio = (
                    (daily_returns.mean() / daily_returns.std()) * (252**0.5)
                    if daily_returns.std() > 0
                    else 0
                )
                negative_returns = daily_returns[daily_returns < 0]
                if len(negative_returns) > 0:
                    downside_std = negative_returns.std() * (252**0.5)
                    metrics.sortino_ratio = (
                        (daily_returns.mean() * 252) / downside_std if downside_std > 0 else 0
                    )
                metrics.downside_deviation = (
                    negative_returns.std() * (252**0.5) if len(negative_returns) > 0 else 0
                )
                metrics.skewness = float(daily_returns.skew())
                metrics.kurtosis = float(daily_returns.kurt())

        final_capital = initial_capital + sum(t["pnl"] for t in closed_trades)
        metrics.total_return = (
            (final_capital - initial_capital) / initial_capital if initial_capital > 0 else 0
        )

        if len(returns) > 252:
            metrics.cagr = (
                ((final_capital / initial_capital) ** (252 / len(returns))) - 1
                if initial_capital > 0
                else 0
            )

        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        metrics.max_drawdown_pct = abs(drawdown.min()) * 100
        metrics.max_drawdown = abs(drawdown.min()) * initial_capital

        if metrics.max_drawdown_pct > 0:
            metrics.calmar_ratio = metrics.cagr / metrics.max_drawdown_pct

        return metrics
