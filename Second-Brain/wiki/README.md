# TSRL Wiki Export

This folder contains template files to copy into your Obsidian vault.

## Quick Start

### Step 1: Copy to Obsidian

Copy the entire `wiki-export/` folder into your Obsidian vault directory.

### Step 2: Customize

Edit `index.md` to add your tracked stocks.

### Step 3: Start Researching

- Add sources to `index.md` → Research Sources
- Create stock pages using `schema/CLAUDE.md` template
- Update `log.md` after each session

## Daily Workflow

### Start of Session

```bash
# Query the graph for context
graphify query "what did we work on last?"

# Start coding with reduced token usage
```

### End of Session

```bash
# Update the graph after code changes
graphify --update

# Log the session
# Edit wiki-export/log.md
```

## File Structure

```
wiki-export/
├── index.md              # Master index
├── log.md               # Session log
├── concepts/
│   ├── backtesting.md
│   ├── portfolio_metrics.md
│   └── risk_metrics.md
├── strategies/
│   ├── ema_crossover.md
│   ├── macd_strategy.md
│   └── bollinger_bands.md
└── schema/
    └── CLAUDE.md        # Wiki schema for stock pages
```

## Key Links

- [CLAUDE.md](../CLAUDE.md) — Project context
- [docs/system/](../docs/system/) — System architecture docs
- [graphify-out/](../graphify-out/) — Graph output (after running graphify)

## Token Savings

With Graphify:
- First run: ~3000 tokens (extract code structure)
- Subsequent runs: ~200 tokens (incremental update)
- Queries: ~100 tokens per question

Without Graphify:
- Each session: ~5000+ tokens (read entire codebase)