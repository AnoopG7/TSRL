from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from config.settings import get_settings
from src.infrastructure.database.connection import init_db
from src.infrastructure.database.repositories import BacktestRepository
from src.strategies.registry import StrategyRegistry

# Import strategies to trigger @register_strategy decorators
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy, RSIMeanReversionStrategy  # noqa
from src.strategies.momentum.macd_strategy import MACDStrategy  # noqa
from src.strategies.momentum.ma_ribbon import MovingAverageRibbonStrategy, TripleMAStrategy  # noqa
from src.strategies.momentum.volume_strategies import VolumeProfileStrategy, VolumeBreakoutStrategy  # noqa
from src.strategies.mean_reversion.bollinger_bands import BollingerBandsStrategy, BollingerBandsBreakoutStrategy  # noqa

from src.application.services.backtest_service import BacktestService
from src.application.services.data_service import DataService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
