import click
from datetime import datetime, timedelta

from src.infrastructure.data_providers.yahoo_provider import YahooFinanceProvider
from src.strategies.registry import StrategyRegistry
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy, RSIMeanReversionStrategy
from src.strategies.breakout.breakout_strategy import BreakoutStrategy
from src.engine.backtest.engine import BacktestEngine, BacktestConfig


@click.group()
def cli():
    """Trading Strategy Research Lab CLI"""
    pass


@cli.command()
@click.option("--symbol", default="AAPL", help="Stock symbol")
@click.option("--start-date", default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
@click.option("--end-date", default=datetime.now().strftime("%Y-%m-%d"))
@click.option("--timeframe", default="1d")
@click.option("--capital", default=100000.0)
@click.option("--commission", default=0.001)
@click.option("--slippage", default=0.0005)
def backtest(symbol, start_date, end_date, timeframe, capital, commission, slippage):
    """Run a backtest"""
    click.echo(f"Running backtest for {symbol}...")

    provider = YahooFinanceProvider()
    df = provider.fetch_ohlcv(
        symbol=symbol,
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date),
        timeframe=timeframe,
    )
    click.echo(f"Loaded {len(df)} bars of data")

    strategy = EMACrossoverStrategy()

    config = BacktestConfig(
        initial_capital=capital,
        commission=commission,
        slippage=slippage,
    )

    engine = BacktestEngine(config)
    result = engine.run(strategy, df)

    click.echo(f"\n{'=' * 50}")
    click.echo(f"Backtest Results")
    click.echo(f"{'=' * 50}")
    click.echo(f"Final Capital: ${result.final_capital:,.2f}")
    click.echo(f"Total Return: {result.total_return * 100:.2f}%")
    click.echo(f"Total Trades: {len(result.trades)}")
    click.echo(f"Execution Time: {result.execution_time_ms:.2f}ms")
    click.echo(f"\nMetrics:")
    click.echo(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    click.echo(f"  Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%")
    click.echo(f"  Win Rate: {result.metrics.win_rate * 100:.2f}%")
    click.echo(f"  Sortino Ratio: {result.metrics.sortino_ratio:.2f}")


@cli.command()
def strategies():
    """List all available strategies"""
    click.echo("Available Strategies:")
    for info in StrategyRegistry.get_all_strategy_info():
        click.echo(f"\n  {info['name']} (v{info['version']})")
        click.echo(f"  Type: {info['type']}")
        click.echo(f"  {info['description']}")


@cli.command()
@click.option("--symbol", required=True)
@click.option("--start-date", required=True)
@click.option("--end-date", required=True)
@click.option("--timeframe", default="1d")
def fetch_data(symbol, start_date, end_date, timeframe):
    """Fetch OHLCV data"""
    click.echo(f"Fetching data for {symbol}...")

    provider = YahooFinanceProvider()
    df = provider.fetch_ohlcv(
        symbol=symbol,
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date),
        timeframe=timeframe,
    )

    click.echo(f"Fetched {len(df)} records")
    click.echo(f"Date range: {df.index.min()} to {df.index.max()}")
    click.echo(f"\nFirst 5 rows:")
    click.echo(df.head())


if __name__ == "__main__":
    cli()
