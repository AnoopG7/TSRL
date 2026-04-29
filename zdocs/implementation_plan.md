# Fundamental Analysis Module — Phase 2 Enhancement Plan

## Overview

This document covers 8 enhancements to the Fundamental Analysis module. The existing backend
(`FundamentalService`, `FundamentalProvider`, `NewsProvider`) and frontend (`FundamentalsPage`,
`RatioTable`, `HealthScoreGauge`, `RadarScoreChart`, `FinancialTrendsChart`) serve as the base.

---

## Item 1 — Navigation: Module-Level Category Tabs

### Problem
All analysis types (Backtest, Compare, Portfolio, Optimization, Walk-Forward, Fundamentals) are
presented as peer tabs in the same flat nav bar. As the app grows this becomes cluttered, and
there's no conceptual grouping between "quantitative backtest tools" and "fundamental analysis."

### Solution: Grouped Navigation with Category Headers

#### [MODIFY] [AppLayout.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/layout/AppLayout.tsx)
Split the flat list of `NavLink` items into two labelled groups:

```
┌─────────────────────────────────────────────────────┐
│  TSRL  ─────────────────────────────  [theme toggle] │
├──── QUANTITATIVE ─────────────────── FUNDAMENTAL ───┤
│  Backtest │ Compare │ Portfolio │ Opt │ Walk-Forward  ║  Fundamentals  │
└─────────────────────────────────────────────────────┘
```

- Groups are separated by a faint vertical rule with an uppercase label `QUANT` / `FUNDAMENTAL`
  rendered in `var(--color-text-tertiary)` at `0.65rem`
- Active group label gets a subtle accent colour tint
- No routing changes needed — `NavLink` `app-tab-active` class already handles the underline

#### [MODIFY] [theme.css](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/styles/theme.css)
Add `.app-tabs-group` and `.app-tabs-separator` classes for group dividers. No breaking changes to
existing `.app-tab` / `.app-tab-active`.

---

## Item 2 — Multi-Ticker Search & Comparison Mode

### Problem
Search bar accepts a single ticker. When multiple tickers are entered nothing happens.

### Solution

#### Frontend — [MODIFY] [FundamentalsPage.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/pages/FundamentalsPage.tsx)
- Parse `searchInput` on submit: split on `,` or spaces, filter empty, uppercase, max 5 tickers
- If **1 ticker** → existing single-analysis flow (calls `useFundamentals`)
- If **2–5 tickers** → switches to **comparison mode**, calls `useCompareFundamentals` (already defined in `apiHooks.ts`)
- Show **tag chips** in the input as each ticker is confirmed (pill UI)
- Comparison mode renders a new `ComparisonTable` component (see Item 6) instead of the 4-tab layout

#### Backend — [MODIFY] [main.py](file:///Users/anoop/Developer/Projects/TSRL/src/main.py)
The `/api/v1/fundamentals/compare` endpoint already exists. It needs to:
- Accept `symbols` query param as comma-separated string
- Run `FundamentalService.analyze()` concurrently (using `asyncio.gather`) per symbol
- Return the `FundamentalComparison` schema (already drafted in `fundamental.schema.ts`)

#### [NEW] [ComparisonTable.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/fundamentals/ComparisonTable.tsx)
Side-by-side metrics table. Columns = tickers, rows = key ratios. Winning value highlighted in
`var(--color-positive)`.

---

## Item 3 — API Keys in .env

### Problem
`config/.env` only has `ALPHA_VANTAGE_API_KEY`. `FINNHUB_API_KEY` and `FMP_API_KEY` are
referenced in code but missing from the file.

### Solution

#### [MODIFY] [config/.env](file:///Users/anoop/Developer/Projects/TSRL/config/.env)
```env
# ── Existing ──────────────────────────────────────────
ALPHA_VANTAGE_API_KEY=H204V3BOKZ575M7X

# ── Fundamental Analysis (add your keys below) ────────
FINNHUB_API_KEY=           # Free at finnhub.io — used for company news
FMP_API_KEY=               # Paid at financialmodelingprep.com — for production data

# ── Insider Trading ──────────────────────────────────
SEC_EDGAR_USER_AGENT=YourName yourname@email.com   # Required by SEC, totally free
```

#### [MODIFY] [config/settings.py or wherever Settings is defined]
Ensure all three keys are optional fields with `None` default so the server doesn't crash without them.

---

## Item 4 — Insider Trading Tracker

### Deep-Dive Knowledge

**What is it?**  
SEC requires all corporate insiders (directors, officers, 10%+ shareholders) to file **Form 4**
within 2 business days of any trade. This is public data and a significant alpha signal:
- Insider **buys** → management has conviction the stock is undervalued
- Insider **sells** → could be routine or a warning sign (context matters)

**Where does the data come from?**

