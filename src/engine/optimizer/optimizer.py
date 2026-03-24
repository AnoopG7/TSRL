import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
import random

import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.strategies.base import BaseStrategy
from src.engine.backtest.engine import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    best_params: dict = field(default_factory=dict)
    best_score: float = 0.0
    all_results: list = field(default_factory=list)
    execution_time_ms: float = 0.0
    total_iterations: int = 0


@dataclass
class OptimizationConfig:
    metric: str = "sharpe_ratio"
    maximize: bool = True
    n_jobs: int = 1
    random_state: int = 42
    verbose: bool = True


class BaseOptimizer(ABC):
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.engine = BacktestEngine()

    @abstractmethod
    def optimize(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        param_grid: dict,
        config: Optional[BacktestConfig] = None,
    ) -> OptimizationResult:
        pass

    def _evaluate_params(
        self,
        strategy_class: type,
        params: dict,
        data: pd.DataFrame,
        config: BacktestConfig,
    ) -> dict:
        try:
            strategy = strategy_class(**params)
            result = self.engine.run(strategy, data, config)
            score = self._get_metric(result.metrics)
            return {
                "params": params,
                "score": score,
                "metrics": result.metrics.to_dict(),
                "total_return": result.total_return,
                "total_trades": len(result.trades),
                "max_drawdown": result.metrics.max_drawdown_pct,
                "win_rate": result.metrics.win_rate,
                "success": True,
            }
        except Exception as e:
            logger.warning(f"Failed to evaluate params {params}: {e}")
            return {
                "params": params,
                "score": float("-inf") if self.config.maximize else float("inf"),
                "success": False,
                "error": str(e),
            }

    def _get_metric(self, metrics) -> float:
        metric_map = {
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
            "total_return": metrics.total_return,
            "win_rate": metrics.win_rate,
            "profit_factor": metrics.profit_factor,
            "expectancy": metrics.expectancy,
            "kelly_criterion": metrics.kelly_criterion,
            "omega_ratio": metrics.omega_ratio,
        }
        return metric_map.get(self.config.metric, metrics.sharpe_ratio)


class GridSearchOptimizer(BaseOptimizer):
    def optimize(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        param_grid: dict,
        config: Optional[BacktestConfig] = None,
    ) -> OptimizationResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        param_combinations = self._generate_grid(param_grid)
        logger.info(f"Grid search: {len(param_combinations)} combinations")

        all_results = []
        best_score = float("-inf") if self.config.maximize else float("inf")
        best_params = {}

        for i, params in enumerate(param_combinations):
            result = self._evaluate_params(type(strategy), params, data, cfg)
            all_results.append(result)

            if result["success"]:
                if self.config.maximize:
                    if result["score"] > best_score:
                        best_score = result["score"]
                        best_params = params
                else:
                    if result["score"] < best_score:
                        best_score = result["score"]
                        best_params = params

            if self.config.verbose and (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(param_combinations)}")

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            execution_time_ms=execution_time,
            total_iterations=len(param_combinations),
        )

    def _generate_grid(self, param_grid: dict) -> list[dict]:
        keys = list(param_grid.keys())
        values = list(param_grid.values())

        if not keys:
            return [{}]

        combinations = []
        for combination in self._cartesian_product(values):
            combinations.append(dict(zip(keys, combination)))

        return combinations

    def _cartesian_product(self, arrays: list) -> list:
        if not arrays:
            yield []
            return

        if len(arrays) == 1:
            for item in arrays[0]:
                yield [item]
            return

        for head in arrays[0]:
            for tail in self._cartesian_product(arrays[1:]):
                yield [head] + tail


class RandomSearchOptimizer(BaseOptimizer):
    def optimize(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        param_grid: dict,
        n_iter: int = 100,
        config: Optional[BacktestConfig] = None,
    ) -> OptimizationResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        random.seed(self.config.random_state)
        logger.info(f"Random search: {n_iter} iterations")

        all_results = []
        best_score = float("-inf") if self.config.maximize else float("inf")
        best_params = {}

        for i in range(n_iter):
            params = self._sample_params(param_grid)
            result = self._evaluate_params(type(strategy), params, data, cfg)
            all_results.append(result)

            if result["success"]:
                if self.config.maximize:
                    if result["score"] > best_score:
                        best_score = result["score"]
                        best_params = params
                else:
                    if result["score"] < best_score:
                        best_score = result["score"]
                        best_params = params

            if self.config.verbose and (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{n_iter}")

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            execution_time_ms=execution_time,
            total_iterations=n_iter,
        )

    def _sample_params(self, param_grid: dict) -> dict:
        params = {}
        for key, values in param_grid.items():
            params[key] = random.choice(values)
        return params


