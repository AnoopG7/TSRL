"""Tests for all 12 FastAPI endpoints in src/main.py."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


# ==================== GET Endpoints ====================


class TestRootEndpoint:
    def test_root_returns_app_info(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Trading Strategy Research Lab"
        assert data["version"] == "0.2.0"
        assert data["status"] == "running"


class TestHealthEndpoint:
    def test_health_returns_healthy(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestListStrategies:
    def test_returns_all_strategies(self):
        response = client.get("/api/v1/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        strategies = data["strategies"]
        assert len(strategies) >= 10  # At least 10 strategies registered

    def test_strategies_have_required_fields(self):
        response = client.get("/api/v1/strategies")
        data = response.json()
        for s in data["strategies"]:
            assert "name" in s
            assert "version" in s
            assert "type" in s
            assert "description" in s
            assert "registry_key" in s
            assert "parameters" in s

    def test_ema_crossover_in_strategies(self):
        response = client.get("/api/v1/strategies")
        data = response.json()
        keys = [s["registry_key"] for s in data["strategies"]]
        assert "ema_crossover" in keys

    def test_ml_strategies_in_list(self):
        response = client.get("/api/v1/strategies")
        data = response.json()
        keys = [s["registry_key"] for s in data["strategies"]]
        assert "ml_random_forest" in keys


class TestGetStrategy:
    def test_get_existing_strategy(self):
        response = client.get("/api/v1/strategies/ema_crossover")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "EMA Crossover"
        assert data["registry_key"] == "ema_crossover"
        assert data["type"] == "momentum"

    def test_get_strategy_includes_parameters(self):
        response = client.get("/api/v1/strategies/ema_crossover")
        data = response.json()
        assert "parameters" in data
        params = data["parameters"]
        assert "fast_period" in params or len(params) > 0

    def test_get_nonexistent_strategy_returns_404(self):
        response = client.get("/api/v1/strategies/nonexistent_strategy")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_macd_strategy(self):
        response = client.get("/api/v1/strategies/macd")
        assert response.status_code == 200
        assert response.json()["registry_key"] == "macd"

    def test_get_ml_strategy(self):
        response = client.get("/api/v1/strategies/ml_random_forest")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "ml"


class TestListBacktests:
    def test_list_backtests_returns_list(self):
        response = client.get("/api/v1/backtests")
        assert response.status_code == 200
        data = response.json()
        assert "backtests" in data
        assert isinstance(data["backtests"], list)

    def test_list_backtests_with_limit(self):
        response = client.get("/api/v1/backtests?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["backtests"]) <= 5


# ==================== POST Endpoints ====================


class TestRunBacktest:
    def test_run_backtest_success(self):
        response = client.post("/api/v1/backtests/run", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "initial_capital": 100000.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["strategy"] == "ema_crossover"
        assert "results" in data
        assert "final_capital" in data["results"]
        assert "total_return" in data["results"]
        assert "total_trades" in data["results"]
        assert "equity_curve" in data
        assert "drawdown_series" in data
        assert "trades" in data

    def test_run_backtest_invalid_strategy(self):
        response = client.post("/api/v1/backtests/run", json={
            "strategy_name": "nonexistent_strategy",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code in (404, 500)

    def test_run_backtest_with_custom_params(self):
        response = client.post("/api/v1/backtests/run", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "initial_capital": 50000.0,
            "commission": 0.002,
            "slippage": 0.001,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_run_backtest_has_metrics(self):
        response = client.post("/api/v1/backtests/run", json={
            "strategy_name": "macd",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 200
        metrics = response.json()["results"]["metrics"]
        assert isinstance(metrics, dict)


class TestCompareStrategies:
    def test_compare_two_strategies(self):
        response = client.post("/api/v1/backtests/compare", json={
            "strategy_names": ["ema_crossover", "macd"],
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "strategies" in data

    def test_compare_three_strategies(self):
        response = client.post("/api/v1/backtests/compare", json={
            "strategy_names": ["ema_crossover", "macd", "rsi_mean_reversion"],
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("strategies", {})) == 3


class TestDataIngest:
    def test_data_ingest(self):
        response = client.post("/api/v1/data/ingest", json={
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-06-01",
        })
        # May succeed or fail depending on Yahoo Finance availability
        assert response.status_code in (200, 500)


class TestGridOptimization:
    def test_grid_optimization(self):
        response = client.post("/api/v1/optimization/grid", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {
                "fast_period": [8, 12],
                "slow_period": [21, 26],
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "best_params" in data
        assert "best_score" in data
        assert "total_iterations" in data
        assert data["total_iterations"] == 4  # 2 x 2

    def test_grid_optimization_invalid_strategy(self):
        response = client.post("/api/v1/optimization/grid", json={
            "strategy_name": "nonexistent",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {"fast_period": [8, 12]},
        })
        assert response.status_code == 404


class TestRandomOptimization:
    def test_random_optimization(self):
        response = client.post("/api/v1/optimization/random", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {
                "fast_period": [8, 10, 12],
                "slow_period": [21, 26, 30],
            },
            "n_iterations": 3,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_iterations"] <= 3


class TestGeneticOptimization:
    def test_genetic_optimization(self):
        response = client.post("/api/v1/optimization/genetic", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {
                "fast_period": [8, 10, 12],
                "slow_period": [21, 26, 30],
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "best_params" in data


class TestWalkForward:
    def test_walkforward_analysis(self):
        response = client.post("/api/v1/walkforward/run", json={
            "strategy_name": "ema_crossover",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {
                "fast_period": [8, 12],
                "slow_period": [21, 26],
            },
            "train_days": 120,
            "test_days": 30,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "windows" in data
        assert "n_windows" in data
        assert "stability_score" in data

    def test_walkforward_invalid_strategy(self):
        response = client.post("/api/v1/walkforward/run", json={
            "strategy_name": "nonexistent",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "param_grid": {"fast_period": [8, 12]},
        })
        assert response.status_code == 404


class TestMLTrain:
    def test_ml_train_random_forest(self):
        response = client.post("/api/v1/ml/train", json={
            "strategy_name": "ml_random_forest",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["model"] == "ml_random_forest"
        assert "results" in data
        assert "equity_curve" in data

    def test_ml_train_gradient_boosting(self):
        response = client.post("/api/v1/ml/train", json={
            "strategy_name": "ml_gradient_boosting",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_ml_train_invalid_strategy(self):
        response = client.post("/api/v1/ml/train", json={
            "strategy_name": "nonexistent_ml",
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code in (404, 500)
