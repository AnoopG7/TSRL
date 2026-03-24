"""Portfolio-specific metrics calculator."""

from typing import Optional

import numpy as np
import pandas as pd

from src.domain.entities.portfolio_metrics import PortfolioMetrics


class PortfolioMetricsCalculator:
    """Calculate portfolio-specific risk metrics."""

    @staticmethod
    def calculate_all(
        asset_returns: dict[str, pd.Series],
        weights: dict[str, float],
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.0,
    ) -> PortfolioMetrics:
        """
        Calculate all portfolio metrics.

        Args:
            asset_returns: Dict mapping symbol -> daily return series
            weights: Dict mapping symbol -> allocation weight
            benchmark_returns: Optional benchmark daily returns for beta/alpha
            risk_free_rate: Annual risk-free rate (default 0.0)

        Returns:
            PortfolioMetrics with all calculated values
        """
        metrics = PortfolioMetrics()

        # Build returns DataFrame
        returns_df = pd.DataFrame(asset_returns)
        if returns_df.empty:
            return metrics

        # Correlation matrix
        corr_matrix = returns_df.corr()
        metrics.correlation_matrix = {
            col: {row: round(corr_matrix.loc[row, col], 4) for row in corr_matrix.index}
            for col in corr_matrix.columns
        }

        # Average correlation (excluding diagonal)
        n = len(corr_matrix)
        if n > 1:
            mask = ~np.eye(n, dtype=bool)
            off_diag = corr_matrix.values[mask]
            metrics.avg_correlation = float(np.nanmean(off_diag))

        # Portfolio returns (weighted sum)
        valid_symbols = [s for s in weights if s in returns_df.columns]
        if not valid_symbols:
            return metrics

        portfolio_returns = sum(
            returns_df[s] * weights[s] for s in valid_symbols
        )

        # Beta and Alpha (if benchmark provided)
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            aligned = pd.DataFrame({
                "portfolio": portfolio_returns,
                "benchmark": benchmark_returns,
            }).dropna()

            if len(aligned) > 20:
                cov = aligned["portfolio"].cov(aligned["benchmark"])
                var_bench = aligned["benchmark"].var()

                if var_bench > 0:
                    metrics.beta = float(cov / var_bench)

                    # Jensen's Alpha (annualized)
                    portfolio_annual = aligned["portfolio"].mean() * 252
                    benchmark_annual = aligned["benchmark"].mean() * 252
                    metrics.alpha = float(
                        portfolio_annual - risk_free_rate - metrics.beta * (benchmark_annual - risk_free_rate)
                    )

                    # Tracking error
                    tracking_diff = aligned["portfolio"] - aligned["benchmark"]
                    metrics.tracking_error = float(tracking_diff.std() * np.sqrt(252))

                    # Information ratio
                    if metrics.tracking_error > 0:
                        active_return = portfolio_annual - benchmark_annual
                        metrics.information_ratio = float(active_return / metrics.tracking_error)

        # Diversification ratio
        metrics.diversification_ratio = PortfolioMetricsCalculator._calc_diversification_ratio(
            returns_df, weights
        )

        # Concentration (HHI - Herfindahl-Hirschman Index)
        metrics.concentration_hhi = float(sum(w ** 2 for w in weights.values()))

        # Asset contributions
        metrics.asset_contributions = PortfolioMetricsCalculator._calc_return_contributions(
            returns_df, weights
        )
        metrics.risk_contributions = PortfolioMetricsCalculator._calc_risk_contributions(
            returns_df, weights
        )

        return metrics

    @staticmethod
    def _calc_diversification_ratio(
        returns_df: pd.DataFrame,
        weights: dict[str, float],
    ) -> float:
        """
        Calculate diversification ratio.

        Diversification ratio = weighted avg volatility / portfolio volatility
        Higher values indicate better diversification (correlations reducing risk).
        """
        if returns_df.empty:
            return 0.0

        # Individual volatilities (annualized)
        vols = returns_df.std() * np.sqrt(252)

        # Weighted average volatility
        weighted_vol = sum(
            weights.get(s, 0) * vols.get(s, 0)
            for s in returns_df.columns
            if s in weights
        )

        # Portfolio volatility
        cov_matrix = returns_df.cov() * 252
        valid_symbols = [s for s in returns_df.columns if s in weights]
        w = np.array([weights.get(s, 0) for s in valid_symbols])

        # Filter cov matrix to valid symbols
        cov_filtered = cov_matrix.loc[valid_symbols, valid_symbols]
        portfolio_var = float(np.dot(w, np.dot(cov_filtered.values, w)))
        portfolio_vol = np.sqrt(portfolio_var) if portfolio_var > 0 else 0

        if portfolio_vol > 0:
            return float(weighted_vol / portfolio_vol)
        return 0.0

    @staticmethod
    def _calc_return_contributions(
        returns_df: pd.DataFrame,
        weights: dict[str, float],
    ) -> dict[str, float]:
        """Calculate each asset's contribution to total return."""
        contributions = {}
        for symbol in returns_df.columns:
            if symbol in weights:
                asset_return = float((1 + returns_df[symbol]).prod() - 1)
                contributions[symbol] = asset_return * weights[symbol]
        return contributions

    @staticmethod
    def _calc_risk_contributions(
        returns_df: pd.DataFrame,
        weights: dict[str, float],
    ) -> dict[str, float]:
        """
        Calculate each asset's marginal contribution to risk (MCTR).

        Risk contribution = weight * MCTR / portfolio volatility
        """
        if returns_df.empty:
            return {}

        cov_matrix = returns_df.cov() * 252
        valid_symbols = [s for s in returns_df.columns if s in weights]
        w = np.array([weights.get(s, 0) for s in valid_symbols])

        if len(w) == 0:
            return {}

        # Filter cov matrix to valid symbols
        cov_filtered = cov_matrix.loc[valid_symbols, valid_symbols]
        portfolio_var = float(np.dot(w, np.dot(cov_filtered.values, w)))
        portfolio_vol = np.sqrt(portfolio_var) if portfolio_var > 0 else 1

        # Marginal contribution to risk
        mctr = np.dot(cov_filtered.values, w) / portfolio_vol

        # Component contribution = weight * MCTR / portfolio_vol
        contributions = {}
        for i, symbol in enumerate(valid_symbols):
            if portfolio_vol > 0:
                contributions[symbol] = float(w[i] * mctr[i] / portfolio_vol)
            else:
                contributions[symbol] = 0.0

        return contributions

    @staticmethod
    def calculate_correlation_matrix(
        symbols_data: dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix from OHLCV data.

        Args:
            symbols_data: Dict mapping symbol -> OHLCV DataFrame

        Returns:
            Correlation matrix as DataFrame
        """
        returns = {
            symbol: data["close"].pct_change().dropna()
            for symbol, data in symbols_data.items()
        }
        returns_df = pd.DataFrame(returns)
        return returns_df.corr()