| Source | Cost | Quality | What you get |
|--------|------|---------|--------------|
| **SEC EDGAR** | Free | Gold-standard (official) | Raw XML Form 4 filings |
| **Finnhub** `/insider-transactions` | Free (25 req/day) | Parsed, clean JSON | Insider name, shares, value, type |
| **FMP** `/insider-trading` | Paid | Production-grade | Full details + acquisition notes |

**Recommended approach:** Use Finnhub (free) in dev, FMP in production — consistent with the
existing hybrid provider pattern.

**Data per transaction:**
- `name` — insider's name
- `position` — CFO, CEO, Director, etc.
- `transaction_type` — `P` (purchase) or `S` (sale)
- `shares` — number of shares
- `price` — trade price per share
- `value` — total dollar value
- `date` — filing date

**What signals matter?**
- **Cluster buying** — multiple insiders buying within weeks ← strongest bullish signal
- **CEO buying > $1M** ← very meaningful
- **Routine 10b5-1 sales** ← pre-planned, less meaningful (noted in FMP data)

### Implementation Plan

#### Backend

##### [NEW] [insider_provider.py](file:///Users/anoop/Developer/Projects/TSRL/src/infrastructure/data_providers/insider_provider.py)
```python
class InsiderProvider:
    """Fetches Form 4 insider transaction data.
    Sources: Finnhub (free) / FMP (paid).
    """
    def get_transactions(self, symbol: str, limit: int = 20) -> list[InsiderTransaction]
```

`InsiderTransaction` dataclass fields:
```python
@dataclass
class InsiderTransaction:
    name: str
    position: str
    transaction_type: str        # "P" or "S"
    shares: int
    price: float
    value: float
    date: str
    is_10b5_plan: bool = False   # Pre-planned routine sale — less significant
```

##### [MODIFY] [fundamental_service.py](file:///Users/anoop/Developer/Projects/TSRL/src/application/services/fundamental_service.py)
Add `_populate_insider_data()` method:
- Calls `InsiderProvider.get_transactions()`
- Computes a **Net Insider Sentiment** score: `(buy_count - sell_count) / total_count`
- Computes **Net Buy Value** (total $ bought - total $ sold) over 6 months
- Attaches to `FundamentalReport.insider_transactions` and `FundamentalReport.insider_sentiment`

##### [MODIFY] [fundamental.py (domain entity)](file:///Users/anoop/Developer/Projects/TSRL/src/domain/entities/fundamental.py)
Add fields:
```python
insider_transactions: list[dict] = field(default_factory=list)
insider_net_sentiment: Optional[float] = None    # +1.0 = all buys, -1.0 = all sells
insider_net_buy_value: Optional[float] = None    # Net $ over 6 months
```

##### [MODIFY] [main.py](file:///Users/anoop/Developer/Projects/TSRL/src/main.py)
`GET /api/v1/fundamentals/{symbol}/insiders` — dedicated endpoint for on-demand insider data
(separated from the main analysis because it has its own cache TTL of ~4 hours).

#### Frontend

##### [NEW] [InsiderTracker.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/fundamentals/InsiderTracker.tsx)
- **Summary bar** at top: Net Buy Value chip, Buy/Sell ratio pill, 6-month momentum indicator
- **Transaction table**: columns `Date | Insider | Role | Type | Shares | Value`
  - `P` (Purchase) rows tinted green; `S` (Sale) rows tinted red
  - `10b5-1` sales shown with a muted `[PLANNED]` badge
- **Timeline mini-chart**: a `ComposedChart` with green bars (buys) and red bars (sells) by month

##### [MODIFY] [FundamentalsPage.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/pages/FundamentalsPage.tsx)
Add 5th tab: `Insiders` with lock icon (`Lock` from lucide-react)

##### [MODIFY] [fundamental.schema.ts](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/lib/schemas/fundamental.schema.ts)
Add `InsiderTransactionSchema` and extend `FundamentalReportSchema`.

---

## Item 5 — Piotroski F-Score, Altman Z-Score & EPS Surprise

### Knowledge

#### Piotroski F-Score (0–9)
A 9-point binary checklist published by Prof. Joseph Piotroski (2000).
Each criterion = 1 point if met, 0 if not. Scores 7–9 = strong fundamentals.

| # | Criterion | What it checks |
|---|-----------|----------------|
| 1 | ROA > 0 | Profitable |
| 2 | Operating CF > 0 | Cash-positive |
| 3 | ROA increased YoY | Improving profitability |
| 4 | Accruals < 0 (CF/Assets > ROA) | High earnings quality |
| 5 | Leverage decreased | Less risky |
| 6 | Current Ratio improved | More liquid |
| 7 | No new share issuance | Shareholder-friendly |
| 8 | Gross Margin improved | Pricing power |
| 9 | Asset Turnover improved | Operational efficiency |

