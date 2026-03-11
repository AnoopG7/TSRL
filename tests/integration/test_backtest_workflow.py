import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.application.services.backtest_service import BacktestService, BacktestResponse
from src.engine.backtest.engine import BacktestEngine, BacktestConfig
from src.strategies.registry import StrategyRegistry
from src.infrastructure.database.repositories.backtest_repository import (
    BacktestRepository,
    TradeRepository,
)

import src.strategies.momentum.ema_crossover


@pytest.fixture
def sample_ohlcv_dataframe():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(100) * 0.5)

    data = pd.DataFrame(
        {
            "open": prices + np.random.randn(100) * 0.2,
            "high": prices + np.abs(np.random.randn(100)) * 0.5,
            "low": prices - np.abs(np.random.randn(100)) * 0.5,
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 100).astype(float),
        },
        index=dates,
    )

    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)

    return data


class TestBacktestServiceWorkflow:
    @patch("src.application.services.backtest_service.DataService")
    @patch("src.application.services.backtest_service.get_session_factory")
    def test_run_backtest_full_workflow(
        self, mock_session_factory, mock_data_service_class, sample_ohlcv_dataframe
    ):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        mock_session = Mock()
        mock_session_factory.return_value.return_value = mock_session

        mock_backtest_repo = Mock()
        mock_backtest_repo.create.return_value = Mock(id=1)
        mock_backtest_repo.update_results.return_value = None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)

        with patch(
            "src.application.services.backtest_service.BacktestRepository",
            return_value=mock_backtest_repo,
        ):
            with patch(
                "src.application.services.backtest_service.TradeRepository", return_value=Mock()
            ):
                service = BacktestService()

                result = service.run_backtest(
                    strategy_name="ema_crossover",
                    symbol="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-04-10",
                    timeframe="1d",
                    initial_capital=100000.0,
                    commission=0.001,
                    slippage=0.0005,
                )

                assert isinstance(result, BacktestResponse)
                assert result.strategy == "ema_crossover"
                assert result.symbol == "AAPL"
                assert result.final_capital > 0

    @patch("src.application.services.backtest_service.DataService")
    def test_run_backtest_invalid_strategy(self, mock_data_service_class, sample_ohlcv_dataframe):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        service = BacktestService()

        with pytest.raises(ValueError, match="Strategy 'invalid_strategy' not found"):
            service.run_backtest(
                strategy_name="invalid_strategy",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10",
            )

    @patch("src.application.services.backtest_service.DataService")
    @patch("src.application.services.backtest_service.BacktestEngine")
    def test_compare_strategies(
        self, mock_engine_class, mock_data_service_class, sample_ohlcv_dataframe
    ):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        mock_result = Mock()
        mock_result.final_capital = 105000.0
        mock_result.total_return = 0.05
        mock_result.trades = []
        mock_result.metrics.to_dict.return_value = {}
        mock_result.equity_curve = pd.DataFrame({"equity": [100000, 105000]})

        mock_engine = Mock()
        mock_engine.run.return_value = mock_result
        mock_engine_class.return_value = mock_engine

        service = BacktestService()

        result = service.compare_strategies(
            strategy_names=["ema_crossover", "rsi_mean_reversion"],
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10",
            initial_capital=100000.0,
        )

        assert "symbol" in result
        assert "strategies" in result
        assert len(result["strategies"]) == 2

    @patch("src.application.services.backtest_service.DataService")
    def test_extract_equity_curve(self, mock_data_service_class, sample_ohlcv_dataframe):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        service = BacktestService()

        mock_result = Mock()
        ec = pd.DataFrame(
            {"equity": [100000.0, 105000.0, 102000.0]}, index=pd.date_range("2023-01-01", periods=3)
        )
        mock_result.equity_curve = ec
        mock_result.trades = []
        mock_result.metrics.to_dict.return_value = {}
        mock_result.final_capital = 102000.0
        mock_result.total_return = 0.02

        equity_curve = service._extract_equity_curve(mock_result)

        assert len(equity_curve) == 3
        assert "date" in equity_curve[0]
        assert "equity" in equity_curve[0]

    @patch("src.application.services.backtest_service.DataService")
    def test_extract_drawdown(self, mock_data_service_class, sample_ohlcv_dataframe):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        service = BacktestService()

        mock_result = Mock()
        ec = pd.DataFrame(
            {"equity": [100000.0, 110000.0, 105000.0, 100000.0]},
            index=pd.date_range("2023-01-01", periods=4),
        )
        mock_result.equity_curve = ec

        drawdown = service._extract_drawdown(mock_result)

        assert len(drawdown) > 0
        assert "date" in drawdown[0]
        assert "drawdown" in drawdown[0]

    @patch("src.application.services.backtest_service.DataService")
    def test_extract_monthly_returns(self, mock_data_service_class, sample_ohlcv_dataframe):
        mock_data_service = Mock()
        mock_data_service.fetch_data.return_value = (sample_ohlcv_dataframe, "simulated")
        mock_data_service_class.return_value = mock_data_service

        service = BacktestService()

        mock_result = Mock()
        dates = pd.date_range(start="2023-01-01", end="2023-03-31", freq="B")
        equity_values = [100000 + i * 100 for i in range(len(dates))]
        ec = pd.DataFrame({"equity": equity_values}, index=dates)
        mock_result.equity_curve = ec

        monthly_returns = service._extract_monthly_returns(mock_result)

        assert isinstance(monthly_returns, list)
