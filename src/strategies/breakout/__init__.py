# The original BreakoutStrategy is defined in momentum/ema_crossover.py
# Re-export it here for the breakout package
from src.strategies.momentum.ema_crossover import BreakoutStrategy

__all__ = ["BreakoutStrategy"]
