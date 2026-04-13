from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

from config.settings import get_settings
from src.infrastructure.database.connection import init_db
from src.infrastructure.database.repositories import BacktestRepository
from src.strategies.registry import StrategyRegistry
from src.engine.optimizer.optimizer import (
    GridSearchOptimizer,
    RandomSearchOptimizer,
    GeneticOptimizer,
    OptimizationConfig,
)
from src.engine.walkforward.walkforward import WalkForwardAnalysis
from src.engine.backtest.engine import BacktestConfig

# Import strategies to trigger @register_strategy decorators
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy, RSIMeanReversionStrategy  # noqa
from src.strategies.momentum.macd_strategy import MACDStrategy  # noqa
from src.strategies.momentum.ma_ribbon import MovingAverageRibbonStrategy, TripleMAStrategy  # noqa
from src.strategies.momentum.volume_strategies import VolumeProfileStrategy, VolumeBreakoutStrategy  # noqa
from src.strategies.mean_reversion.bollinger_bands import (
    BollingerBandsStrategy,
    BollingerBandsBreakoutStrategy,
)  # noqa
from src.ml.strategies.ml_strategies import MLRandomForestStrategy, MLGradientBoostingStrategy  # noqa

from src.application.services.backtest_service import BacktestService
from src.application.services.data_service import DataService
from src.application.services.fundamental_service import FundamentalService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    StrategyRegistry.auto_discover()
    yield


app = FastAPI(
    title="Trading Strategy Research Lab",
    description="AI-Powered Trading Strategy Research Platform",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request Models ====================


class DataIngestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    timeframe: str = "1d"
    source: str = "yahoo"


class BacktestRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    parameters: Optional[dict] = None


class CompareRequest(BaseModel):
    strategy_names: List[str]
    symbol: str
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005


class OptimizationRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List]
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    metric: str = "sharpe_ratio"
    n_iterations: int = 100


class WalkForwardRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List]
    train_days: int = 252
    test_days: int = 63
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005


class MLTrainRequest(BaseModel):
    strategy_name: str = "ml_random_forest"
    symbol: str
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    parameters: Optional[dict] = None


class PortfolioBacktestRequest(BaseModel):
    strategy_name: str
    symbols: List[str]
    weights: Optional[Dict[str, float]] = None
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    rebalance_frequency: str = "none"
    rebalance_threshold: Optional[float] = None
    benchmark_symbol: Optional[str] = None
    parameters: Optional[dict] = None


# ==================== Endpoints ====================


@app.get("/")
async def root():
    return {
        "name": "Trading Strategy Research Lab",
        "version": "0.2.0",
        "status": "running",
    }


@app.get("/api/v1/strategies")
async def list_strategies():
    strategies = StrategyRegistry.get_all_strategy_info()
    return {"strategies": strategies}


@app.get("/api/v1/strategies/{strategy_name}")
async def get_strategy(strategy_name: str):
    info = StrategyRegistry.get_strategy_info(strategy_name)
    if info is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return info


