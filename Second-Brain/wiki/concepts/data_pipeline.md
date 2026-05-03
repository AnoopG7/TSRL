# Data Pipeline

## Definition
The system that transforms raw market data from external providers into clean, validated DataFrames ready for strategy consumption. It handles provider selection, market-specific formatting, error recovery, and persistence.

## Why It Matters
- **Garbage in, garbage out**: A strategy's signals are only as good as the data feeding them
- **Provider reliability**: APIs fail, rate-limit, return partial data — the pipeline must handle all cases
- **Market differences**: Indian stocks need `.NS` suffix, crypto needs `-USD` — wrong format = empty DataFrame

## In My System

### The Fetch Flow

```
DataService.fetch_data(symbol, start, end, timeframe, market)
    ↓
    1. Market-specific symbol formatting
       - US:    "AAPL" → "AAPL"
       - India: "RELIANCE" → "RELIANCE.NS"
       - Crypto: "BTC" → "BTC-USD"
    ↓
    2. Provider selection
       - "yahoo" → YahooFinanceProvider()
       - "alpha_vantage" → AlphaVantageProvider()
    ↓
    3. provider.fetch_ohlcv(symbol, start, end, timeframe)
       → Returns pd.DataFrame with [open, high, low, close, volume]
    ↓
    4. Return (DataFrame, "live", quality_metadata)
```

**Implementation:** `src/application/services/data_service.py:18-92`

---

### Provider Abstraction

All providers inherit from `BaseDataProvider` and implement `fetch_ohlcv()`:

```
BaseDataProvider (abstract)
├── YahooFinanceProvider   — Free, no API key, reliable for US/India/Crypto
├── AlphaVantageProvider   — Paid, 5 calls/min (free tier), historical data
└── FMPFundamentalProvider — Financial Modeling Prep (fundamentals, not OHLCV)
```

**Design pattern:** Strategy pattern — `DataService` instantiates the appropriate provider based on `source` parameter. No factory registry (unlike strategies).

**Why no registry?** Data providers are infrastructure-level, not user-facing. Users pick via API parameter, not discovery.

---

### Symbol Formatting (`data_service.py:44-60`)

```python
if market == "india":
    base_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
                      .replace("NSE:", "").replace("BSE:", "")
    symbol = base_symbol + ".NS"  # Yahoo needs .NS for NSE
elif market == "crypto":
    base = symbol.upper().replace("-USD", "")
    if not base.endswith("-USD"):
        symbol = base + "-USD"
# US: use as-is
```

**Edge cases this handles:**
- User passes `RELIANCE.NS` (already suffixed) → strips and re-adds
- User passes `NSE:RELIANCE` (exchange prefix) → strips prefix
- User passes `BTC-USD` (already suffixed) → doesn't double-suffix

**Edge case NOT handled:**
- `BSE:` stocks on Yahoo (need `.BO` suffix instead of `.NS`)
- Non-Yahoo providers that don't use suffixes

---

### Quality Metadata

Every fetch returns a metadata dict:

```python
{
    "is_simulated": False,   # True if using generated fallback data
    "warning_message": None, # Description of any issues
    "original_exception": None,  # Error that triggered fallback
}
```

**Current state:** No fallback generator exists. If the fetch fails, it raises `ValueError`. The metadata structure is future-proofing for a planned simulated data fallback.

---

### Persistence Path

```python
# data_service.py:94-123
def ingest_and_persist(self, symbol, start, end, ...):
    df, source, quality = self.fetch_data(...)
    repo = OHLCVRepository(session=session)
    records_added = repo.save_ohlcv(symbol, timeframe, df, source=data_source)
```

**When used:** CLI `ingest` command for pre-loading data. The backtest flow does NOT persist data — it fetches on-demand.

---

## Fundamental Data Pipeline (Separate)

Fundamental data (financials, ratios, scores) follows a different path:

```
FundamentalAnalysisService
    → FundamentalCache.get_or_fetch(symbol, data_type)
        → Cache hit? Return cached JSON
        → Cache miss? FMPFundamentalProvider.fetch(symbol)
            → Cache result with TTL
            → Return fresh data
```

**Cache location:** File-based JSON in `data/fundamental_cache/`

**TTL by data type:**
| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Financial statements | 7 days | Updated quarterly |
| Key metrics | 1 day | Can change daily |
| Company profile | 30 days | Rarely changes |
| Stock screener | 1 hour | Real-time data |

---

## Failure Cases & Edge Cases

### 1. Provider API Failure
**Symptom:** `DataProviderError` exception

**Current handling:** Bubbles up as `ValueError` to caller

**Missing:** No retry logic, no fallback to alternative provider

**Fix needed:** Implement provider chain: Yahoo → AlphaVantage → Simulated

### 2. Stale Data
**Symptom:** Backtest on "today" uses yesterday's data

**Cause:** Yahoo's daily data may lag by 15-20 minutes. End-of-day data isn't available until market close.

**Impact:** Intraday backtests may use incomplete bars

### 3. Missing Bars
**Symptom:** Strategy crashes with KeyError on holidays/weekends

**Cause:** No data for non-trading days, but strategy expects continuous series

**Current handling:** Not handled — strategies must handle NaN/missing bars themselves

### 4. Indian Market Suffix
**Symptom:** Empty DataFrame for Indian stocks

**Cause:** Forgot `market="india"` parameter → fetches US ticker (which doesn't exist)

**Example:** `RELIANCE` (without `.NS`) returns no data from Yahoo

---

## Key Insights

### No Caching for OHLCV
The `DataService` fetches fresh data every time. There's no in-memory cache for OHLCV data. For repeated backtests (e.g., optimization with 600 iterations), this means 600 API calls for the same data.

**Optimization path:** Cache the DataFrame in memory keyed by `(symbol, start, end, timeframe)`. The optimizer should fetch once and pass the DataFrame to all iterations (it already does this — the optimizer calls `engine.run()` with pre-fetched data).

### Provider ≠ Source of Truth
The provider is a fetch mechanism, not a data store. For production, the persistence path (`ingest_and_persist`) should be the primary data source, with providers as the refresh mechanism.

### Two-Pipeline Architecture
OHLCV data and fundamental data are completely separate pipelines. They don't share providers, caching, or persistence. This is intentional — they have different update frequencies, data shapes, and quality requirements.

---

## Related Concepts
- [[Caching Strategy]] — How fundamental data is cached (OHLCV is not)
- [[Backtesting]] — The consumer of this pipeline's output
- [[Architecture Decisions]] — Why two pipelines, not one

## Implementation References
- `src/application/services/data_service.py` — OHLCV fetch + persist
- `src/infrastructure/data_providers/base.py` — Provider interface
- `src/infrastructure/data_providers/yahoo_provider.py` — Yahoo implementation
- `src/infrastructure/data_providers/alpha_vantage_provider.py` — AV implementation
- `src/infrastructure/database/repositories/ohlcv_repository.py` — OHLCV persistence
