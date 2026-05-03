# Session Log

*Append-only log of research and development sessions*

Format: `## [YYYY-MM-DD] action | title`

---

## 2026-04-30 build | Comprehensive wiki expansion

Transformed wiki from basic documentation to decision-making intelligence layer:

### New Concept Notes (Deep, Actionable)
- [[Backtesting]] — Event-driven vs vectorized, look-ahead bias fixes, failure modes
- [[Risk Metrics]] — 50+ metrics with formulas, edge cases, interpretation guides
- [[Portfolio Metrics]] — Correlation, beta/alpha, risk contribution, diversification ratio
- [[Strategy Design]] — 8 principles for robust strategies, edge cases, look-ahead prevention
- [[Walk-Forward Analysis]] — OOS validation, overfitting detection, parameter stability
- [[ML Pipeline]] — 116 features, label engineering, leakage prevention, model selection
- [[Fundamental Analysis]] — Health scores, Piotroski F-Score, Altman Z-Score, valuation

### Enhanced Strategy Notes
- [[EMA Crossover]] — Parameter sensitivity, whipsaw avoidance, regime dependence
- [[MACD Strategy]] — Three signal types, histogram leading, comparison to EMA cross
- [[Bollinger Bands]] — Band walk patterns, squeeze/breakout, mean reversion vs trend

### Key Improvements
1. **Connected to code** — Every note references actual implementation files
2. **Failure cases** — Each concept includes edge cases and mitigation strategies
3. **Decision frameworks** — When to use, when to avoid, parameter selection
4. **Key insights** — Hard-won trading wisdom, not textbook definitions
5. **Cross-links** — Dense network of [[internal links]] for navigation

### Structure
```
wiki/
├── index.md — Master index with quick reference
├── log.md — This session log
├── concepts/
│   ├── backtesting.md
│   ├── risk_metrics.md
│   ├── portfolio_metrics.md
│   ├── strategy_design.md
│   ├── walk_forward_analysis.md
│   ├── ml_pipeline.md
│   └── fundamental_analysis.md
├── strategies/
│   ├── ema_crossover.md
│   ├── macd_strategy.md
│   └── bollinger_bands.md
└── schema/
    └── CLAUDE.md
```

### Design Principles Applied
- No generic textbook content — every note must be useful for decisions
- Depth over breadth — detailed failure modes, not surface-level definitions
- Code-connected — references to actual implementation files
- Pattern-based — reusable frameworks, not one-off facts
- Dense but scannable — tables, code blocks, clear headers

---

## 2026-04-30 build | Graphify rename + Intelligence layer expansion

### Graphify Community Renaming
Renamed all 109 communities from generic `Community N` to semantic domain names:
- Core Architecture clusters: Strategy Engine & CLI, Backtest Execution Core, API Responses, Data Providers, etc.
- Frontend Components: Named by function (Theme Toggle, Loading Spinner, Chart Tooltips)
- Portfolio Analytics: Return-to-Drawdown Ratio, Weight Drift, Diversification Check
- Python Package Init: Collapsed as module boundary markers (Communities 83–103)

### New Wiki Notes (12 notes, decision-oriented)

**Concepts (9):**
- [[Event System]] — Bar-by-bar event loop, pending signal mechanism, exit priority chain
- [[Trade Lifecycle]] — Signal → position → execution costs → P&L flow, cost model
- [[Optimization]] — Grid/Random/Genetic optimizers, overfitting problem, metric selection
- [[Position Sizing]] — Fixed fractional vs ATR-based gap, Kelly criterion math, 2% rule
- [[Data Pipeline]] — Provider abstraction, market-specific symbol formatting, two-pipeline architecture
- [[Architecture Decisions]] — 8 ADRs: Clean Architecture, dual engines, registry, SQLite, Zustand
- [[Caching Strategy]] — No cache for OHLCV (intentional), file-based TTL for fundamentals
- [[Domain Model]] — Entity catalog, design principles, Signal entity unused gap
- [[Regime Detection]] — Strategy selection matrix, ML labels, ADX/volatility detection

**Strategies (3):**
- [[Breakout]] — Channel breakout with ATR signal strength, false breakout analysis
- [[Volume Strategies]] — Volume Profile + Volume Breakout, asymmetric buy/sell logic
- [[MA Ribbon]] — Triple MA alignment, trend structure, regime proxy

### Refinements
- [[Backtesting]] — Added Advanced Engine section (stop-loss/TP/trailing), expanded links
- [[index.md]] — Reorganized into 6 categories, added all 12 new notes

### Wiki Stats
- Total notes: 22 (was 10)
- Average cross-links per note: 6-8
- Coverage: Execution, risk, data, architecture, ML, strategy categories

---
