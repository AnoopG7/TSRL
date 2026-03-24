import click
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

from src.application.services.data_service import DataService
from src.strategies.registry import StrategyRegistry
from src.engine.backtest.engine import BacktestEngine, BacktestConfig
from src.engine.optimizer.optimizer import (
    GridSearchOptimizer,
    RandomSearchOptimizer,
    GeneticOptimizer,
    OptimizationConfig,
)
from src.engine.walkforward.walkforward import WalkForwardAnalysis

# Import all strategies to trigger @register_strategy decorators
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy, RSIMeanReversionStrategy  # noqa
from src.strategies.momentum.macd_strategy import MACDStrategy  # noqa
from src.strategies.momentum.ma_ribbon import MovingAverageRibbonStrategy, TripleMAStrategy  # noqa
from src.strategies.momentum.volume_strategies import VolumeProfileStrategy, VolumeBreakoutStrategy  # noqa
from src.strategies.mean_reversion.bollinger_bands import (
    BollingerBandsStrategy,
    BollingerBandsBreakoutStrategy,
)  # noqa
from src.ml.strategies.ml_strategies import MLRandomForestStrategy, MLGradientBoostingStrategy  # noqa


def _get_strategy_names() -> list[str]:
    """Get available strategy names from registry."""
    return [s["name"] for s in StrategyRegistry.get_all_strategy_info()]


@click.group()
def cli():
    """Trading Strategy Research Lab CLI"""
    pass


@cli.command()
@click.option("--strategy", "-s", default="ema_crossover", help="Strategy name")
@click.option("--symbol", default="AAPL", help="Stock symbol")
@click.option(
    "--start-date",
    default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    default=datetime.now().strftime("%Y-%m-%d"),
    help="End date (YYYY-MM-DD)",
)
@click.option("--timeframe", default="1d")
@click.option("--capital", default=100000.0, help="Initial capital")
@click.option("--commission", default=0.001)
@click.option("--slippage", default=0.0005)
@click.option("--source", default="yahoo", help="Data source: yahoo, alpha_vantage")
def backtest(
    strategy, symbol, start_date, end_date, timeframe, capital, commission, slippage, source
):
    """Run a backtest with any registered strategy."""
    click.echo(f"\n{click.style('TSRL Backtest', fg='cyan', bold=True)}")
    click.echo(f"Strategy: {click.style(strategy, fg='yellow')}")
    click.echo(f"Symbol:   {symbol}  |  {start_date} → {end_date}\n")

    # Resolve strategy from registry
    strat = StrategyRegistry.create(strategy)
    if strat is None:
        click.echo(click.style(f"✗ Strategy '{strategy}' not found.", fg="red"))
        click.echo(f"Available: {', '.join(_get_strategy_names())}")
        return

    # Fetch data
    data_service = DataService()
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    df, data_source, _ = data_service.fetch_data(symbol, start_dt, end_dt, timeframe, source=source)
    click.echo(f"Data: {len(df)} bars ({data_source})")

    # Run backtest
    config = BacktestConfig(
        initial_capital=capital,
        commission=commission,
        slippage=slippage,
    )
    engine = BacktestEngine(config)
    result = engine.run(strat, df)

    # Display results
    click.echo(f"\n{'=' * 50}")
    click.echo(click.style(" Backtest Results", fg="cyan", bold=True))
    click.echo(f"{'=' * 50}")

    ret_color = "green" if result.total_return >= 0 else "red"
    click.echo(f"  Final Capital:  ${result.final_capital:,.2f}")
    click.echo(
        f"  Total Return:   {click.style(f'{result.total_return * 100:.2f}%', fg=ret_color)}"
    )
    click.echo(f"  Total Trades:   {len(result.trades)}")
    click.echo(f"  Execution Time: {result.execution_time_ms:.2f}ms")

    m = result.metrics
    click.echo(f"\n  {click.style('Metrics', bold=True)}")
    click.echo(f"  Sharpe Ratio:   {_color_metric(m.sharpe_ratio, '{:.2f}')}")
    click.echo(f"  Sortino Ratio:  {_color_metric(m.sortino_ratio, '{:.2f}')}")
    click.echo(f"  Max Drawdown:   {click.style(f'{m.max_drawdown_pct:.2f}%', fg='red')}")
    click.echo(f"  Win Rate:       {m.win_rate * 100:.1f}%")
    click.echo(f"  Profit Factor:  {_color_metric(m.profit_factor, '{:.2f}', threshold=1.0)}")
    click.echo()


