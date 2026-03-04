import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.engine.optimizer.optimizer import (
    OptimizationConfig,
    OptimizationResult,
    GridSearchOptimizer,
    RandomSearchOptimizer,
    GeneticOptimizer,
)
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy
from src.engine.backtest.engine import BacktestConfig


class TestOptimizationConfig:
    """Tests for OptimizationConfig"""

    def test_default_values(self):
        config = OptimizationConfig()

        assert config.metric == "sharpe_ratio"
        assert config.maximize is True
        assert config.n_jobs == 1
        assert config.random_state == 42
        assert config.verbose is True

    def test_custom_values(self):
        config = OptimizationConfig(
            metric="total_return",
            maximize=False,
            n_jobs=4,
            random_state=123,
            verbose=False,
        )

        assert config.metric == "total_return"
        assert config.maximize is False
        assert config.n_jobs == 4
        assert config.random_state == 123
        assert config.verbose is False


class TestOptimizationResult:
    """Tests for OptimizationResult"""

    def test_default_values(self):
        result = OptimizationResult()

        assert result.best_params == {}
        assert result.best_score == 0.0
        assert result.all_results == []
        assert result.execution_time_ms == 0.0
        assert result.total_iterations == 0


class TestGridSearchOptimizer:
    """Tests for GridSearchOptimizer"""

    def test_optimizer_creation(self):
        optimizer = GridSearchOptimizer()

        assert optimizer.config.metric == "sharpe_ratio"
        assert optimizer.engine is not None

    def test_optimizer_with_custom_config(self):
        config = OptimizationConfig(metric="total_return", maximize=True)
        optimizer = GridSearchOptimizer(config)

        assert optimizer.config.metric == "total_return"

    def test_generate_grid_single_param(self):
        optimizer = GridSearchOptimizer()
        param_grid = {"fast_period": [5, 10, 15]}

        combinations = optimizer._generate_grid(param_grid)

        assert len(combinations) == 3
        assert {"fast_period": 5} in combinations
        assert {"fast_period": 10} in combinations
        assert {"fast_period": 15} in combinations

    def test_generate_grid_multiple_params(self):
        optimizer = GridSearchOptimizer()
        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20, 30],
        }

        combinations = optimizer._generate_grid(param_grid)

        assert len(combinations) == 4  # 2 * 2
        assert {"fast_period": 5, "slow_period": 20} in combinations
        assert {"fast_period": 5, "slow_period": 30} in combinations
        assert {"fast_period": 10, "slow_period": 20} in combinations
        assert {"fast_period": 10, "slow_period": 30} in combinations

    def test_generate_grid_empty(self):
        optimizer = GridSearchOptimizer()
        param_grid = {}

        combinations = optimizer._generate_grid(param_grid)

        assert len(combinations) == 1
        assert combinations[0] == {}

    def test_cartesian_product(self):
        optimizer = GridSearchOptimizer()
        arrays = [[1, 2], [3, 4, 5]]

        result = list(optimizer._cartesian_product(arrays))

        assert len(result) == 6  # 2 * 3

    def test_cartesian_product_single_array(self):
        optimizer = GridSearchOptimizer()
        arrays = [[1, 2, 3]]

        result = list(optimizer._cartesian_product(arrays))

        assert len(result) == 3

    def test_cartesian_product_empty(self):
        optimizer = GridSearchOptimizer()
        arrays = []

        result = list(optimizer._cartesian_product(arrays))

        assert len(result) == 1
        assert result[0] == []

    def test_optimize_with_sample_data(self):
        optimizer = GridSearchOptimizer()
        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20, 30],
        }

        # Create sample data
        data = pd.DataFrame(
            {
                "open": list(range(100, 200)),
                "high": list(range(101, 201)),
                "low": list(range(99, 199)),
                "close": list(range(100, 200)),
                "volume": [1000000] * 100,
            },
            index=pd.date_range("2023-01-01", periods=100),
        )

        strategy = EMACrossoverStrategy()
        result = optimizer.optimize(strategy, data, param_grid)

        assert isinstance(result, OptimizationResult)
        assert result.total_iterations == 4
        assert len(result.all_results) == 4

    def test_optimize_with_minimize(self):
        config = OptimizationConfig(metric="max_drawdown", maximize=False)
        optimizer = GridSearchOptimizer(config)
        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20, 30],
        }

        data = pd.DataFrame(
            {
                "open": list(range(100, 150)),
                "high": list(range(101, 151)),
                "low": list(range(99, 149)),
                "close": list(range(100, 150)),
                "volume": [1000000] * 50,
            },
            index=pd.date_range("2023-01-01", periods=50),
        )

        strategy = EMACrossoverStrategy()
        result = optimizer.optimize(strategy, data, param_grid)

        assert result.total_iterations == 4


