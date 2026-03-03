from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np


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
    kelly_criterion: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    var_99: float = 0.0
    cvar_99: float = 0.0
    omega_ratio: float = 0.0
    information_ratio: float = 0.0
    tail_ratio: float = 0.0
    gain_to_pain: float = 0.0
    ulcer_index: float = 0.0
    downside_risk: float = 0.0
    upside_ratio: float = 0.0

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
        return self.total_return / abs(self.max_drawdown)

    @property
    def risk_adjusted_return(self) -> float:
        if self.volatility == 0:
            return 0.0
        return self.total_return / self.volatility

    @property
    def win_loss_ratio(self) -> float:
        if self.avg_loss == 0:
            return 0.0
        return self.avg_win / abs(self.avg_loss)

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
            "kelly_criterion": self.kelly_criterion,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "var_99": self.var_99,
            "cvar_99": self.cvar_99,
            "omega_ratio": self.omega_ratio,
            "information_ratio": self.information_ratio,
            "tail_ratio": self.tail_ratio,
            "gain_to_pain": self.gain_to_pain,
            "ulcer_index": self.ulcer_index,
            "downside_risk": self.downside_risk,
            "upside_ratio": self.upside_ratio,
            "risk_adjusted_return": self.risk_adjusted_return,
            "win_loss_ratio": self.win_loss_ratio,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
        }

    @classmethod
    def from_trades(
        cls, trades: list[dict], initial_capital: float, returns: pd.Series
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
            losses = [t["pnl"] for t in closed_trades if t["pnl"] < 0]
            metrics.avg_loss = abs(sum(losses)) / metrics.losing_trades
            metrics.largest_loss = min(losses)  # stored as negative

        # Profit factor = gross_profit / gross_loss (standard definition)
        gross_profit = sum(t["pnl"] for t in closed_trades if t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in closed_trades if t["pnl"] < 0))
        if gross_loss > 0:
            metrics.profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            metrics.profit_factor = float("inf")

        metrics.expectancy = (metrics.win_rate * metrics.avg_win) - (
            (1 - metrics.win_rate) * metrics.avg_loss
        )

        daily_returns = returns.dropna() if len(returns) > 0 else pd.Series()

        if len(daily_returns) > 1:
            metrics.volatility = daily_returns.std() * (252**0.5)
            metrics.downside_risk = daily_returns[daily_returns < 0].std() * (252**0.5)

            if daily_returns.std() > 0:
                metrics.sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * (252**0.5)

            negative_returns = daily_returns[daily_returns < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std() * (252**0.5)
                metrics.sortino_ratio = (
                    (daily_returns.mean() * 252) / downside_std if downside_std > 0 else 0
                )
                metrics.downside_deviation = downside_std

            metrics.skewness = (
                float(daily_returns.skew()) if hasattr(daily_returns, "skew") else 0.0
            )
            metrics.kurtosis = (
                float(daily_returns.kurt()) if hasattr(daily_returns, "kurt") else 0.0
            )

            metrics.kelly_criterion = cls._calculate_kelly_criterion(daily_returns)
            metrics.var_95 = cls._calculate_var(daily_returns, 0.95)
            metrics.cvar_95 = cls._calculate_cvar(daily_returns, 0.95)
            metrics.var_99 = cls._calculate_var(daily_returns, 0.99)
            metrics.cvar_99 = cls._calculate_cvar(daily_returns, 0.99)
            metrics.omega_ratio = cls._calculate_omega_ratio(daily_returns)
            metrics.tail_ratio = cls._calculate_tail_ratio(daily_returns)
            metrics.ulcer_index = cls._calculate_ulcer_index(daily_returns)
            metrics.gain_to_pain = cls._calculate_gain_to_pain(daily_returns)
            metrics.upside_ratio = cls._calculate_upside_ratio(daily_returns)

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

    @staticmethod
    def _calculate_kelly_criterion(returns: pd.Series) -> float:
        if len(returns) < 2:
            return 0.0

        win_rate = (returns > 0).sum() / len(returns)
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0

        if avg_loss == 0:
            return 0.0

        win_loss_ratio = avg_win / avg_loss
        if win_loss_ratio == 0:
            return 0.0
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        return max(0.0, min(1.0, kelly))

    @staticmethod
    def _calculate_var(returns: pd.Series, confidence: float) -> float:
        if len(returns) < 2:
            return 0.0

        var = returns.quantile(1 - confidence)
        return abs(var) if not pd.isna(var) else 0.0

    @staticmethod
    def _calculate_cvar(returns: pd.Series, confidence: float) -> float:
        if len(returns) < 2:
            return 0.0

        var_threshold = returns.quantile(1 - confidence)
        cvar = returns[returns <= var_threshold].mean()

        return abs(cvar) if not pd.isna(cvar) else 0.0

    @staticmethod
    def _calculate_omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
        if len(returns) < 2:
            return 0.0

        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns < threshold].sum())

        if losses == 0:
            return float("inf") if gains > 0 else 0.0

        return gains / losses

    @staticmethod
    def _calculate_tail_ratio(returns: pd.Series) -> float:
        if len(returns) < 20:
            return 0.0

        percentile_95 = returns.quantile(0.95)
        percentile_5 = abs(returns.quantile(0.05))

        if percentile_5 == 0:
            return 0.0

        return percentile_95 / percentile_5

    @staticmethod
    def _calculate_ulcer_index(returns: pd.Series) -> float:
        if len(returns) < 2:
            return 0.0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = ((cumulative - running_max) / running_max) * 100

        return float(np.sqrt((drawdown**2).mean()))

    @staticmethod
    def _calculate_gain_to_pain(returns: pd.Series) -> float:
        if len(returns) < 2:
            return 0.0

        total_return = returns.sum()
        pain = abs(returns[returns < 0].sum())

        if pain == 0:
            return float("inf") if total_return > 0 else 0.0

        return total_return / pain

    @staticmethod
    def _calculate_upside_ratio(returns: pd.Series, target_return: float = 0.0) -> float:
        if len(returns) < 2:
            return 0.0

        upside_returns = returns[returns > target_return]
        downside_returns = returns[returns < target_return]

        upside_std = upside_returns.std() * (252**0.5) if len(upside_returns) > 1 else 0
        downside_std = downside_returns.std() * (252**0.5) if len(downside_returns) > 1 else 0

        if downside_std == 0:
            return 0.0

        return upside_std / downside_std
