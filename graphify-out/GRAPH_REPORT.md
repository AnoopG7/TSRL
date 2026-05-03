# Graph Report - /Users/anoop/Developer/Projects/TSRL  (2026-04-29)

## Corpus Check
- 165 files · ~193,833 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2080 nodes · 6385 edges · 109 communities detected
- Extraction: 35% EXTRACTED · 65% INFERRED · 0% AMBIGUOUS · INFERRED: 4133 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)

### Core Architecture (high-density clusters)
- [[_COMMUNITY_Community 0|Strategy Engine & CLI]] — BaseStrategy, all strategy implementations, CLI commands (115 nodes)
- [[_COMMUNITY_Community 1|Fundamental Analysis & Migrations]] — FundamentalReport, providers, DB schema (177 nodes)
- [[_COMMUNITY_Community 2|Backtest Execution Core]] — BacktestConfig, BacktestEngine, orders, risk management (119 nodes)
- [[_COMMUNITY_Community 3|API Responses & Serialization]] — BacktestResponse, equity curves, chart data extraction (90 nodes)
- [[_COMMUNITY_Community 4|Data Providers & Validation]] — BaseDataProvider, Yahoo, NSE, Alpha Vantage (77 nodes)
- [[_COMMUNITY_Community 5|Fundamental Cache Layer]] — FundamentalCache, TTL, comparison endpoints (56 nodes)
- [[_COMMUNITY_Community 6|Database & Persistence]] — BacktestRepository, TradeRepository, session factory (43 nodes)
- [[_COMMUNITY_Community 7|Domain Entities (Core)]] — OHLCV, Signal, RiskManagementResult, from_dict (15 nodes)
- [[_COMMUNITY_Community 8|Risk Metrics Calculator]] — calculate_sharpe, calculate_sortino, all metric functions (26 nodes)
- [[_COMMUNITY_Community 9|ML Feature Engineering]] — FeatureEngineer, FeatureSelector, label generation (12 nodes)
- [[_COMMUNITY_Community 10|Signal System]] — Signal, SignalType, SignalStrength enums (11 nodes)
- [[_COMMUNITY_Community 11|FMP Provider Integration]] — FMPFundamentalProvider, API requests, error handling (28 nodes)
- [[_COMMUNITY_Community 12|App Lifecycle & Registry]] — Strategy registration, auto_discover, FastAPI lifespan (22 nodes)
- [[_COMMUNITY_Community 13|Advanced Risk Metrics]] — VaR, CVaR, Kelly criterion, Omega ratio, Ulcer Index (12 nodes)
- [[_COMMUNITY_Community 14|Symbol & Timeframe]] — Symbol value object, Timeframe enum (9 nodes)
- [[_COMMUNITY_Community 15|CLI Test Suite]] — All CLI command tests (6 nodes)
- [[_COMMUNITY_Community 16|Configuration System]] — Pydantic settings, YAML config classes (17 nodes)

### Frontend Components (small clusters)
- [[_COMMUNITY_Community 18|Currency Formatters]] — formatCurrency utilities
- [[_COMMUNITY_Community 19|Table Sorting]] — getCellValue, rowComparator
- [[_COMMUNITY_Community 22|Chart Tooltips (ComparisonTable)]] — CustomTooltip
- [[_COMMUNITY_Community 23|Alembic Migrations]] — Online/offline migration runners
- [[_COMMUNITY_Community 28|Logging System]] — get_logger, LoggerMixin
- [[_COMMUNITY_Community 29|Test Mocks]] — mock_data_service
- [[_COMMUNITY_Community 39|Theme Toggle]] — ThemeToggle component
- [[_COMMUNITY_Community 40|Loading Spinner]] — Spinner component
- [[_COMMUNITY_Community 41|Loading Skeleton]] — Skeleton component
- [[_COMMUNITY_Community 42|News Card]] — timeAgo, NewsCard
- [[_COMMUNITY_Community 43|Insider Tracker]] — InsiderTracker tooltip
- [[_COMMUNITY_Community 44|Parameter Editor]] — ParameterEditor form
- [[_COMMUNITY_Community 45|App Layout]] — AppLayout navigation
- [[_COMMUNITY_Community 46|EPS Surprise Chart]] — EpsSurpriseChart tooltip
- [[_COMMUNITY_Community 47|Chart Tooltip (shared)]] — ChartTooltip component
- [[_COMMUNITY_Community 48|Radar Score Chart]] — RadarScoreChart component
- [[_COMMUNITY_Community 49|Backtest Page]] — BacktestPage form submission
- [[_COMMUNITY_Community 50|Portfolio Page]] — PortfolioPage form submission
- [[_COMMUNITY_Community 51|Sample Data Generator]] — generate_sample_ohlcv script