@cli.command()
def strategies():
    """List all available strategies."""
    all_strats = StrategyRegistry.get_all_strategy_info()
    click.echo(
        f"\n{click.style('Available Strategies', fg='cyan', bold=True)} ({len(all_strats)} total)\n"
    )

    for info in all_strats:
        click.echo(f"  {click.style(info['name'], fg='yellow', bold=True)} (v{info['version']})")
        click.echo(f"    Type: {info['type']}")
        click.echo(f"    {info['description']}")
        click.echo()


@cli.command()
@click.option("--strategy", "-s", required=True, help="Strategy name")
@click.option("--symbol", default="AAPL", help="Stock symbol")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD)")
@click.option(
    "--method",
    type=click.Choice(["grid", "random", "genetic"]),
    default="grid",
    help="Optimization method",
)
@click.option("--metric", default="sharpe_ratio", help="Metric to optimize")
@click.option("--n-iterations", default=50, help="Iterations for random search")
@click.option("--capital", default=100000.0)
def optimize(strategy, symbol, start_date, end_date, method, metric, n_iterations, capital):
    """Run strategy parameter optimization."""
    click.echo(f"\n{click.style('TSRL Optimizer', fg='cyan', bold=True)}")
    click.echo(f"Strategy: {click.style(strategy, fg='yellow')}  |  Method: {method}")
    click.echo(f"Symbol:   {symbol}  |  Metric: {metric}\n")

    strat = StrategyRegistry.create(strategy)
    if strat is None:
        click.echo(click.style(f"✗ Strategy '{strategy}' not found.", fg="red"))
        return

    # Build param grid from strategy's parameter definitions
    param_grid = _build_param_grid(strat)
    if not param_grid:
        click.echo(click.style("✗ No optimizable parameters found.", fg="red"))
        return

    click.echo(f"Parameters: {list(param_grid.keys())}")

    data_service = DataService()
    df, data_source, _ = data_service.fetch_data(
        symbol, datetime.fromisoformat(start_date), datetime.fromisoformat(end_date)
    )
    click.echo(f"Data: {len(df)} bars ({data_source})\n")

    bt_config = BacktestConfig(initial_capital=capital)
    opt_config = OptimizationConfig(metric=metric)

    optimizer_map = {
        "grid": GridSearchOptimizer,
        "random": RandomSearchOptimizer,
        "genetic": GeneticOptimizer,
    }
    optimizer = optimizer_map[method](config=opt_config)

    click.echo("Running optimization...")
    if method == "random":
        result = optimizer.optimize(strat, df, param_grid, n_iter=n_iterations, config=bt_config)
    else:
        result = optimizer.optimize(strat, df, param_grid, config=bt_config)

    click.echo(f"\n{'=' * 50}")
    click.echo(click.style(" Optimization Results", fg="cyan", bold=True))
    click.echo(f"{'=' * 50}")
    click.echo(f"  Best Score ({metric}): {click.style(f'{result.best_score:.4f}', fg='green')}")
    click.echo(f"  Best Params: {result.best_params}")
    click.echo(f"  Iterations:  {result.total_iterations}")
    click.echo(f"  Time:        {result.execution_time_ms:.0f}ms")

    # Show top 5 results
    top = sorted(
        [r for r in result.all_results if r.get("success")],
        key=lambda x: x["score"],
        reverse=True,
    )[:5]
    if top:
        click.echo(f"\n  {click.style('Top 5 Results', bold=True)}")
        for i, r in enumerate(top, 1):
            click.echo(f"    {i}. Score: {r['score']:.4f}  Params: {r['params']}")
    click.echo()


