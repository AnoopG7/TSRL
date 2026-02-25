from typing import Dict, Type, Optional, List

from src.strategies.base import BaseStrategy


class StrategyRegistry:
    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        cls._strategies[name] = strategy_class

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
        return strategy.to_dict()

    @classmethod
    def get_all_strategy_info(cls) -> List[Dict]:
        info = []
        for name in cls._strategies.keys():
            strategy_info = cls.get_strategy_info(name)
            if strategy_info:
                info.append(strategy_info)
        return info


def register_strategy(name: str):
    def decorator(strategy_class: Type[BaseStrategy]):
        StrategyRegistry.register(name, strategy_class)
        return strategy_class

    return decorator
