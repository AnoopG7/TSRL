import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Dict, Type, Optional, List

from src.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        cls._strategies[name] = strategy_class
        logger.debug(f"Registered strategy: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseStrategy]]:
        return cls._strategies.get(name)

    @classmethod
    def create(cls, name: str, **params) -> Optional[BaseStrategy]:
        strategy_class = cls.get(name)
        if strategy_class is None:
            return None
        return strategy_class(**params)

    @classmethod
    def list_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_info(cls, name: str) -> Optional[Dict]:
        strategy_class = cls.get(name)
        if strategy_class is None:
            return None
        strategy = strategy_class()
        info = strategy.to_dict()
        info["registry_key"] = name
        return info

    @classmethod
    def get_all_strategy_info(cls) -> List[Dict]:
        info = []
        for name in cls._strategies:
            strategy_info = cls.get_strategy_info(name)
            if strategy_info:
                info.append(strategy_info)
        return info

    @classmethod
    def auto_discover(cls, base_path: Optional[Path] = None) -> None:
        if cls._initialized:
            return

        if base_path is None:
            base_path = Path(__file__).parent

        strategy_dirs = ["momentum", "breakout", "volatility", "mean_reversion"]

        for dir_name in strategy_dirs:
            dir_path = base_path / dir_name
            if not dir_path.exists():
                continue

            for _, module_name, _ in pkgutil.iter_modules([str(dir_path)]):
                try:
                    module = importlib.import_module(f"src.strategies.{dir_name}.{module_name}")
                    logger.info(f"Auto-discovered strategies from: {dir_name}.{module_name}")
                except Exception as e:
                    logger.warning(f"Failed to import {dir_name}.{module_name}: {e}")

        cls._initialized = True
        logger.info(f"Auto-discovery complete. Found {len(cls._strategies)} strategies.")

    @classmethod
    def validate_parameters(cls, name: str, params: Dict) -> tuple[bool, Optional[str]]:
        strategy_class = cls.get(name)
        if strategy_class is None:
            return False, f"Strategy '{name}' not found"

        strategy = strategy_class()
        required_params = strategy.get_parameters()

        for param_name in required_params:
            if param_name not in params:
                return False, f"Missing required parameter: {param_name}"

            value = params[param_name]
            param_def = required_params[param_name]

            # Type validation - infer expected type from default value
            if hasattr(param_def, "value"):
                expected_type = type(param_def.value)
                if expected_type == int and not isinstance(value, int):
                    return False, f"Parameter '{param_name}' must be an integer, got {type(value).__name__}"
                elif expected_type == float and not isinstance(value, (int, float)):
                    return False, f"Parameter '{param_name}' must be a number, got {type(value).__name__}"
                elif expected_type == str and not isinstance(value, str):
                    return False, f"Parameter '{param_name}' must be a string, got {type(value).__name__}"
                elif expected_type == bool and not isinstance(value, bool):
                    return False, f"Parameter '{param_name}' must be a boolean, got {type(value).__name__}"

            # Range validation
            if hasattr(param_def, "min_value") and param_def.min_value is not None:
                if value < param_def.min_value:
                    return False, f"Parameter '{param_name}' below minimum: {param_def.min_value}"

            if hasattr(param_def, "max_value") and param_def.max_value is not None:
                if value > param_def.max_value:
                    return False, f"Parameter '{param_name}' above maximum: {param_def.max_value}"

        return True, None


def register_strategy(name: str, version: str = "1.0.0"):
    def decorator(strategy_class: Type[BaseStrategy]):
        StrategyRegistry.register(name, strategy_class)
        return strategy_class

    return decorator
