from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class RiskMetricsCalculator:
    @staticmethod
    def calculate_total_return(initial_capital: float, final_capital: float) -> float:
        if initial_capital <= 0:
            return 0.0
        return (final_capital - initial_capital) / initial_capital

    @staticmethod
    def calculate_cagr(initial_capital: float, final_capital: float, n_days: int) -> float:
        if initial_capital <= 0 or n_days <= 0:
            return 0.0
        years = n_days / 252
        if years <= 0:
            return 0.0
        return (final_capital / initial_capital) ** (1 / years) - 1

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        if len(returns) < 2 or returns.std() == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / periods_per_year
        return np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()

    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        return (excess_returns.mean() * periods_per_year) / downside_std

    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
        if len(equity_curve) < 2:
            return 0.0, pd.NaT, pd.NaT

        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max

        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()

        peak_idx = equity_curve[:max_dd_idx].idxmax()

        return abs(max_dd), peak_idx, max_dd_idx

    @staticmethod
    def calculate_calmar_ratio(cagr: float, max_drawdown: float) -> float:
        if max_drawdown == 0:
            return 0.0
        return cagr / max_drawdown

    @staticmethod
    def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0

        closed_trades = [t for t in trades if t.get("pnl") is not None]
        if not closed_trades:
            return 0.0

        winning = len([t for t in closed_trades if t["pnl"] > 0])
        return winning / len(closed_trades)

    @staticmethod
    def calculate_expectancy(trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0

        closed_trades = [t for t in trades if t.get("pnl") is not None]
        if not closed_trades:
            return 0.0

        total_pnl = sum(t["pnl"] for t in closed_trades)
        return total_pnl / len(closed_trades)

    @staticmethod
    def calculate_profit_factor(trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0

        closed_trades = [t for t in trades if t.get("pnl") is not None]
        if not closed_trades:
            return 0.0

        gross_profit = sum(t["pnl"] for t in closed_trades if t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in closed_trades if t["pnl"] < 0))

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    @staticmethod
    def calculate_rolling_sharpe(
        returns: pd.Series,
        window: int = 60,
        risk_free_rate: float = 0.0,
    ) -> pd.Series:
        if len(returns) < window:
            return pd.Series([0.0], index=returns.index)

        rolling_mean = returns.rolling(window=window).mean()
        rolling_std = returns.rolling(window=window).std()

        sharpe = np.sqrt(252) * (rolling_mean - risk_free_rate / 252) / rolling_std
        return sharpe.fillna(0)

    @staticmethod
    def calculate_rolling_max_drawdown(
        equity_curve: pd.Series,
        window: int = 60,
    ) -> pd.Series:
        if len(equity_curve) < window:
            return pd.Series([0.0], index=equity_curve.index)

        rolling_max = equity_curve.rolling(window=window).max()
        drawdown = (equity_curve - rolling_max) / rolling_max
        return drawdown.fillna(0)

    @staticmethod
    def calculate_monthly_returns(returns: pd.Series) -> pd.DataFrame:
        if len(returns) < 1:
            return pd.DataFrame()

        monthly = returns.resample("M").apply(lambda x: (1 + x).prod() - 1)
        monthly_pivot = monthly.to_frame()
        monthly_pivot["year"] = monthly_pivot.index.year
        monthly_pivot["month"] = monthly_pivot.index.month

        return monthly_pivot.pivot_table(values=0, index="year", columns="month")

    @staticmethod
    def calculate_trade_statistics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trades:
            return {}

        closed_trades = [t for t in trades if t.get("pnl") is not None]
        if not closed_trades:
            return {}

        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in closed_trades if t["pnl"] < 0]

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades) if closed_trades else 0,
            "avg_win": sum(t["pnl"] for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0,
            "avg_loss": sum(t["pnl"] for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0,
            "largest_win": max(t["pnl"] for t in winning_trades) if winning_trades else 0,
            "largest_loss": min(t["pnl"] for t in losing_trades) if losing_trades else 0,
            "avg_trade": sum(t["pnl"] for t in closed_trades) / len(closed_trades)
            if closed_trades
            else 0,
        }


class DrawdownAnalyzer:
    @staticmethod
    def get_drawdown_periods(equity_curve: pd.Series) -> List[Dict[str, Any]]:
        if len(equity_curve) < 2:
            return []

        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max

        in_drawdown = drawdown < 0
        drawdown_periods = []
        start = None

        for i, (idx, (is_dd, dd_val)) in enumerate(zip(drawdown.index, drawdown.items())):
            if is_dd and start is None:
                start = i
                start_idx = idx
            elif not is_dd and start is not None:
                peak_idx = equity_curve.iloc[:start].idxmax()
                trough_idx = equity_curve.iloc[start:i].idxmin()

                drawdown_periods.append(
                    {
                        "start": peak_idx,
                        "end": trough_idx,
                        "duration": (trough_idx - peak_idx).days,
                        "drawdown": abs(drawdown.iloc[start:i].min()),
                        "peak_value": equity_curve[peak_idx],
                        "trough_value": equity_curve[trough_idx],
                    }
                )
                start = None

        return drawdown_periods

    @staticmethod
    def calculate_recovery_time(
        equity_curve: pd.Series,
        drawdown_start: pd.Timestamp,
    ) -> Optional[int]:
        if drawdown_start not in equity_curve.index:
            return None

        peak_value = equity_curve[drawdown_start]
        after_start = equity_curve[drawdown_start:]

        # Find when equity recovers back to the peak value
        recovered = after_start[after_start >= peak_value]

        if len(recovered) > 1:  # First match is the start itself
            recovery_date = recovered.index[1]
            return (recovery_date - drawdown_start).days

        return None
