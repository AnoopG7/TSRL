# TradingBrain — LLM Wiki Schema

## Purpose

Research wiki for the TSRL trading project. Tracks:
- Financial concepts and indicators
- Strategy documentation
- Stock research (NSE/BSE focus)
- Backtest results and learnings
- Market research and articles

## Folder Structure

```
wiki/
├── concepts/      → indicators, metrics, financial terms
├── strategies/   → one page per strategy (implemented + researched)
├── stocks/       → one page per stock being tracked
├── sessions/     → important session outputs worth keeping
├── syntheses/    → cross-cutting analyses
├── index.md      → master catalog, update after every ingest
└── log.md        → append-only log: ## [DATE] action | title
```

## Stock Page Template

```markdown
# TICKER — Company Name

**Sector**: | **Exchange**: NSE/BSE | **Last updated**:
## Investment thesis
## Key metrics (latest)
| Metric | Value | Source | Date |
## Technical levels
- Support: 
- Resistance: 
- Current trend:
## Fundamental health
- Piotroski Score: /9
- Altman Z-Score:
- Screener.in link:
## Backtest results (if any)
## News & catalysts
## Risks
## Sources
```

## Ingest Workflow

When I give you a source to process:
1. Read it, discuss key takeaways with me
2. Create or update the relevant wiki page
3. Update index.md
4. Update any related pages that this source adds to
5. Flag any contradictions with existing pages
6. Append to log.md: `## [DATE] ingest | [source title]`

## Query Workflow

When I ask a question:
1. Check index.md for relevant pages
2. Read those pages
3. Answer with citations to wiki pages
4. If the answer is valuable, offer to save it as a new synthesis page

## Lint Reminders (run monthly)

- Orphan pages (in wiki/ but not in index.md)
- Outdated metrics (stock data older than 3 months)
- Contradictions between strategy pages and backtest results

## Do NOT Do

- Never edit files in raw/
- Never skip updating index.md
- Never create a stock page without the full template
- Never delete log.md entries