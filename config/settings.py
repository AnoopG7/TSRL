from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    path: str = "data/trading_lab.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class YahooConfig(BaseModel):
    enabled: bool = True
    default_timeframe: str = "1d"
    max_retries: int = 3
    retry_delay: int = 1


class NSEConfig(BaseModel):
    enabled: bool = True
    default_timeframe: str = "1d"
    max_retries: int = 3
    retry_delay: int = 1


class DataProvidersConfig(BaseModel):
    yahoo: YahooConfig = YahooConfig()
    nse: NSEConfig = NSEConfig()


class CacheConfig(BaseModel):
    enabled: bool = True
    ttl_hours: int = 24
    cache_dir: str = "data/cache"


class BacktestConfig(BaseModel):
    default_capital: float = 100000.0
    default_commission: float = 0.001
    default_slippage: float = 0.0005
    default_timeframe: str = "1d"


class RiskConfig(BaseModel):
    default_risk_per_trade: float = 0.02
    max_position_size: float = 0.2
    max_drawdown_limit: float = 0.25
    max_daily_loss: float = 0.05


class OptimizationConfig(BaseModel):
    n_jobs: int = -1
    cv_folds: int = 5
    default_iterations: int = 100
    random_state: int = 42


class MLConfig(BaseModel):
    test_size: float = 0.2
    random_state: int = 42
    default_model_path: str = "data/models/"
    feature_cache_ttl: int = 3600


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    output_dir: str = "logs"
    rotation: str = "daily"
    retention: int = 30


class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1


class PaperTradingConfig(BaseModel):
    initial_capital: float = 100000.0
    simulated_latency_ms: int = 100
    enable_order_simulation: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TRADING_LAB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database: DatabaseConfig = DatabaseConfig()
    data_providers: DataProvidersConfig = DataProvidersConfig()
    cache: CacheConfig = CacheConfig()
    backtest: BacktestConfig = BacktestConfig()
    risk: RiskConfig = RiskConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    ml: MLConfig = MLConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()
    paper_trading: PaperTradingConfig = PaperTradingConfig()

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> "Settings":
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            return cls()

        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


@lru_cache
def get_settings() -> Settings:
    config_path = Path(__file__).parent / "settings.yaml"
    return Settings.from_yaml(config_path)