### Frontend Config (singletons)
- [[_COMMUNITY_Community 52|Tailwind Config]]
- [[_COMMUNITY_Community 53|ESLint Config]]
- [[_COMMUNITY_Community 54|Vite Config]]
- [[_COMMUNITY_Community 55|PostCSS Config]]
- [[_COMMUNITY_Community 56|App Entry (React)]]
- [[_COMMUNITY_Community 57|Main Entry (React)]]

### Frontend UI (singletons)
- [[_COMMUNITY_Community 58|Card Component]]
- [[_COMMUNITY_Community 59|Skeleton Metric Grid]]
- [[_COMMUNITY_Community 60|Page Footer]]
- [[_COMMUNITY_Community 61|Skeleton Card]]
- [[_COMMUNITY_Community 62|Skeleton Chart]]
- [[_COMMUNITY_Community 63|Metric Card]]
- [[_COMMUNITY_Community 64|Button Variants]]
- [[_COMMUNITY_Community 65|Market Selector]]
- [[_COMMUNITY_Community 66|Button Component]]
- [[_COMMUNITY_Community 67|Select Component]]
- [[_COMMUNITY_Community 68|Quality Scores]]
- [[_COMMUNITY_Community 69|Skeleton Fundamentals]]
- [[_COMMUNITY_Community 70|Data Source Selector]]
- [[_COMMUNITY_Community 71|Header Component]]
- [[_COMMUNITY_Community 72|Financial Trends Chart]]

### Frontend State & API (singletons)
- [[_COMMUNITY_Community 73|Store Index]]
- [[_COMMUNITY_Community 74|API Client]]
- [[_COMMUNITY_Community 75|Constants]]
- [[_COMMUNITY_Community 76|Backtest Schema]]
- [[_COMMUNITY_Community 77|Hooks Index]]
- [[_COMMUNITY_Community 78|Fundamental Schema]]
- [[_COMMUNITY_Community 79|Data Source Store]]
- [[_COMMUNITY_Community 80|Theme Store]]
- [[_COMMUNITY_Community 81|Backtest Store]]
- [[_COMMUNITY_Community 82|Pages Index]]

### Python Package Init (singletons — module boundaries)
- Communities 83–103: Python `__init__.py` module boundary markers

### Portfolio Analytics (edge nodes)
- [[_COMMUNITY_Community 104|Return-to-Drawdown Ratio]] — Alias metric
- [[_COMMUNITY_Community 105|Weight Drift Calculator]] — Per-asset drift
- [[_COMMUNITY_Community 106|Max Drift Threshold]] — Rebalance trigger
- [[_COMMUNITY_Community 107|Diversification Check]] — HHI < 0.25 test
- [[_COMMUNITY_Community 108|Alpha Check]] — Positive alpha validation

## God Nodes (most connected - your core abstractions)
1. `BacktestConfig` - 187 edges
2. `BaseStrategy` - 179 edges
3. `BacktestEngine` - 116 edges
4. `FundamentalReport` - 108 edges
5. `FundamentalService` - 101 edges
6. `EMACrossoverStrategy` - 100 edges
7. `Trade` - 90 edges
8. `PortfolioConfig` - 87 edges
9. `TradeSide` - 86 edges
10. `TradeStatus` - 84 edges

## Surprising Connections (you probably didn't know these)
- `test_sortino_ratio_always_finite()` --calls--> `calculate_sortino_ratio()`  [INFERRED]
  /Users/anoop/Developer/Projects/TSRL/tests/unit/test_properties.py → /Users/anoop/Developer/Projects/TSRL/src/analytics/risk_metrics.py
- `Set, invalidate, get: returns None.` --uses--> `FundamentalCache`  [INFERRED]
  /Users/anoop/Developer/Projects/TSRL/tests/unit/fundamentals/test_fundamental_cache.py → /Users/anoop/Developer/Projects/TSRL/src/infrastructure/data_providers/fundamental_cache.py
- `Integration tests for Fundamentals API endpoints - using mocked data.` --uses--> `FundamentalReport`  [INFERRED]
  /Users/anoop/Developer/Projects/TSRL/tests/integration/test_fundamentals_api.py → /Users/anoop/Developer/Projects/TSRL/src/domain/entities/fundamental.py
- `Return a mock fundamental report for any symbol.` --uses--> `FundamentalReport`  [INFERRED]
  /Users/anoop/Developer/Projects/TSRL/tests/integration/test_fundamentals_api.py → /Users/anoop/Developer/Projects/TSRL/src/domain/entities/fundamental.py