All 9 inputs derive from **consecutive year balance sheet + income statement** data we already fetch.

#### Altman Z-Score
Formulated by Edward Altman (1968). Predicts bankruptcy within 2 years.
> Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5

Where:
- X1 = Working Capital / Total Assets
- X2 = Retained Earnings / Total Assets
- X3 = EBIT / Total Assets
- X4 = Market Cap / Total Liabilities
- X5 = Revenue / Total Assets

| Z-Score | Zone |
|---------|------|
| > 2.99 | 🟢 Safe |
| 1.81–2.99 | 🟡 Grey Zone |
| < 1.81 | 🔴 Distress |

All inputs come from **balance sheet + income statement** data — no new API calls needed.

#### EPS Surprise History
The delta between Wall St. analyst consensus EPS estimates and the actual reported EPS each quarter.

**Data source:** Finnhub's `/stock/earnings` endpoint (free tier, 4 quarters).
Returns: `date`, `actual`, `estimate`, `surprise`, `surprisePercent`.

### Implementation Plan

#### Backend — [MODIFY] [fundamental_service.py](file:///Users/anoop/Developer/Projects/TSRL/src/application/services/fundamental_service.py)
Add three new private methods called inside `analyze()`:

```python
def _compute_piotroski_score(self, report, raw) -> tuple[int, dict[str, int]]:
    """Returns (score 0-9, per-criterion breakdown)."""

def _compute_altman_z_score(self, report, raw) -> Optional[float]:
    """Returns Z-score float or None if data incomplete."""

def _fetch_eps_surprise(self, symbol) -> list[dict]:
    """Calls Finnhub /stock/earnings, returns last 4-8 quarters."""
```

#### [MODIFY] [fundamental.py](file:///Users/anoop/Developer/Projects/TSRL/src/domain/entities/fundamental.py)
Add fields:
```python
piotroski_score: Optional[int] = None
piotroski_breakdown: dict = field(default_factory=dict)
altman_z_score: Optional[float] = None
altman_z_zone: Optional[str] = None   # "safe" | "grey" | "distress"
eps_surprise_history: list[dict] = field(default_factory=list)
```

#### [MODIFY] [fundamental.schema.ts](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/lib/schemas/fundamental.schema.ts)
Add Zod fields for the above.

#### Frontend

##### [NEW] [QualityScores.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/fundamentals/QualityScores.tsx)
Side-by-side panel for the two quantitative scores:
- **Piotroski:** Score displayed as `7/9` with a checklist of all 9 criteria (✓/✗)
- **Altman Z:** Gauge needle chart (like a car speedometer) painted green/yellow/red by zone

##### [NEW] [EpsSurpriseChart.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/charts/EpsSurpriseChart.tsx)
Grouped bar chart (`BarChart`) per quarter:
- Light bar = analyst estimate
- Solid bar = actual EPS (green if beat, red if miss)
- Labels show `+X%` beat or `-X%` miss

##### [MODIFY] [FundamentalsPage.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/pages/FundamentalsPage.tsx)
- Inject `QualityScores` into the **Overview** tab (below the health gauge + key metrics)
- Inject `EpsSurpriseChart` into the **Financials** tab (below the revenue/margin charts)

---

## Item 6 — Frontend Enhancement

### Changes

#### A. Use existing `chart-tooltip` CSS classes
All custom Recharts `contentStyle` inline objects in `FinancialTrendsChart`, `RadarScoreChart`,
`EquityCurveChart` should be replaced with a shared `<CustomTooltip>` component that renders
using `.chart-tooltip`, `.chart-tooltip-header`, `.chart-tooltip-row`, `.chart-tooltip-label`,
`.chart-tooltip-value` CSS classes already defined in `theme.css`.

##### [NEW] [ChartTooltip.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/charts/ChartTooltip.tsx)
```tsx
interface TooltipRow { label: string; value: string; color?: string; }
interface Props { header: string; rows: TooltipRow[]; }
export function ChartTooltip({ header, rows }: Props) { ... }
```

#### B. Upgrade `FinancialTrendsChart`
- Switch from grouped `BarChart` to a `ComposedChart` with bars (Revenue) + line (Net Income) + area (FCF) on one chart — less chart clutter
- Add reference line at `y=0` styled with `var(--color-border-default)`
- Secondary Y-axis for margins (right side)

#### C. Upgrade `MetricCard` for Fundamentals
Current `MetricCard` doesn't show a trend arrow or sub-label. Add optional `trend` prop:
```tsx
interface MetricCardProps {
  label: string;
  value: string;
  subValue?: string;       // e.g. "vs industry avg: 12.3%"
  trend?: 'up' | 'down' | 'neutral';
  positive?: boolean;
  negative?: boolean;
  icon?: ReactNode;
}
```

