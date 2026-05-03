# Caching Strategy

## Definition
How TSRL manages data freshness vs. performance for different data types. The system has two distinct caching philosophies: no cache for OHLCV, file-based TTL cache for fundamentals.

## Why It Matters
- **API rate limits**: FMP free tier allows 250 calls/day. Without cache, a comparison of 5 stocks burns 10 calls
- **Stale data risk**: Cached financial statements from 7 days ago are fine. Cached price from 7 days ago is dangerous.
- **User experience**: Fundamental analysis page loads in <200ms from cache vs 2-3s from API

## In My System

### OHLCV Data: No Cache (By Design)

`DataService.fetch_data()` hits the provider on every call.

**Why:** 
- Each backtest should be reproducible with the latest available data
- The optimizer handles redundancy internally (fetches once, passes DataFrame to all iterations)
- Price data changes every day — any cache would need daily invalidation

**Optimization shortcut:** The `BacktestService.compare_strategies()` method fetches data once and passes it to multiple engines:

```python
# backtest_service.py:150-153
df, data_source, _ = self.data_service.fetch_data(symbol, start_dt, end_dt, timeframe)
# One fetch, used by all strategies in the comparison
for name in strategy_names:
    engine = BacktestEngine(config)
    result = engine.run(strategy, df)  # Same df, different strategy
```

---

### Fundamental Data: File-Based JSON Cache

The `FundamentalCache` stores API responses as JSON files with type-specific TTLs.

**Cache structure:**
```
data/fundamental_cache/
├── AAPL/
│   ├── financial_statements_2026-04-30.json
│   ├── key_metrics_2026-04-30.json
│   └── company_profile_2026-04-15.json
└── RELIANCE/
    └── ...
```

**TTL configuration:**

| Data Type | TTL | Why |
|-----------|-----|-----|
| Financial statements | 7 days | Quarterly updates, unlikely to change mid-quarter |
| Key metrics / ratios | 1 day | Derived from price data, changes daily |
| Company profile | 30 days | Rarely changes (sector, description) |
| Stock screener | 1 hour | Real-time market data |
| Earnings calendar | 1 day | Event-driven, updates as earnings approach |

**Cache logic:**
```python
# Pseudocode for FundamentalCache.get_or_fetch()
cached = load_from_file(symbol, data_type)
if cached and not expired(cached.timestamp, ttl[data_type]):
    return cached.data
else:
    fresh = provider.fetch(symbol, data_type)
    save_to_file(symbol, data_type, fresh, timestamp=now)
    return fresh
```

---

## Cache Invalidation

### Automatic (TTL-based)
Each cache entry has a timestamp. On read, compare `now - timestamp > ttl`. If expired, re-fetch.

### Manual
Delete the cache file. No API endpoint for cache bust — it's file-level:
```bash
rm -rf data/fundamental_cache/AAPL/
```

### No Invalidation on Write
If you persist backtest results, the OHLCV cache (which doesn't exist) isn't affected. If fundamental data changes upstream, you wait for TTL expiry.

---

## Failure Cases & Edge Cases

### 1. Stale Fundamental Data During Earnings
**Symptom:** Financial statements cached 5 days ago, earnings just released

**Impact:** Analysis uses pre-earnings numbers for 2 more days until TTL expires

**Mitigation:** Reduce financial statements TTL to 1 day during earnings season. Not implemented — manual cache clear is the current workaround.

### 2. Cache Corruption
**Symptom:** JSON parse error on cached file

**Cause:** Interrupted write, disk full, encoding issue

**Current handling:** Likely crashes with unhandled exception

**Fix needed:** Wrap cache reads in try/except, delete corrupt files, re-fetch

### 3. Disk Space Growth
**Symptom:** `data/fundamental_cache/` grows unbounded

**Cause:** No eviction policy — old cache files accumulate forever

**Impact:** Negligible for <100 symbols. Could matter for screener workloads covering 1000+ symbols.

---

## Key Insights

### Why Not Redis?
Same reason as SQLite over Postgres: zero-dependency deployment. File-based cache works for single-user, single-process workloads. If TSRL becomes multi-user, a proper cache layer (Redis, Memcached) should replace file-based caching.

### The Optimizer Doesn't Need Cache
The optimizer receives a pre-fetched DataFrame and runs 600+ backtests against it. The bottleneck is compute (strategy evaluation), not I/O (data fetching). Adding OHLCV cache would save ~2 seconds on the first fetch but add cache invalidation complexity.

### Cache Is a Feature Gate
The fundamental analysis comparison feature would be unusable without cache — 5 symbols × 3 data types = 15 API calls × 2-3 seconds = 45-second page load. With cache: <200ms.

---

## Related Concepts
- [[Data Pipeline]] — The fetch system that populates the cache
- [[Architecture Decisions]] — ADR-7: Why two cache systems
- [[Fundamental Analysis]] — The primary consumer of cached data

## Implementation References
- `src/application/services/data_service.py` — OHLCV fetch (no cache)
- `src/infrastructure/cache/fundamental_cache.py` — File-based TTL cache
- `src/application/services/backtest_service.py:150-153` — Shared fetch optimization