class GeneticOptimizer(BaseOptimizer):
    def __init__(self, config: Optional[OptimizationConfig] = None):
        super().__init__(config)
        self.population_size = 20
        self.n_generations = 30
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
        self.elite_size = 4  # Increased from 2 to maintain diversity
        self.tournament_size = 5  # For tournament selection
        self.mutation_amount = 0.2  # Probability of mutating to random value

    def optimize(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        param_grid: dict,
        config: Optional[BacktestConfig] = None,
    ) -> OptimizationResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        random.seed(self.config.random_state)
        np.random.seed(self.config.random_state)

        logger.info(
            f"Genetic algorithm: {self.n_generations} generations, pop size {self.population_size}"
        )

        population = self._initialize_population(param_grid)

        best_score = float("-inf") if self.config.maximize else float("inf")
        best_params = {}
        all_results = []

        for generation in range(self.n_generations):
            evaluated = []
            for params in population:
                result = self._evaluate_params(type(strategy), params, data, cfg)
                evaluated.append((params, result))
                all_results.append(result)

                if result["success"]:
                    if self.config.maximize:
                        if result["score"] > best_score:
                            best_score = result["score"]
                            best_params = params.copy()
                    else:
                        if result["score"] < best_score:
                            best_score = result["score"]
                            best_params = params.copy()

            evaluated.sort(key=lambda x: x[1]["score"], reverse=self.config.maximize)

            if self.config.verbose:
                logger.info(f"Gen {generation + 1}: Best score = {best_score:.4f}")

            # Elite individuals (guaranteed to survive)
            elites = [p for p, _ in evaluated[: self.elite_size]]
            offspring = elites.copy()

            # Tournament selection for parents - maintains diversity better than pure elite selection
            def tournament_select():
                tournament = random.sample(evaluated, min(self.tournament_size, len(evaluated)))
                tournament.sort(key=lambda x: x[1]["score"], reverse=self.config.maximize)
                return tournament[0][0]

            while len(offspring) < self.population_size:
                # Select two parents via tournament selection (not just from elites)
                parent1 = tournament_select()
                parent2 = tournament_select()

                if random.random() < self.crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    # Asexual reproduction - copy one parent
                    child = parent1.copy()

                # Mutation: either perturb or random reset
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, param_grid)
                elif random.random() < self.mutation_amount:
                    # Random reset mutation - jump to anywhere in search space
                    key = random.choice(list(param_grid.keys()))
                    child[key] = random.choice(param_grid[key])

                offspring.append(child)

            population = offspring[: self.population_size]

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            execution_time_ms=execution_time,
            total_iterations=self.n_generations * self.population_size,
        )

    def _initialize_population(self, param_grid: dict) -> list[dict]:
        population = []
        for _ in range(self.population_size):
            individual = {}
            for key, values in param_grid.items():
                individual[key] = random.choice(values)
            population.append(individual)
        return population

    def _crossover(self, parent1: dict, parent2: dict) -> dict:
        child = {}
        for key in parent1.keys():
            child[key] = random.choice([parent1[key], parent2[key]])
        return child

    def _mutate(self, individual: dict, param_grid: dict) -> dict:
        mutated = individual.copy()
        key = random.choice(list(param_grid.keys()))
        mutated[key] = random.choice(param_grid[key])
        return mutated


class ParallelOptimizer:
    def __init__(self, n_jobs: int = -1):
        self.n_jobs = n_jobs if n_jobs > 0 else None

    def optimize(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        param_combinations: list[dict],
        config: Optional[BacktestConfig] = None,
        metric: str = "sharpe_ratio",
    ) -> OptimizationResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()
        engine = BacktestEngine()

        logger.info(f"Parallel optimization: {len(param_combinations)} combinations")

        results = []

        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = {}
            for params in param_combinations:
                future = executor.submit(
                    _evaluate_single,
                    strategy.__class__,
                    params,
                    data,
                    cfg,
                    metric,
                )
                futures[future] = params

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed: {futures[future]}: {e}")

        results.sort(key=lambda x: x["score"], reverse=True)

        best = results[0] if results else {}

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return OptimizationResult(
            best_params=best.get("params", {}),
            best_score=best.get("score", 0.0),
            all_results=results,
            execution_time_ms=execution_time,
            total_iterations=len(param_combinations),
        )


def _evaluate_single(
    strategy_class: type,
    params: dict,
    data: pd.DataFrame,
    config: BacktestConfig,
    metric: str,
) -> dict:
    try:
        engine = BacktestEngine()
        strategy = strategy_class(**params)
        result = engine.run(strategy, data, config)

        metric_map = {
            "sharpe_ratio": result.metrics.sharpe_ratio,
            "sortino_ratio": result.metrics.sortino_ratio,
            "calmar_ratio": result.metrics.calmar_ratio,
            "total_return": result.metrics.total_return,
            "win_rate": result.metrics.win_rate,
            "profit_factor": result.metrics.profit_factor,
            "expectancy": result.metrics.expectancy,
        }
        score = metric_map.get(metric, result.metrics.sharpe_ratio)

        return {
            "params": params,
            "score": score,
            "metrics": result.metrics.to_dict(),
            "total_return": result.total_return,
            "total_trades": len(result.trades),
            "max_drawdown": result.metrics.max_drawdown_pct,
            "win_rate": result.metrics.win_rate,
            "success": True,
        }
    except Exception as e:
        return {
            "params": params,
            "score": float("-inf"),
            "success": False,
            "error": str(e),
        }