#### D. `ComparisonTable` Component (for multi-ticker mode)
- Sticky ticker header row (symbol + company name + health grade badge)
- Rows = metric groups (Valuation, Profitability, Solvency, etc.)
- Best value in each row highlighted with `background: var(--color-positive)/10` and green text
- Worst value highlighted with red tint

#### E. Skeleton loading states
Add `SkeletonFundamentals` component used while `isLoading = true`, consistent with existing
`SkeletonMetricGrid` and `SkeletonChart` UI components.

---

## Item 7 — Provider Switcher (yfinance ↔ FMP)

### Problem
There is no UI control to switch the data provider. It's hardcoded in the backend.

### Solution

#### Backend — [MODIFY] [main.py](file:///Users/anoop/Developer/Projects/TSRL/src/main.py)
Add optional `source` query param to `GET /api/v1/fundamentals/{symbol}`:
```
GET /api/v1/fundamentals/AAPL?source=yfinance   # default
GET /api/v1/fundamentals/AAPL?source=fmp         # paid, production
```
`FundamentalService` already accepts `source` in its constructor — just wire it through the route.

#### Frontend — [MODIFY] [FundamentalsPage.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/pages/FundamentalsPage.tsx)
Add a small segmented control (reuse `.tab-nav` / `.tab-item` / `.tab-active` CSS) next to the
search bar:

```
[ yfinance (Free) ]  [ FMP (Paid) ]
```

- Default: `yfinance`
- Selecting `FMP` appends `?source=fmp` to the API call
- If `FMP_API_KEY` is empty on the server, the endpoint should return a clear `400` with
  message "FMP_API_KEY not configured" — the frontend shows a toast.
- Provider badge shown in the company header: e.g. `Data: Yahoo Finance`

#### [MODIFY] [apiHooks.ts](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/hooks/apiHooks.ts)
Update `useFundamentals` to accept optional `source` param:
```ts
export function useFundamentals(symbol: string, source: 'yfinance' | 'fmp' = 'yfinance', enabled = true)
```

---

## Item 8 — Enhanced Page Footer (Data Attribution)

### Problem
The `PageFooter` component (already exists as `.page-footer` CSS class) doesn't appear on
`FundamentalsPage`. The existing footer pattern in other pages is a single attribution line.
For fundamentals, users need to know what data source powers each section.

### Solution

#### [MODIFY] [FundamentalsPage.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/pages/FundamentalsPage.tsx)
Add a `FundamentalsFooter` section at the bottom using the existing `PageFooter` component,
conditionally shown after a report loads. Fields to show:

| Section | Data Source | Refresh Cadence |
|---------|-------------|-----------------|
| Price & Ratios | Yahoo Finance / FMP | ~15 min delay |
| Financial Statements | Yahoo Finance / FMP | Quarterly |
| News | Finnhub | Real-time |
| Sentiment | Alpha Vantage | Intraday |
| Insider Transactions | Finnhub / FMP | Within 2 business days of filing |
| EPS Surprise | Finnhub | Post-earnings |
| Health Score | Computed on server | Recalculated per request |

Also include:
- `fetch_timestamp` from the report (shown as "Last updated: X minutes ago")
- Disclaimer: "This data is for research purposes only and does not constitute financial advice."
- Cache notice: "Fundamental data is cached for 1 hour. Force-refresh available."

---

## Proposed Implementation Order

```
Step 1: Item 3 (env keys) + Item 7 (source switcher) — 30 mins (pure wiring, no new logic)
Step 2: Item 5 (Piotroski + Altman + EPS) — 2 hrs (backend math + 2 frontend components)
Step 3: Item 4 (Insider Tracker) — 2 hrs (new provider + InsiderTracker component)
Step 4: Item 6 (Frontend enhancement + ChartTooltip) — 1.5 hrs (polish)
Step 5: Item 2 (Multi-ticker search + ComparisonTable) — 1.5 hrs
Step 6: Item 1 (Nav grouping) — 30 mins (CSS only)
Step 7: Item 8 (Footer) — 30 mins
```

**Total estimated effort: ~8.5 hours**

---

## Open Questions

> [!IMPORTANT]
> **Insider Tracker API Key**: Finnhub's free tier limits insider data to 25 requests/day.
> Do you want to use Finnhub (free dev, already in use for news) or go straight to FMP for
> insiders (paid but higher limits)?

> [!NOTE]
> **EPS Surprise quarters**: Finnhub free tier gives the last 4 quarters. FMP gives up to 8.
> This is fine for the chart — confirming 4 is acceptable.

> [!NOTE]
> **Multi-ticker comparison limit**: Suggested cap of 5 tickers max per comparison call to keep
> `asyncio.gather` latency under ~3 seconds. Does that work for you?
