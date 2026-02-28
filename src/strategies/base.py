from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np


@dataclass
class StrategyParameter:
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: str = ""


@dataclass
class RiskManagementResult:
    should_stop_loss: bool = False
    should_take_profit: bool = False
    should_trailing_stop: bool = False
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    position_size_multiplier: float = 1.0
    additional_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    def __init__(self, **params):
        self._params: Dict[str, Any] = {}
        self._set_default_parameters()
        self.set_parameters(**params)
        self._validate_parameters()

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        pass

    def _set_default_parameters(self) -> None:
        pass

    def get_parameters(self) -> Dict[str, Any]:
        return self._params.copy()

    def get_parameter(self, name: str, default: Any = None) -> Any:
        return self._params.get(name, default)

    def set_parameters(self, **params) -> None:
        for key, value in params.items():
            if key in self._params:
                current = self._params[key]
                if hasattr(current, 'value'):
                    current.value = value
                else:
                    self._params[key] = value

    def _validate_parameters(self) -> bool:
        return True

    def validate_parameters(self) -> bool:
        return self._validate_parameters()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

    def entry_conditions(self, data: pd.DataFrame, idx: int) -> bool:
        signals = self.generate_signals(data)
        if idx >= len(signals):
            return False
        row = signals.iloc[idx]
        return row.get("signal", 0) == 1

    def exit_conditions(self, data: pd.DataFrame, idx: int) -> bool:
        signals = self.generate_signals(data)
        if idx >= len(signals):
            return False
        row = signals.iloc[idx]
        return row.get("signal", 0) == -1

    def risk_management(
        self,
        position: Any,
        data: pd.DataFrame,
        current_idx: int,
    ) -> RiskManagementResult:
        return RiskManagementResult()

    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        return data

    def after_backtest(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return results

    def get_requirements(self) -> List[str]:
        return ["open", "high", "low", "close", "volume"]

    def calculate_position_size(
        self,
        capital: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        if entry_price <= 0 or stop_loss_price <= 0:
            return 0
        if entry_price == stop_loss_price:
            return 0

        risk_amount = capital * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price)
        position_size = risk_amount / price_risk

        return max(0, position_size)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "type": self.strategy_type,
            "parameters": self.get_parameters(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseStrategy":
        params = data.get("parameters", {})
        return cls(**params)

    def __repr__(self) -> str:
        return f"{self.name}(v{self.version})"