@cli.command()
@click.option("--strategy", "-s", required=True, help="Strategy name")
@click.option("--symbol", default="AAPL", help="Stock symbol")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD)")
@click.option("--train-days", default=252, help="Training window (days)")
@click.option("--test-days", default=63, help="Testing window (days)")
@click.option("--capital", default=100000.0)
def walkforward(strategy, symbol, start_date, end_date, train_days, test_days, capital):
    """Run walk-forward analysis."""
    click.echo(f"\n{click.style('TSRL Walk-Forward Analysis', fg='cyan', bold=True)}")
    click.echo(f"Strategy: {click.style(strategy, fg='yellow')}")
    click.echo(f"Symbol:   {symbol}  |  Train: {train_days}d  |  Test: {test_days}d\n")

    strat = StrategyRegistry.create(strategy)
    if strat is None:
        click.echo(click.style(f"✗ Strategy '{strategy}' not found.", fg="red"))
        return

    param_grid = _build_param_grid(strat)
    if not param_grid:
        click.echo(click.style("✗ No optimizable parameters found.", fg="red"))
        return

    data_service = DataService()
    df, data_source, _ = data_service.fetch_data(
        symbol, datetime.fromisoformat(start_date), datetime.fromisoformat(end_date)
    )
    click.echo(f"Data: {len(df)} bars ({data_source})\n")

    bt_config = BacktestConfig(initial_capital=capital)
    wfa = WalkForwardAnalysis()

    click.echo("Running walk-forward analysis...")
    result = wfa.run(
        strategy_class=type(strat),
        data=df,
        param_grid=param_grid,
        train_days=train_days,
        test_days=test_days,
        config=bt_config,
    )

    click.echo(f"\n{'=' * 50}")
    click.echo(click.style(" Walk-Forward Results", fg="cyan", bold=True))
    click.echo(f"{'=' * 50}")
    click.echo(f"  Windows:          {len(result.windows)}")
    click.echo(f"  Avg Train Sharpe: {_color_metric(result.avg_train_sharpe, '{:.4f}')}")
    click.echo(f"  Avg Test Sharpe:  {_color_metric(result.avg_test_sharpe, '{:.4f}')}")
    click.echo(
        f"  Stability Score:  {_color_metric(result.stability_score, '{:.4f}', threshold=0.5)}"
    )
    click.echo(f"  Total Test Return:{_color_metric(result.total_test_return, '{:.2%}')}")
    click.echo(f"  Time:             {result.execution_time_ms:.0f}ms")

    if result.windows:
        click.echo(f"\n  {click.style('Windows', bold=True)}")
        for i, w in enumerate(result.windows, 1):
            ret_color = "green" if w.test_return >= 0 else "red"
            click.echo(
                f"    {i}. {w.train_start.strftime('%Y-%m-%d')} → {w.test_end.strftime('%Y-%m-%d')}  "
                f"Return: {click.style(f'{w.test_return:.2%}', fg=ret_color)}  "
                f"Trades: {w.test_trades}  Params: {w.best_params}"
            )
    click.echo()


@cli.command()
@click.option("--symbol", required=True)
@click.option("--start-date", required=True)
@click.option("--end-date", required=True)
@click.option("--timeframe", default="1d")
def fetch_data(symbol, start_date, end_date, timeframe):
    """Fetch OHLCV data for a symbol."""
    click.echo(f"Fetching data for {symbol}...")

    data_service = DataService()
    df, data_source, _ = data_service.fetch_data(
        symbol,
        datetime.fromisoformat(start_date),
        datetime.fromisoformat(end_date),
        timeframe,
    )

    click.echo(f"Fetched {len(df)} records ({data_source})")
    click.echo(f"Date range: {df.index.min()} to {df.index.max()}")
    click.echo(f"\nFirst 5 rows:")
    click.echo(df.head())


# ==================== Helpers ====================


def _color_metric(value: float, fmt: str, threshold: float = 0.0) -> str:
    """Return a colorized string: green above threshold, red below."""
    formatted = fmt.format(value)
    color = "green" if value >= threshold else "red"
    return click.style(formatted, fg=color)


def _build_param_grid(strategy) -> dict:
    """Build a parameter grid from the strategy's parameter definitions."""
    params = strategy.get_parameters()
    grid = {}
    for name, param in params.items():
        if isinstance(param, dict):
            min_val = param.get("min_value")
            max_val = param.get("max_value")
            step = param.get("step")
            value = param.get("value")
        elif hasattr(param, "min_value"):
            min_val = param.min_value
            max_val = param.max_value
            step = getattr(param, "step", None)
            value = getattr(param, "value", None)
        else:
            continue

        if min_val is not None and max_val is not None:
            if step is not None and step > 0:
                vals = []
                v = min_val
                while v <= max_val:
                    vals.append(type(value)(v) if value is not None else v)
                    v += step
                grid[name] = vals
            else:
                # Generate 5 evenly spaced values
                step_val = (max_val - min_val) / 4
                vals = [min_val + step_val * i for i in range(5)]
                if value is not None:
                    vals = [type(value)(v) for v in vals]
                grid[name] = vals

    return grid


if __name__ == "__main__":
    cli()
