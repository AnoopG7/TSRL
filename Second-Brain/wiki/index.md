# TradingBrain — Master Index

## Concepts

### Backtesting
- [[Backtesting]] — Core concept: event-driven vs vectorized engines

### Technical Indicators
- [[EMA Crossover]] — Exponential Moving Average crossover
- [[MACD]] — Moving Average Convergence Divergence
- [[Bollinger Bands]] — Mean reversion with standard deviation bands
- [[RSI]] — Relative Strength Index
- [[MA Ribbon]] — Multiple moving averages

### Risk Metrics
- [[Risk Metrics]] — Sharpe, Sortino, Max Drawdown, VaR, CVaR
- [[Portfolio Metrics]] — Correlation, risk contribution

### Fundamental Analysis
- [[Fundamental Analysis]] — Piotroski F-Score, Altman Z-Score, health scores
- [[Piotroski Score]] — 9-point profitability checklist
- [[Altman Z-Score]] — Bankruptcy prediction

### Strategy Types
- Momentum — Trend-following strategies
- Mean Reversion — Range-bound strategies
- Breakout — Price expansion strategies
- ML Strategies — Machine learning classifiers

## Strategies

| Strategy | Family | Status | Notes |
|----------|--------|--------|-------|
| ema_crossover | Momentum | ✅ Implemented | Fast/slow EMA crossover |
| rsi_mean_reversion | Momentum | ✅ Implemented | RSI oversold/overbought |
| macd | Momentum | ✅ Implemented | MACD crossover |
| ma_ribbon | Momentum | ✅ Implemented | Multiple MA ribbon |
| triple_ma | Momentum | ✅ Implemented | Triple MA crossover |
| volume_profile | Momentum | ✅ Implemented | Volume support/resistance |
| volume_breakout | Momentum | ✅ Implemented | Volume surge |
| breakout | Breakout | ✅ Implemented | Price breakout |
| bollinger_bands | Mean Reversion | ✅ Implemented | BB bounce |
| bbands | Breakout | ✅ Implemented | BB breakout |
| ml_random_forest | ML | ✅ Implemented | RF classifier |
| ml_gradient_boosting | ML | ✅ Implemented | GBM classifier |

## Stocks Tracked

| Ticker | Sector | Status | Last Updated |
|--------|--------|--------|------------|
| AAPL | Technology | Active | |
| MSFT | Technology | Active | |
| GOOGL | Technology | Active | |
| AMZN | Consumer | Active | |
| RELIANCE | India | Active | |

## Research Sources

*Add URLs as you research — one per line*

## Sessions Log

- [[log]] — Session action log

## Quick Links

- [CLAUDE.md](../CLAUDE.md) — Project context
- [docs/system/architecture.md](../docs/system/architecture.md) — System architecture
- [docs/system/strategy-map.md](../docs/system/strategy-map.md) — All strategies
- [graphify-out/GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md) — Graph insights