@app.get("/api/v1/backtests")
async def list_backtests(limit: int = 20):
    repo = BacktestRepository()
    try:
        backtests = repo.get_all(limit=limit)
        return {
            "backtests": [
                {
                    "id": b.id,
                    "name": b.name,
                    "symbol": b.symbol.ticker if b.symbol else None,
                    "strategy": b.strategy.name if b.strategy else None,
                    "start_date": b.start_date.isoformat() if b.start_date else None,
                    "end_date": b.end_date.isoformat() if b.end_date else None,
                    "initial_capital": b.initial_capital,
                    "final_capital": b.final_capital,
                    "total_return": b.total_return,
                    "total_trades": b.total_trades,
                    "status": b.status,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in backtests
            ]
        }
    finally:
        repo.close()


@app.post("/api/v1/data/ingest")
async def ingest_data(request: DataIngestRequest):
    try:
        service = DataService()
        result = service.ingest_and_persist(
            symbol=request.symbol,
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date),
            timeframe=request.timeframe,
            source=request.source,
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtests/run")
async def run_backtest(request: BacktestRequest):
    try:
        service = BacktestService()
        result = service.run_backtest(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
            parameters=request.parameters,
        )
        return {
            "status": "success",
            "backtest_id": result.backtest_id,
            "strategy": result.strategy,
            "symbol": result.symbol,
            "data_source": result.data_source,
            "results": {
                "final_capital": result.final_capital,
                "total_return": result.total_return,
                "total_trades": result.total_trades,
                "metrics": result.metrics,
                "execution_time_ms": result.execution_time_ms,
            },
            "equity_curve": result.equity_curve,
            "drawdown_series": result.drawdown_series,
            "monthly_returns": result.monthly_returns,
            "trades": result.trades[:10],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtests/compare")
async def compare_strategies(request: CompareRequest):
    try:
        service = BacktestService()
        result = service.compare_strategies(
            strategy_names=request.strategy_names,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/api/v1/backtests/portfolio")
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """Run portfolio backtest with multiple symbols and optional rebalancing."""
    import math

    def clean_nan(value):
        """Replace NaN/Inf values with 0 for JSON serialization."""
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return value
        elif isinstance(value, dict):
            return {k: clean_nan(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_nan(v) for v in value]
        return value

    try:
        service = BacktestService()
        result = service.run_portfolio_backtest(
            strategy_name=request.strategy_name,
            symbols=request.symbols,
            weights=request.weights,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
            rebalance_frequency=request.rebalance_frequency,
            rebalance_threshold=request.rebalance_threshold,
            benchmark_symbol=request.benchmark_symbol,
            parameters=request.parameters,
        )

        # Build equity curve response (limit to 500 points)
        equity_curve = []
        if not result.combined_equity.empty:
            for idx, row in result.combined_equity.iterrows():
                equity_curve.append(
                    {
                        "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                        "total": round(row.get("total", 0), 2),
                    }
                )
            equity_curve = equity_curve[:500]

        response = {
            "status": "success",
            "symbols": result.symbols,
            "weights": result.weights,
            "results": {
                "total_return": result.total_return,
                "total_trades": result.total_trades,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "execution_time_ms": result.execution_time_ms,
            },
            "rebalancing": {
                "events": [e.to_dict() for e in result.rebalance_events[:20]],
                "total_events": len(result.rebalance_events),
                "total_cost": result.total_rebalance_cost,
            },
            "portfolio_metrics": result.portfolio_metrics.to_dict()
            if result.portfolio_metrics
            else None,
            "equity_curve": equity_curve,
            "per_asset_results": {
                symbol: {
                    "total_return": r.total_return,
                    "trades": len(r.trades),
                    "sharpe": r.metrics.sharpe_ratio if r.metrics else 0,
                }
                for symbol, r in result.results.items()
            },
        }

        # Clean NaN values from response
        return clean_nan(response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Optimization Endpoints ====================


def _run_optimization(request: OptimizationRequest, optimizer_cls: type) -> dict:
    """Shared logic for all optimization endpoints."""
    strategy = StrategyRegistry.create(request.strategy_name)
    if strategy is None:
        raise HTTPException(status_code=404, detail=f"Strategy '{request.strategy_name}' not found")

    data_service = DataService()
    start_dt = datetime.fromisoformat(request.start_date)
    end_dt = datetime.fromisoformat(request.end_date)
    df, data_source, _ = data_service.fetch_data(
        request.symbol, start_dt, end_dt, request.timeframe
    )

    opt_config = OptimizationConfig(metric=request.metric)
    optimizer = optimizer_cls(config=opt_config)

    bt_config = BacktestConfig(
        initial_capital=request.initial_capital,
        commission=request.commission,
        slippage=request.slippage,
    )

    if isinstance(optimizer, RandomSearchOptimizer):
        result = optimizer.optimize(
            strategy, df, request.param_grid, n_iter=request.n_iterations, config=bt_config
        )
    else:
        result = optimizer.optimize(strategy, df, request.param_grid, config=bt_config)

    top_results = sorted(
        [r for r in result.all_results if r.get("success")],
        key=lambda x: x["score"],
        reverse=True,
    )[:20]

    return {
        "status": "success",
        "strategy": request.strategy_name,
        "symbol": request.symbol,
        "data_source": data_source,
        "best_params": result.best_params,
        "best_score": result.best_score,
        "total_iterations": result.total_iterations,
        "execution_time_ms": result.execution_time_ms,
        "top_results": top_results,
    }


@app.post("/api/v1/optimization/grid")
async def run_grid_optimization(request: OptimizationRequest):
    """Run grid search parameter optimization."""
    try:
        return _run_optimization(request, GridSearchOptimizer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/api/v1/optimization/random")
async def run_random_optimization(request: OptimizationRequest):
    """Run random search parameter optimization."""
    try:
        return _run_optimization(request, RandomSearchOptimizer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/api/v1/optimization/genetic")
async def run_genetic_optimization(request: OptimizationRequest):
    """Run genetic algorithm parameter optimization."""
    try:
        return _run_optimization(request, GeneticOptimizer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


# ==================== Walk-Forward Endpoint ====================


@app.post("/api/v1/walkforward/run")
async def run_walkforward(request: WalkForwardRequest):
    """Run walk-forward analysis."""
    try:
        strategy = StrategyRegistry.create(request.strategy_name)
        if strategy is None:
            raise HTTPException(
                status_code=404, detail=f"Strategy '{request.strategy_name}' not found"
            )

        data_service = DataService()
        start_dt = datetime.fromisoformat(request.start_date)
        end_dt = datetime.fromisoformat(request.end_date)
        df, data_source, _ = data_service.fetch_data(
            request.symbol, start_dt, end_dt, request.timeframe
        )

        bt_config = BacktestConfig(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
        )

        wfa = WalkForwardAnalysis()
        result = wfa.run(
            strategy_class=type(strategy),
            data=df,
            param_grid=request.param_grid,
            train_days=request.train_days,
            test_days=request.test_days,
            config=bt_config,
        )

        windows = [
            {
                "train_start": w.train_start.isoformat(),
                "train_end": w.train_end.isoformat(),
                "test_start": w.test_start.isoformat(),
                "test_end": w.test_end.isoformat(),
                "best_params": w.best_params,
                "test_return": w.test_return,
                "test_trades": w.test_trades,
            }
            for w in result.windows
        ]

        return {
            "status": "success",
            "strategy": request.strategy_name,
            "symbol": request.symbol,
            "data_source": data_source,
            "train_days": request.train_days,
            "test_days": request.test_days,
            "n_windows": len(windows),
            "avg_train_sharpe": result.avg_train_sharpe,
            "avg_test_sharpe": result.avg_test_sharpe,
            "stability_score": result.stability_score,
            "total_test_return": result.total_test_return,
            "execution_time_ms": result.execution_time_ms,
            "windows": windows,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


# ==================== ML Endpoint ====================


@app.post("/api/v1/ml/train")
async def train_ml_model(request: MLTrainRequest):
    """Train an ML model and run backtest with it."""
    try:
        service = BacktestService()
        result = service.run_backtest(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            initial_capital=request.initial_capital,
            parameters=request.parameters or {},
        )

        return {
            "status": "success",
            "model": request.strategy_name,
            "symbol": request.symbol,
            "data_source": result.data_source,
            "results": {
                "final_capital": result.final_capital,
                "total_return": result.total_return,
                "total_trades": result.total_trades,
                "metrics": result.metrics,
                "execution_time_ms": result.execution_time_ms,
            },
            "equity_curve": result.equity_curve,
            "trades": result.trades[:10],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


# ── Compare must be registered BEFORE /{symbol} so FastAPI doesn't treat "compare" as a symbol
@app.get("/api/v1/fundamentals/compare")
async def compare_fundamentals(
    symbols: str = Query(..., description="Comma-separated symbols, e.g. 'AAPL,MSFT,GOOGL'"),
    source: str = Query("yfinance", description="Data source: 'yfinance' or 'fmp'"),
):
    """Compare fundamental metrics across multiple stocks side-by-side (concurrent fetch)."""
    import asyncio
    import dataclasses
    from concurrent.futures import ThreadPoolExecutor

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 symbols required for comparison")
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols per comparison")

    if source == "fmp" and not os.environ.get("FMP_API_KEY"):
        raise HTTPException(status_code=400, detail="FMP_API_KEY not configured.")

    service = FundamentalService(source=source)

    def _fetch(sym: str) -> tuple:
        try:
            result = service.analyze(sym, include_news=False)
            report = result["report"]
            return sym, {
                "company_name": report.company_name,
                "sector": report.sector,
                "market_cap": report.market_cap,
                "current_price": report.current_price,
                "pe_ratio": report.pe_ratio,
                "pb_ratio": report.pb_ratio,
                "ps_ratio": report.ps_ratio,
                "ev_ebitda": report.ev_ebitda,
                "peg_ratio": getattr(report, "peg_ratio", None),
                "roe": report.roe,
                "roa": report.roa,
                "gross_margin": report.gross_margin,
                "operating_margin": report.operating_margin,
                "net_margin": report.net_margin,
                "debt_to_equity": report.debt_to_equity,
                "current_ratio": report.current_ratio,
                "interest_coverage": getattr(report, "interest_coverage", None),
                "free_cash_flow": report.free_cash_flow,
                "fcf_margin": report.fcf_margin,
                "revenue_cagr_3yr": report.revenue_cagr_3yr,
                "earnings_cagr_3yr": getattr(report, "earnings_cagr_3yr", None),
                "health_score": report.health_score,
                "health_grade": report.health_grade,
                "beta": report.beta,
                "dividend_yield": report.dividend_yield,
                "analyst_rating": report.analyst_rating,
                "piotroski_score": getattr(report, "piotroski_score", None),
                "altman_z_score": getattr(report, "altman_z_score", None),
                "altman_z_zone": getattr(report, "altman_z_zone", None),
            }
        except Exception as e:
            return sym, {"error": str(e)}

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [loop.run_in_executor(executor, _fetch, sym) for sym in symbol_list]
        raw_results = await asyncio.gather(*tasks)

    results = {sym: data for sym, data in raw_results}

    return {
        "status": "success",
        "symbols": symbol_list,
        "comparison": results,
    }


# ── Specific routes /{symbol}/news and /{symbol}/insiders MUST come before /{symbol}
# ── to avoid route shadowing
@app.get("/api/v1/fundamentals/{symbol}")
async def get_fundamentals(
    symbol: str,
    source: str = Query("yfinance", description="Data source: 'yfinance' (free) or 'fmp' (paid)"),
    include_news: bool = Query(True, description="Include news and sentiment data"),
    use_cache: bool = Query(True, description="Use cache (bypassed in production)"),
):
    """Get complete fundamental analysis for a stock.

    Source options:
    - yfinance: Free, good for development (default)
    - fmp: Paid (Financial Modeling Prep), production-grade

    Cache behavior:
    - In development: Respects use_cache parameter
    - In production: Always fetches fresh (use_cache is ignored)
    """
    import dataclasses

    if source == "fmp" and not os.environ.get("FMP_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="FMP_API_KEY not configured. Add it to config/.env to use FMP as data source.",
        )

    try:
        service = FundamentalService(source=source)
        result = service.analyze(symbol.upper(), include_news=include_news, use_cache=use_cache)
        report = result["report"]
        from_cache = result["from_cache"]
        return {"status": "success", "from_cache": from_cache, **dataclasses.asdict(report)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/api/v1/fundamentals/{symbol}/news")
async def get_fundamentals_news(symbol: str):
    """Get only news and sentiment for a stock (lightweight endpoint)."""
    try:
        service = FundamentalService(source="yfinance")
        result = service.analyze(symbol.upper(), include_news=True, use_cache=False)
        report = result["report"]
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "news": report.news,
            "sentiment": report.sentiment,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/api/v1/fundamentals/{symbol}/insiders")
async def get_fundamentals_insiders(
    symbol: str,
    source: str = Query("finnhub", description="Data source: 'finnhub' or 'fmp'"),
):
    """Get insider trading transactions (Form 4 data) for a stock."""
    try:
        from src.infrastructure.data_providers.insider_provider import InsiderProvider

        provider = InsiderProvider(source=source)
        transactions = provider.get_transactions(symbol.upper())
        net_sentiment = provider.compute_net_sentiment(transactions)
        net_buy_value = provider.compute_net_buy_value(transactions)
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "transactions": [t.__dict__ for t in transactions],
            "net_sentiment": net_sentiment,
            "net_buy_value": net_buy_value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None



@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
    )