class TestRandomSearchOptimizer:
    """Tests for RandomSearchOptimizer"""

    def test_optimizer_creation(self):
        optimizer = RandomSearchOptimizer()

        assert optimizer.config.metric == "sharpe_ratio"

    def test_optimize_with_sample_data(self):
        optimizer = RandomSearchOptimizer()
        param_grid = {
            "fast_period": [5, 10, 15, 20],
            "slow_period": [20, 30, 40, 50],
        }

        data = pd.DataFrame(
            {
                "open": list(range(100, 200)),
                "high": list(range(101, 201)),
                "low": list(range(99, 199)),
                "close": list(range(100, 200)),
                "volume": [1000000] * 100,
            },
            index=pd.date_range("2023-01-01", periods=100),
        )

        strategy = EMACrossoverStrategy()
        result = optimizer.optimize(strategy, data, param_grid, n_iter=5)

        assert isinstance(result, OptimizationResult)
        assert len(result.all_results) <= 5


class TestGeneticOptimizer:
    """Tests for GeneticOptimizer"""

    def test_optimizer_creation(self):
        optimizer = GeneticOptimizer()

        assert optimizer.config.metric == "sharpe_ratio"
        assert optimizer.population_size == 20
        assert optimizer.n_generations == 30
        assert optimizer.mutation_rate == 0.1

    def test_optimizer_custom_params(self):
        optimizer = GeneticOptimizer()
        optimizer.population_size = 50
        optimizer.n_generations = 20
        optimizer.mutation_rate = 0.2

        assert optimizer.population_size == 50
        assert optimizer.n_generations == 20
        assert optimizer.mutation_rate == 0.2

    def test_optimize_with_sample_data(self):
        optimizer = GeneticOptimizer()
        optimizer.population_size = 10
        optimizer.n_generations = 3
        optimizer.mutation_rate = 0.1
        param_grid = {
            "fast_period": [5, 10, 15, 20],
            "slow_period": [20, 30, 40, 50],
        }

        data = pd.DataFrame(
            {
                "open": list(range(100, 200)),
                "high": list(range(101, 201)),
                "low": list(range(99, 199)),
                "close": list(range(100, 200)),
                "volume": [1000000] * 100,
            },
            index=pd.date_range("2023-01-01", periods=100),
        )

        strategy = EMACrossoverStrategy()
        result = optimizer.optimize(strategy, data, param_grid)

        assert isinstance(result, OptimizationResult)
        assert result.total_iterations > 0

    def test_crossover(self):
        optimizer = GeneticOptimizer()
        parent1 = {"fast_period": 5, "slow_period": 20}
        parent2 = {"fast_period": 10, "slow_period": 30}

        child = optimizer._crossover(parent1, parent2)

        assert "fast_period" in child
        assert "slow_period" in child
        assert child["fast_period"] in [5, 10]
        assert child["slow_period"] in [20, 30]

    def test_mutate(self):
        optimizer = GeneticOptimizer()
        param_grid = {
            "fast_period": [5, 10, 15, 20],
            "slow_period": [20, 30, 40, 50],
        }
        individual = {"fast_period": 5, "slow_period": 20}

        mutated = optimizer._mutate(individual, param_grid)

        # Should either stay the same or change
        assert "fast_period" in mutated
        assert "slow_period" in mutated