- `Test fundamental analysis API endpoints with mocked data.` --uses--> `FundamentalReport`  [INFERRED]
  /Users/anoop/Developer/Projects/TSRL/tests/integration/test_fundamentals_api.py → /Users/anoop/Developer/Projects/TSRL/src/domain/entities/fundamental.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (115): BaseStrategy, BollingerBandsBreakoutStrategy, BollingerBandsStrategy, List all available strategies., Run strategy parameter optimization., Run walk-forward analysis., Fetch OHLCV data for a symbol., Run portfolio backtest with multiple symbols. (+107 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (177): Initial migration  Revision ID: edb1db2aa774 Revises:  Create Date: 2026-02-27 2, upgrade(), float, FundamentalReport, FundamentalProvider, Fundamental data provider — dual source: yfinance (free) + FMP (paid).  Usage:, Raw financial data collected from a provider., Unified provider that delegates to yfinance (free) or FMP (paid).      Usage: (+169 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (119): AdvancedBacktestConfig, AdvancedBacktestEngine, BacktestConfig, BacktestEngine, BacktestResult, Order, OrderType, RiskManagementConfig (+111 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (90): BacktestResponse, Run backtests for multiple strategies on the same data and return comparison., Extract equity curve as list of {date, equity} dicts., Extract drawdown series as list of {date, drawdown} dicts., Extract monthly returns as list of {year, month, return_pct} dicts., Serializable backtest result for API responses., Persist backtest result to database. Returns backtest_id or None., Run portfolio backtest with multiple symbols.          Args:             strateg (+82 more)

### Community 4 - "Community 4"
Cohesion: 0.03
Nodes (77): ABC, AlphaVantageProvider, BaseDataProvider, DataProviderError, DataValidationError, fetch_ohlcv(), get_recent_price(), get_symbol_info() (+69 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (56): FundamentalCache, get_fundamental_cache(), JSON-based cache for fundamental analysis data.  Fundamental data is expensive t, Clear all fundamental caches., File-backed JSON cache with configurable TTL per data type., Retrieve cached data if within TTL.          Args:             symbol: Stock tic, compare_fundamentals(), drift() (+48 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (43): BacktestRepository, session(), TradeRepository, BacktestService, Base, backtest(), _build_param_grid(), cli() (+35 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (15): from_dict(), generate_signals(), Replace NaN/inf with None for JSON serialization., RiskManagementResult, _sanitize_float(), from_dict(), from_pandas_row(), OHLCV (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (26): calculate_cagr(), calculate_calmar_ratio(), calculate_expectancy(), calculate_max_drawdown(), calculate_monthly_returns(), calculate_profit_factor(), calculate_recovery_time(), calculate_rolling_max_drawdown() (+18 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (12): FeatureEngineer, FeatureSelector, generate_labels(), generate_regime_labels(), select_by_correlation(), select_by_importance(), TestFeatureEngineer, TestFeatureSelector (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (11): create_buy(), create_sell(), Signal, SignalStrength, SignalType, Tests for SignalStrength enum, Tests for Signal dataclass, Tests for SignalType enum (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (28): FMPFundamentalProvider, FundamentalProviderError, Fetch all fundamental data from FMP.          FMP returns pre-computed ratios, s, Make an authenticated GET request to FMP API., Build a unified info dict from FMP endpoints, mapped to yfinance-compatible keys, Convert FMP's list of statement dicts into a pandas DataFrame.          FMP retu, Fetch fundamental data from the configured source., Raised when fundamental data fetch fails. (+20 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (22): strategies(), init_db(), Initialize the database using Alembic migrations.      Runs 'alembic upgrade hea, register(), get_strategy(), lifespan(), list_strategies(), auto_discover() (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (12): _calculate_cvar(), _calculate_gain_to_pain(), _calculate_kelly_criterion(), _calculate_omega_ratio(), _calculate_tail_ratio(), _calculate_ulcer_index(), _calculate_upside_ratio(), _calculate_var() (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (9): from_minutes(), full_ticker(), minutes(), Symbol, Timeframe, Tests for Symbol value object, Tests for Timeframe enum, TestSymbol (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (6): Tests for all CLI commands in src/cli.py., TestBacktestCommand, TestFetchDataCommand, TestOptimizeCommand, TestStrategiesCommand, TestWalkForwardCommand

### Community 16 - "Community 16"
Cohesion: 0.19
Nodes (17): BaseModel, BaseSettings, APIConfig, BacktestConfig, CacheConfig, DatabaseConfig, DataProvidersConfig, from_yaml() (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.2
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (2): formatCurrency(), formatLargeCurrency()

### Community 19 - "Community 19"
Cohesion: 0.29
Nodes (2): getCellValue(), rowComparator()

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (2): CustomTooltip(), formatCurrency()

### Community 23 - "Community 23"
Cohesion: 0.4
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 24 - "Community 24"
Cohesion: 0.4
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 0.4
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 0.4
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 0.4
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 0.5
Nodes (3): get_logger(), logger(), LoggerMixin

### Community 29 - "Community 29"
Cohesion: 0.5
Nodes (2): mock_data_service(), Mock DataService to prevent slow network calls during API tests.

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 0.67
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 0.67
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 0.67
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 0.67
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 0.67
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (0): 

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (0): 

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (0): 

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (0): 

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (0): 

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (0): 

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (0): 

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (0): 

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (0): 

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (0): 

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (0): 

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (0): 

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (0): 

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (0): 

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (0): 

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (0): 

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (0): 

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (0): 

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (0): 

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (0): 

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (0): 

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (0): 

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (0): 

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (0): 

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (0): 

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (1): Alias for return_to_drawdown ratio.

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): Calculate weight drift for each asset.

### Community 106 - "Community 106"
Cohesion: 1.0
Nodes (1): Maximum weight drift across all assets.

### Community 107 - "Community 107"
Cohesion: 1.0
Nodes (1): Check if portfolio is well-diversified (HHI < 0.25).

### Community 108 - "Community 108"
Cohesion: 1.0
Nodes (1): Check if portfolio has positive alpha.

## Knowledge Gaps
- **91 isolated node(s):** `Create a temporary cache directory.`, `Create cache instance with short TTL for testing.`, `Finnhub response is normalized to our schema.`, `Unexpected response type (not a list) → empty list.`, `Network error on news fetch → empty list, no crash.` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 39`** (2 nodes): `ThemeToggle()`, `ThemeToggle.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `Spinner()`, `Spinner.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (2 nodes): `Skeleton()`, `Skeleton.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (2 nodes): `timeAgo()`, `NewsCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (2 nodes): `CustomTooltip()`, `InsiderTracker.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `handleChange()`, `ParameterEditor.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (2 nodes): `navLinkClass()`, `AppLayout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (2 nodes): `CustomTooltip()`, `EpsSurpriseChart.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `ChartTooltip()`, `ChartTooltip.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `RadarScoreChart()`, `RadarScoreChart.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `onSubmit()`, `BacktestPage.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `onSubmit()`, `PortfolioPage.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `generate_sample_ohlcv()`, `generate_sample_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `tailwind.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `eslint.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `card.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `SkeletonMetricGrid.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `PageFooter.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `SkeletonCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `SkeletonChart.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `MetricCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `button-variants.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `MarketSelector.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `select.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `QualityScores.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `SkeletonFundamentals.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `DataSourceSelector.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Header.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `FinancialTrendsChart.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `api.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `constants.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `backtest.schema.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `fundamental.schema.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `useDataSourceStore.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `useThemeStore.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `useBacktestStore.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `Alias for return_to_drawdown ratio.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `Calculate weight drift for each asset.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 106`** (1 nodes): `Maximum weight drift across all assets.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 107`** (1 nodes): `Check if portfolio is well-diversified (HHI < 0.25).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 108`** (1 nodes): `Check if portfolio has positive alpha.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseStrategy` connect `Community 2` to `Community 0`, `Community 3`, `Community 4`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `BacktestConfig` connect `Community 3` to `Community 0`, `Community 2`, `Community 4`, `Community 6`, `Community 13`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `FundamentalService` connect `Community 1` to `Community 0`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 185 inferred relationships involving `BacktestConfig` (e.g. with `TestOptimizationConfig` and `TestOptimizationResult`) actually correct?**
  _`BacktestConfig` has 185 INFERRED edges - model-reasoned connections that need verification._
- **Are the 162 inferred relationships involving `BaseStrategy` (e.g. with `TestRiskMetricsProperties` and `TestTradeProperties`) actually correct?**
  _`BaseStrategy` has 162 INFERRED edges - model-reasoned connections that need verification._
- **Are the 107 inferred relationships involving `BacktestEngine` (e.g. with `MockStrategy` and `TestBacktestConfig`) actually correct?**
  _`BacktestEngine` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 106 inferred relationships involving `FundamentalReport` (e.g. with `TestPiotroski` and `Tests for Piotroski F-Score in FundamentalService.`) actually correct?**
  _`FundamentalReport` has 106 INFERRED edges - model-reasoned connections that need verification._