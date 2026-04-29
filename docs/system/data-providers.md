# Data Providers

## Available Providers

| Provider | File | Data Source | Use Case |
|----------|------|-------------|----------|
| `YahooProvider` | `yahoo_provider.py` | Yahoo Finance (yfinance) | Primary OHLCV data for US stocks |
| `NSEProvider` | `nse_provider.py` | NSE India (nsetools) | Indian stock data |
| `AlphaVantageProvider` | `alpha_vantage_provider.py` | Alpha Vantage API | Sentiment, forex, commodities |
| `FundamentalProvider` | `fundamental_provider.py` | Yahoo Finance | Fundamentals, financials |
| `NewsProvider` | `news_provider.py` | Finnhub API | Company news |
| `InsiderProvider` | `insider_provider.py` | Finnhub/FMP/SEC EDGAR | Insider trading data |

## Provider Architecture

### Base Class
All providers inherit from `BaseProvider` (`src/infrastructure/data_providers/base.py`):

```python
class BaseProvider:
    def fetch(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame: ...
    def get_latest(self, symbol: str) -> Optional[OHLCV]: ...
    def search(self, query: str) -> list[Symbol]: ...
```

### Factory Pattern
Provider selection via factory (`src/infrastructure/data_providers/factory.py`):
```python
from src.infrastructure.data_providers.factory import DataProviderFactory

provider = DataProviderFactory.create("yahoo")  # Returns YahooProvider
```

## Caching Layers

1. **OHLCV Cache** (`cache.py`): TTL-based caching for price data
2. **Fundamental Cache** (`fundamental_cache.py`): 1-hour TTL for fundamentals

## Environment Variables Required

```bash
# config/.env
FINNHUB_API_KEY=          # News, EPS, insider data (free: 60 calls/min)
ALPHA_VANTAGE_API_KEY=    # Sentiment scoring (free: 500 calls/day)
SEC_EDGAR_USER_AGENT=   # SEC EDGAR insider data (free)
FMP_API_KEY=            # Financial Modeling Prep (paid, production)
```

## Data Flow

```
Provider.fetch(symbol, start_date, end_date)
    ↓
[Cache check] → hit → return cached data
    ↓ miss
_provider.fetch_ohlcv() → pd.DataFrame
    ↓
[Cache storage] → return DataFrame
```

## Key Methods by Provider

### YahooProvider
- `fetch_ohlcv()` - Fetch OHLCV data
- `get_ticker_info()` - Get metadata (market cap, P/E, etc.)

### NSEProvider
- `get_quote()` - Get NSE quote
- `get_index_members()` - Get index constituents

### FundamentalProvider
- `fetch()` - Get full fundamentals (income, balance sheet, cash flow)
- `fetch_quarterly()` - Get quarterly data

### NewsProvider
- `get_company_news()` - Fetch recent news
- `get_sentiment()` - Get sentiment score

### InsiderProvider
- `get_transactions()` - Get Form 4 insider transactions
- Falls back: Finnhub → Alpha Vantage → SEC EDGAR