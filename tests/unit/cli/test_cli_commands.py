"""Tests for all CLI commands in src/cli.py."""
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestStrategiesCommand:
    def test_lists_strategies(self, runner):
        result = runner.invoke(cli, ["strategies"])
        assert result.exit_code == 0
        assert "Available Strategies" in result.output

    def test_lists_ema_crossover(self, runner):
        result = runner.invoke(cli, ["strategies"])
        assert result.exit_code == 0
        assert "EMA Crossover" in result.output

    def test_lists_macd(self, runner):
        result = runner.invoke(cli, ["strategies"])
        assert result.exit_code == 0
        assert "macd" in result.output.lower()

    def test_shows_strategy_count(self, runner):
        result = runner.invoke(cli, ["strategies"])
        assert result.exit_code == 0
        assert "total" in result.output.lower()

    def test_lists_ml_strategies(self, runner):
        result = runner.invoke(cli, ["strategies"])
        assert result.exit_code == 0
        assert "ml_random_forest" in result.output


class TestBacktestCommand:
    def test_backtest_default(self, runner):
        result = runner.invoke(cli, [
            "backtest",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code == 0
        assert "Backtest Results" in result.output or "Total Return" in result.output

    def test_backtest_with_strategy(self, runner):
        result = runner.invoke(cli, [
            "backtest",
            "--strategy", "macd",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code == 0

    def test_backtest_invalid_strategy(self, runner):
        result = runner.invoke(cli, [
            "backtest",
            "--strategy", "nonexistent_strategy",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()

    def test_backtest_with_custom_capital(self, runner):
        result = runner.invoke(cli, [
            "backtest",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
            "--capital", "50000",
        ])
        assert result.exit_code == 0

    def test_backtest_shows_metrics(self, runner):
        result = runner.invoke(cli, [
            "backtest",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "return" in output or "capital" in output


class TestOptimizeCommand:
    def test_optimize_grid(self, runner):
        result = runner.invoke(cli, [
            "optimize",
            "--strategy", "ema_crossover",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
            "--method", "grid",
        ])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "optimizer" in output or "best" in output or "optimizable" in output

    def test_optimize_random(self, runner):
        result = runner.invoke(cli, [
            "optimize",
            "--strategy", "ema_crossover",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
            "--method", "random",
        ])
        assert result.exit_code == 0

    def test_optimize_invalid_strategy(self, runner):
        result = runner.invoke(cli, [
            "optimize",
            "--strategy", "nonexistent",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()


class TestWalkForwardCommand:
    def test_walkforward_default(self, runner):
        result = runner.invoke(cli, [
            "walkforward",
            "--strategy", "ema_crossover",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2024-01-01",
        ])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "walk" in output or "window" in output or "forward" in output


class TestFetchDataCommand:
    def test_fetch_data(self, runner):
        result = runner.invoke(cli, [
            "fetch-data",
            "--symbol", "AAPL",
            "--start-date", "2023-01-01",
            "--end-date", "2023-06-01",
        ])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "data" in output or "rows" in output or "fetched" in output
