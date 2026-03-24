"""Portfolio-specific metrics entity."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortfolioMetrics:
    """Portfolio-specific risk metrics."""

    # Correlation
    correlation_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    avg_correlation: float = 0.0

    # Beta and Alpha (vs benchmark)
    beta: float = 0.0
    alpha: float = 0.0  # Jensen's alpha (annualized)

    # Diversification
    diversification_ratio: float = 0.0
    concentration_hhi: float = 0.0  # Herfindahl-Hirschman Index

    # Tracking
    tracking_error: float = 0.0
    information_ratio: float = 0.0

    # Contribution analysis
    asset_contributions: dict[str, float] = field(default_factory=dict)  # Return contribution
    risk_contributions: dict[str, float] = field(default_factory=dict)  # Risk contribution

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "correlation_matrix": self.correlation_matrix,
            "avg_correlation": round(self.avg_correlation, 4),
            "beta": round(self.beta, 4),
            "alpha": round(self.alpha, 4),
            "diversification_ratio": round(self.diversification_ratio, 4),
            "concentration_hhi": round(self.concentration_hhi, 4),
            "tracking_error": round(self.tracking_error, 4),
            "information_ratio": round(self.information_ratio, 4),
            "asset_contributions": {k: round(v, 4) for k, v in self.asset_contributions.items()},
            "risk_contributions": {k: round(v, 4) for k, v in self.risk_contributions.items()},
        }

    @property
    def is_diversified(self) -> bool:
        """Check if portfolio is well-diversified (HHI < 0.25)."""
        return self.concentration_hhi < 0.25

    @property
    def has_positive_alpha(self) -> bool:
        """Check if portfolio has positive alpha."""
        return self.alpha > 0
