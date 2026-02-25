from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

from config.settings import get_settings
from src.infrastructure.database.connection import init_db
from src.infrastructure.data_providers.yahoo_provider import YahooFinanceProvider
from src.infrastructure.data_providers.nse_provider import NSEProvider
from src.strategies.registry import StrategyRegistry
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy, RSIMeanReversionStrategy
from scripts.generate_sample_data import generate_sample_ohlcv
from src.engine.backtest.engine import BacktestEngine, BacktestConfig


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Trading Strategy Research Lab",
    description="AI-Powered Trading Strategy Research Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SymbolRequest(BaseModel):
    ticker: str
    exchange: Optional[str] = None


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


class BacktestResponse(BaseModel):
    status: str
    message: str
    backtest_id: Optional[int] = None
    results: Optional[dict] = None


@app.get("/")
async def root():
    return {
        "name": "Trading Strategy Research Lab",
        "version": "0.1.0",
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


@app.post("/api/v1/data/ingest")
async def ingest_data(request: DataIngestRequest):
    try:
        if request.source == "yahoo":
            provider = YahooFinanceProvider()
        elif request.source == "nse":
            provider = NSEProvider()
        else:
            raise HTTPException(status_code=400, detail="Invalid data source")

        df = provider.fetch_ohlcv(
            symbol=request.symbol,
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date),
            timeframe=request.timeframe,
        )

        return {
            "status": "success",
            "symbol": request.symbol,
            "records": len(df),
            "start_date": str(df.index.min()),
            "end_date": str(df.index.max()),
            "columns": list(df.columns),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtests/run")
async def run_backtest(request: BacktestRequest):
    try:
        strategy = StrategyRegistry.create(request.strategy_name, **(request.parameters or {}))
        if strategy is None:
            raise HTTPException(status_code=404, detail="Strategy not found")

        try:
            provider = YahooFinanceProvider()
            df = provider.fetch_ohlcv(
                symbol=request.symbol,
                start_date=datetime.fromisoformat(request.start_date),
                end_date=datetime.fromisoformat(request.end_date),
                timeframe=request.timeframe,
            )
        except Exception:
            start = datetime.fromisoformat(request.start_date)
            end = datetime.fromisoformat(request.end_date)
            n_days = (end - start).days
            df = generate_sample_ohlcv(symbol=request.symbol, n_days=n_days)

        config = BacktestConfig(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
        )

        engine = BacktestEngine(config)
        result = engine.run(strategy, df)

        return {
            "status": "success",
            "strategy": request.strategy_name,
            "symbol": request.symbol,
            "results": {
                "final_capital": result.final_capital,
                "total_return": result.total_return,
                "total_trades": len(result.trades),
                "metrics": result.metrics.to_dict(),
                "execution_time_ms": result.execution_time_ms,
            },
            "trades": [t.to_dict() for t in result.trades[:10]],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
