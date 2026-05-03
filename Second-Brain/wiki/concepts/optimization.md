# Optimization

## Definition
Systematic search for strategy parameters that maximize a chosen objective metric. The core tension: **finding optimal parameters vs. overfitting to historical noise.**

## Why It Matters
- **Edge discovery**: The right parameters can turn a mediocre strategy into a profitable one
- **Overfitting trap**: The best parameters in-sample are often the worst out-of-sample
- **Compute budget**: Grid search of 5 params × 20 values each = 3.2M backtests. Must choose wisely.

## In My System

TSRL provides four optimizer classes in `src/engine/optimizer/optimizer.py`:

### 1. Grid Search (`GridSearchOptimizer`)

**How it works:** Tests every combination in the parameter grid.

```python
# optimizer.py:96-139
param_combinations = self._generate_grid(param_grid)  # Cartesian product
for params in param_combinations:
    result = self._evaluate_params(type(strategy), params, data, cfg)
```

**Trade-offs:**
| Aspect | Value |
|--------|-------|
| Completeness | ✅ Tests everything |
| Speed | ❌ O(n^k) where k = num params |
| Best for | ≤ 3 params, ≤ 10 values each |
| Overfitting risk | 🔴 High (many comparisons) |

**When to use:** Small search spaces. Final refinement after random search narrows the range.

---

### 2. Random Search (`RandomSearchOptimizer`)

**How it works:** Samples N random parameter sets from the grid.

```python
# optimizer.py:169-214
for i in range(n_iter):
    params = self._sample_params(param_grid)  # random.choice per param
    result = self._evaluate_params(type(strategy), params, data, cfg)
```

**Why random beats grid (for high dimensions):**
- With 5 params, grid search wastes 80% of compute on irrelevant dimensions
- Random search is more likely to find good values for the 1-2 params that actually matter (Bergstra & Bengio, 2012)

**Trade-offs:**
| Aspect | Value |
|--------|-------|
| Completeness | ❌ Samples subset |
| Speed | ✅ O(n) — fixed budget |
| Best for | 4+ params, initial exploration |
| Overfitting risk | 🟡 Medium |

---

### 3. Genetic Algorithm (`GeneticOptimizer`)

**How it works:** Evolves a population of parameter sets through selection, crossover, and mutation.

```python
# optimizer.py:223-320
population = self._initialize_population(param_grid)  # 20 random individuals

for generation in range(30):
    # Evaluate all individuals
    # Select elite (top 4)
    # Tournament selection for parents
    # Crossover: child = random mix of parent1/parent2
    # Mutation: 10% chance of random parameter change
    # Random reset: 20% chance of jumping anywhere in space
```

**Key hyperparameters:**
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `population_size` | 20 | Balance diversity vs. compute |
| `n_generations` | 30 | Usually converges by gen 15-20 |
| `elite_size` | 4 | Preserves top 20% |
| `mutation_rate` | 0.1 | Small perturbations |
| `mutation_amount` | 0.2 | Chance of random jump (prevents local optima) |
| `tournament_size` | 5 | Selection pressure |

**Total evaluations:** 20 × 30 = 600 backtests

**Trade-offs:**
| Aspect | Value |
|--------|-------|
| Completeness | ❌ Heuristic search |
| Speed | ✅ Fixed budget (600 evals) |
| Best for | Large spaces, nonlinear interactions |
| Overfitting risk | 🟡 Medium (selection pressure) |

---

### 4. Parallel Optimizer (`ParallelOptimizer`)

**How it works:** Wraps any parameter list with `ProcessPoolExecutor` for multi-core execution.

```python
# optimizer.py:344-396
with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
    futures = {executor.submit(_evaluate_single, ...): params for params in combinations}
```

**Limitation:** Requires strategy classes to be picklable. Some complex strategies may fail.

---

## Metric Selection (Objective Function)

The optimizer maximizes one metric. Choosing the wrong one leads to degenerate strategies.

```python
# optimizer.py:82-93
metric_map = {
    "sharpe_ratio": metrics.sharpe_ratio,
    "sortino_ratio": metrics.sortino_ratio,
    "calmar_ratio": metrics.calmar_ratio,
    "total_return": metrics.total_return,
    "win_rate": metrics.win_rate,
    "profit_factor": metrics.profit_factor,
}
```

| Metric | Optimizes For | Pathology When Maximized |
|--------|-------------|------------------------|
| `sharpe_ratio` | Risk-adjusted return | Tends to prefer infrequent trading |
| `sortino_ratio` | Downside risk-adjusted | Similar to Sharpe but ignores upside vol |
| `total_return` | Raw return | Ignores risk — will pick max leverage |
| `win_rate` | Trade accuracy | Prefers many tiny wins, avoids big moves |
| `profit_factor` | Gross profit / loss | Good balance, but 1-2 trades can distort |
| `calmar_ratio` | Return / max DD | Very sensitive to single worst drawdown |

**Recommendation:** Use `sharpe_ratio` for exploration, `profit_factor` for final selection. Never optimize on `total_return` alone.

---

## The Overfitting Problem

### Degrees of Freedom Rule
```
Max safe parameters ≈ Total trades / 100
```

**Example:** 200 trades → max 2 parameters. EMA crossover (fast_period, slow_period) = 2 params → safe. Adding signal_period = 3 params → borderline.

### Walk-Forward as Antidote

The optimizer finds parameters. [[Walk-Forward Analysis]] validates them:

```
Optimizer.optimize(train_data) → best_params
WalkForward.evaluate(best_params, test_data) → OOS metrics
```

**If OOS Sharpe < 50% of IS Sharpe → overfitted.**

---

## Failure Cases & Edge Cases

### 1. Flat Optimization Landscape
**Symptom:** Many parameter combinations produce similar results

**Cause:** Strategy edge is small relative to noise

**Detection:** Plot score vs. parameter value — if it's nearly flat, the strategy probably has no real edge

### 2. Grid Search Explosion
**Symptom:** Optimizer runs for hours/days

**Cause:** Too many parameters × too many values

**Math:** 5 params × 20 values = 3,200,000 combinations at ~100ms each = 88 hours

**Fix:** Use random search first (100 iterations), then grid search a narrow range

### 3. Genetic Algorithm Premature Convergence
**Symptom:** All individuals converge to same params by gen 5

**Cause:** Tournament size too large or elite size too large

**Fix:** Increase `mutation_amount` (random jump probability) or reduce `elite_size`

---

## Key Insights

### The Optimization Paradox
> "The more you optimize, the worse your out-of-sample performance."

Each additional parameter test is a hypothesis. 100 tests at 5% significance → 5 false discoveries expected. This is why walk-forward matters.

### Random Search > Grid Search (Usually)
For 4+ parameters, random search finds 90% of the optimal in 1% of the compute. It's not about being thorough — it's about covering the important dimensions.

### The Metric Trap
Optimizing for Sharpe ratio produces strategies that trade infrequently (low denominator = high Sharpe). Always check trade count alongside the optimized metric.

---

## Related Concepts
- [[Walk-Forward Analysis]] — Out-of-sample validation after optimization
- [[Backtesting]] — The engine that evaluates each parameter set
- [[Strategy Design]] — Principles that reduce the need for optimization
- [[Risk Metrics]] — The metrics used as optimization objectives

## Implementation References
- `src/engine/optimizer/optimizer.py` — All optimizer classes
- `src/engine/walkforward/walkforward.py` — Uses optimizer internally
- `src/application/services/backtest_service.py` — Orchestration layer
