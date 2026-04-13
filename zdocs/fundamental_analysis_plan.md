# Fundamental Analysis Feature — Complete Implementation Guide

> A full E2E knowledge base + engineering plan for integrating a Fundamental Analysis
> module into the TSRL (Trading Strategy Research Lab) project.

---

## Part 1: What is Fundamental Analysis and What Are We Measuring?

Fundamental analysis answers one core question: **Is this company's stock worth buying at this price?**

Rather than looking at charts and price patterns (technical analysis), fundamental analysis
looks INSIDE the company — its financials, its business model, its competitive position,
and the news surrounding it.

There are **5 financial pillars** + **1 qualitative pillar**:

---

## Part 2: Complete Data Dictionary — Every Metric, Where it Comes From

### 📌 PILLAR 1 — Valuation Ratios (Is the stock cheap or expensive?)

These tell you what the *market is willing to pay* relative to what the company actually *earns or owns*.

| Metric | Formula | Source Field | Interpretation |
|---|---|---|---|
| **Price/Earnings (P/E)** | Market Price / EPS | `ticker.info["trailingPE"]` or `["forwardPE"]` | < 15 = cheap, > 30 = expensive (context-dependent by sector) |
| **PEG Ratio** | P/E / EPS Growth Rate | `ticker.info["trailingPegRatio"]` | < 1 = undervalued relative to growth, > 2 = overpriced |
| **Price/Book (P/B)** | Market Price / Book Value Per Share | `ticker.info["priceToBook"]` | < 1 = trading below accounting value (potential bargain or distressed) |
| **Price/Sales (P/S)** | Market Cap / Annual Revenue | `ticker.info["priceToSalesTrailing12Months"]` | < 1 = very cheap, > 5 = richly valued |
| **EV/EBITDA** | Enterprise Value / EBITDA | `ticker.info["enterpriseToEbitda"]` | < 10 = undervalued, > 20 = expensive |
| **EV/Revenue** | Enterprise Value / Revenue | `ticker.info["enterpriseToRevenue"]` | Sector-dependent |
| **Forward P/E** | Price / Next Year Estimated EPS | `ticker.info["forwardPE"]` | Forward-looking growth expectation |

> **Where EPS comes from:** `ticker.financials.loc["Net Income"] / shares_outstanding`
> Trailing EPS = last 12 months, Forward EPS = analyst estimates

---

### 📌 PILLAR 2 — Profitability Ratios (Can it make money?)

These tell you *how efficiently* the company converts its activities into profit.

| Metric | Formula | Source Field | Interpretation |
|---|---|---|---|
| **Gross Margin** | (Revenue - COGS) / Revenue × 100 | `ticker.info["grossMargins"]` | > 40% = strong pricing power |
| **Operating Margin** | EBIT / Revenue × 100 | `ticker.info["operatingMargins"]` | > 15% = healthy |
| **Net Profit Margin** | Net Income / Revenue × 100 | `ticker.info["profitMargins"]` | > 10% = good |
| **EBITDA Margin** | EBITDA / Revenue × 100 | `ticker.info["ebitdaMargins"]` | Comparable across capital structures |
| **ROE (Return on Equity)** | Net Income / Shareholder Equity | `ticker.info["returnOnEquity"]` | > 15% = excellent, Buffett's rule: always look for this |
| **ROA (Return on Assets)** | Net Income / Total Assets | `ticker.info["returnOnAssets"]` | > 5% = good |
| **EPS (Earnings Per Share)** | Net Income / Shares Outstanding | `ticker.info["trailingEps"]`, `["forwardEps"]` | Growing EPS = good sign |
| **Revenue Growth YoY** | (Revenue_now - Revenue_prev) / Revenue_prev | Computed from `ticker.financials` | Consistent >10% growth is strong |
| **Earnings Growth YoY** | Same but for Net Income | `ticker.info["earningsGrowth"]` or computed | Validate vs. price |

> **Raw data source for historical profitability:**
> ```python
> t = yf.Ticker("AAPL")
> t.financials           # Annual Income Statement (Revenue, Gross Profit, EBIT, Net Income)
> t.quarterly_financials # Quarterly (TTM calculations)
> ```

---

### 📌 PILLAR 3 — Liquidity Ratios (Can it pay its bills tomorrow?)

These measure *short-term financial health* — can the company survive the next 12 months?

| Metric | Formula | Source Field | Interpretation |
|---|---|---|---|
| **Current Ratio** | Current Assets / Current Liabilities | `ticker.info["currentRatio"]` | 1.5–3 = healthy, < 1 = danger zone |
| **Quick Ratio** | (CA - Inventory) / CL | Computed from `ticker.balance_sheet` | More strict: excludes inventory (can't sell fast) |
| **Cash Ratio** | Cash / Current Liabilities | Computed from balance sheet | Most conservative liquidity gauge |

> **Raw data source:**
> ```python
> t.balance_sheet  # Rows: Total Current Assets, Total Current Liabilities, Cash, Inventory
> ```

---

### 📌 PILLAR 4 — Solvency Ratios (Can it survive long-term debt?)

These measure *long-term financial stability* — is the company overleveraged?

| Metric | Formula | Source Field | Interpretation |
|---|---|---|---|
| **Debt-to-Equity (D/E)** | Total Debt / Shareholders' Equity | `ticker.info["debtToEquity"]` | < 1 = low leverage (safe), > 2 = high risk |
| **Interest Coverage (ICR)** | EBIT / Interest Expense | Computed from `ticker.financials` | < 1.5 = danger, > 3 = safe |
| **Long-Term Debt/Capital** | LT Debt / (LT Debt + Equity) | Computed from `ticker.balance_sheet` | > 50% = risky |
| **Debt/EBITDA** | Total Debt / EBITDA | Computed from balance sheet + financials | < 3 = manageable |

> **Raw data source:**
> ```python
> t.balance_sheet   # Long Term Debt, Total Liabilities, Stockholders Equity
> t.financials      # EBIT row for interest coverage numerator
> ```

---

### 📌 PILLAR 5 — Cash Flow (Real money, not accounting tricks)

Net Income can be manipulated. Cash Flow cannot. This is often considered the *truest* measure of business health.

| Metric | Formula | Source Field | Interpretation |
|---|---|---|---|
| **Operating Cash Flow** | Cash from core business | `ticker.cashflow.loc["Total Cash From Operating Activities"]` | Should be positive and growing |
| **Free Cash Flow (FCF)** | Operating Cash Flow - CapEx | Computed from cashflow statement | The "owner's earnings" — key Buffett metric |
| **FCF Margin** | FCF / Revenue | Computed | > 10% = excellent |
| **FCF Yield** | FCF Per Share / Stock Price | Computed | High yield = potentially undervalued |
| **CapEx/Revenue** | Capital Expenditure / Revenue | Computed from cashflow | High capex = capital-intensive business |
| **Cash Conversion** | Operating CF / Net Income | Computed | > 1 = earnings backed by real cash |

> **Raw data source:**
> ```python
> t.cashflow            # Annual: Operating CF, CapEx (Capital Expenditures), Investing, Financing
> t.quarterly_cashflow  # Quarterly values
> ```

---

### 📌 PILLAR 6 — Growth Metrics (Is the business getting better?)

Compounded Annual Growth Rate (CAGR) measures consistent improvement over time.

| Metric | Computed | Interpretation |
|---|---|---|
| **Revenue CAGR (3yr/5yr)** | ((Rev_now/Rev_3yr_ago)^(1/3)) - 1 | > 10% = growth company |
| **EPS CAGR (3yr/5yr)** | Same formula for EPS | Consistent EPS growth = quality |
| **FCF CAGR** | Same for FCF | Signals improving capital efficiency |
| **Dividend Growth Rate** | Computed from `ticker.dividends` | For income investors |
| **Book Value CAGR** | From historical balance sheets | Intrinsic value growth over time |

---

### 📰 PILLAR 7 — Market News + Qualitative Data

This is where we go beyond just the numbers. **You cannot get qualitative data from financial statements alone.**

#### What "Qualitative" Means and Where to Get It

| Data Type | Free Source | What You Get |
|---|---|---|
| **Recent Company News** | **Finnhub API** (free tier: 60 calls/min) | Headlines, source, datetime, url |
| **Market Sentiment Score** | **Alpha Vantage Sentiment API** (free) | Bullish/bearish/neutral score + ticker relevance |
| **Analyst Recommendations** | `ticker.info["recommendationKey"]` | "strong_buy", "buy", "hold", "sell" |
| **Analyst Price Targets** | `ticker.info["targetMeanPrice"]` | Consensus target vs. current price |
| **Number of Analyst Opinions** | `ticker.info["numberOfAnalystOpinions"]` | How many analysts track this stock |
| **Insider Transactions** | `ticker.insider_transactions` | Buys/sells by executives (huge signal!) |
| **Institutional Ownership** | `ticker.institutional_holders` | % held by hedge funds, pension funds |
| **Short Interest** | `ticker.info["shortPercentOfFloat"]` | High short % = market expecting decline |
| **Company Description** | `ticker.info["longBusinessSummary"]` | What the company actually does |
| **Sector + Industry** | `ticker.info["sector"]`, `["industry"]` | For sector comparison |
| **Employee Count** | `ticker.info["fullTimeEmployees"]` | Company size |
| **Dividend Yield** | `ticker.info["dividendYield"]` | For income investors |
| **Beta** | `ticker.info["beta"]` | Volatility vs. market (> 1 = more volatile) |
| **52-Week Range** | `ticker.info["fiftyTwoWeekHigh/Low"]` | Price context |

#### How to Get News (Finnhub — Free, Best Option)

```python
import requests

# 1. Sign up at finnhub.io — get a free API key
FINNHUB_API_KEY = "your_key"

# 2. Get company news for last 7 days
url = f"https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2024-01-01&to=2024-01-07&token={FINNHUB_API_KEY}"
news = requests.get(url).json()
# Returns: [{headline, summary, url, datetime, source, category, sentiment}]

# 3. Get general market news
url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
```

#### How to Get Sentiment (Alpha Vantage — Free)

```python
# Alpha Vantage News Sentiment API  
url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=YOUR_KEY"
# Returns: sentiment_score, ticker_sentiment_label, relevance_score per article
```

---

## Part 3: Full System Architecture for TSRL

```
TSRL Fundamental Analysis Feature
├── Backend (Python/FastAPI)
│   ├── src/infrastructure/data_providers/
│   │   ├── fundamental_provider.py    ← Fetches raw data: yfinance + Finnhub
│   │   └── news_provider.py           ← Fetches news + sentiment
│   ├── src/application/services/
│   │   ├── fundamental_service.py     ← Computes all ratios, CAGR, health score
│   │   └── news_service.py            ← Aggregates + scores news
│   ├── src/domain/entities/
│   │   └── fundamental.py             ← Dataclass: FundamentalReport
│   └── src/main.py                    ← New API routes
│
└── Frontend (React/TypeScript)
    ├── src/pages/FundamentalsPage.tsx  ← Full dashboard page
    ├── src/components/charts/
    │   ├── FinancialTrendsChart.tsx    ← Bar chart: Revenue, Earnings, FCF over 5 years
    │   ├── RadarScoreChart.tsx         ← Spider chart: ratios vs sector average
    │   └── NewsCard.tsx                ← News feed with sentiment badges
    ├── src/hooks/apiHooks.ts           ← useFundamentals() hook
    └── src/lib/schemas/
        └── fundamental.schema.ts       ← Zod types
```

---

## Part 4: Step-by-Step Backend Implementation

### Step 1 — Install New Dependencies

```bash
pip install finnhub-python  # Finnhub SDK
# yfinance is already installed (v1.2.0)
```

Also update [pyproject.toml](file:///Users/anoop/Developer/Projects/TSRL/pyproject.toml) to add `finnhub-python>=2.4.19`.

---

### Step 2 — `fundamental_provider.py`

This is the **data fetching layer**. It talks to APIs and returns raw data. No business logic here.

```python
# src/infrastructure/data_providers/fundamental_provider.py

import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from typing import Optional

@dataclass
class RawFundamentals:
    info: dict                          # yfinance ticker.info
    income_stmt: pd.DataFrame           # Annual Income Statement
    balance_sheet: pd.DataFrame         # Annual Balance Sheet
    cash_flow: pd.DataFrame             # Annual Cash Flow
    quarterly_income: pd.DataFrame      # Last 4 quarters
    quarterly_balance: pd.DataFrame
    quarterly_cashflow: pd.DataFrame


class FundamentalProvider:
    def fetch(self, symbol: str) -> RawFundamentals:
        ticker = yf.Ticker(symbol)
        return RawFundamentals(
            info=ticker.info,
            income_stmt=ticker.financials,        # columns = last 4 annual periods
            balance_sheet=ticker.balance_sheet,
            cash_flow=ticker.cashflow,
            quarterly_income=ticker.quarterly_financials,
            quarterly_balance=ticker.quarterly_balance_sheet,
            quarterly_cashflow=ticker.quarterly_cashflow,
        )
```

> The `ticker.financials` DataFrame has **rows = line items** (Revenue, Gross Profit, Net Income...)
> and **columns = dates** (most recent first). Each column is one year.

---

### Step 3 — `news_provider.py`

```python
# src/infrastructure/data_providers/news_provider.py

import requests, os
from datetime import datetime, timedelta

class NewsProvider:
    FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY")

    def get_company_news(self, symbol: str, days: int = 7) -> list[dict]:
        """Fetch recent news articles for a stock from Finnhub."""
        end = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={symbol}&from={start}&to={end}&token={self.FINNHUB_KEY}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        articles = r.json()
        # Return top 10, sorted by datetime
        return sorted(articles, key=lambda x: x.get("datetime", 0), reverse=True)[:10]

    def get_sentiment(self, symbol: str) -> dict:
        """Get news sentiment from Alpha Vantage."""
        AV_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=NEWS_SENTIMENT&tickers={symbol}&apikey={AV_KEY}&limit=10"
        )
        r = requests.get(url, timeout=20)
        data = r.json()
        # avg the ticker_sentiment_score across articles
        scores = []
        for article in data.get("feed", []):
            for ts in article.get("ticker_sentiment", []):
                if ts.get("ticker") == symbol:
                    scores.append(float(ts.get("ticker_sentiment_score", 0)))
        return {
            "avg_sentiment": round(sum(scores) / len(scores), 3) if scores else 0,
            "article_count": len(scores),
            "label": "Bullish" if (sum(scores)/len(scores) > 0.15 if scores else False)
                     else "Bearish" if (sum(scores)/len(scores) < -0.15 if scores else False)
                     else "Neutral",
        }
```

---

### Step 4 — `fundamental_service.py` (The Brain — Ratio Engine)

This is the most important file. It takes the raw DataFrames and computes every ratio.

```python
# src/application/services/fundamental_service.py

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np

from src.infrastructure.data_providers.fundamental_provider import FundamentalProvider, RawFundamentals
from src.infrastructure.data_providers.news_provider import NewsProvider


@dataclass
class FundamentalReport:
    symbol: str
    company_name: str
    sector: str
    industry: str
    description: str
    market_cap: float
    current_price: float
    currency: str

    # Valuation
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None

    # Profitability
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    eps_trailing: Optional[float] = None
    eps_forward: Optional[float] = None

    # Liquidity
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None

    # Solvency
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Cash Flow
    free_cash_flow: Optional[float] = None
    fcf_margin: Optional[float] = None
    operating_cash_flow: Optional[float] = None

    # Growth (CAGR)
    revenue_cagr_3yr: Optional[float] = None
    earnings_cagr_3yr: Optional[float] = None
    fcf_cagr_3yr: Optional[float] = None

    # Historical trends (for charts)
    annual_revenue: list = field(default_factory=list)       # [{year, value}]
    annual_net_income: list = field(default_factory=list)
    annual_fcf: list = field(default_factory=list)
    annual_gross_margin: list = field(default_factory=list)

    # Analyst & Market
    analyst_rating: Optional[str] = None
    target_price: Optional[float] = None
    analyst_count: Optional[int] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    short_interest: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    # News
    news: list = field(default_factory=list)
    sentiment: dict = field(default_factory=dict)

    # Score
    health_score: Optional[float] = None
    health_grade: Optional[str] = None  # A, B, C, D, F


class FundamentalService:
    def __init__(self):
        self.provider = FundamentalProvider()
        self.news_provider = NewsProvider()

    def analyze(self, symbol: str, include_news: bool = True) -> FundamentalReport:
        raw = self.provider.fetch(symbol)
        info = raw.info

        # ── Core Company Info ──────────────────────────────────────────────
        report = FundamentalReport(
            symbol=symbol.upper(),
            company_name=info.get("shortName", symbol),
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            description=info.get("longBusinessSummary", ""),
            market_cap=info.get("marketCap", 0),
            current_price=info.get("currentPrice", 0),
            currency=info.get("currency", "USD"),
        )

        # ── Valuation ──────────────────────────────────────────────────────
        report.pe_ratio = info.get("trailingPE")
        report.forward_pe = info.get("forwardPE")
        report.peg_ratio = info.get("trailingPegRatio")
        report.pb_ratio = info.get("priceToBook")
        report.ps_ratio = info.get("priceToSalesTrailing12Months")
        report.ev_ebitda = info.get("enterpriseToEbitda")

        # ── Profitability ──────────────────────────────────────────────────
        report.gross_margin = info.get("grossMargins")
        report.operating_margin = info.get("operatingMargins")
        report.net_margin = info.get("profitMargins")
        report.roe = info.get("returnOnEquity")
        report.roa = info.get("returnOnAssets")
        report.eps_trailing = info.get("trailingEps")
        report.eps_forward = info.get("forwardEps")

        # ── Liquidity ──────────────────────────────────────────────────────
        report.current_ratio = info.get("currentRatio")
        report.quick_ratio = info.get("quickRatio")

        # ── Solvency ───────────────────────────────────────────────────────
        report.debt_to_equity = info.get("debtToEquity")
        # Interest Coverage = EBIT / Interest Expense (not in info, compute from financials)
        try:
            ebit = raw.income_stmt.loc["EBIT"].iloc[0]
            interest = raw.income_stmt.loc["Interest Expense"].iloc[0]
            if interest and interest != 0:
                report.interest_coverage = round(abs(ebit / interest), 2)
        except Exception:
            pass

        # ── Cash Flow ──────────────────────────────────────────────────────
        try:
            ocf = raw.cash_flow.loc["Operating Cash Flow"].iloc[0]
            capex = raw.cash_flow.loc["Capital Expenditure"].iloc[0]
            revenue = raw.income_stmt.loc["Total Revenue"].iloc[0]
            report.operating_cash_flow = float(ocf)
            report.free_cash_flow = float(ocf + capex)  # capex is negative in yfinance
            if revenue > 0:
                report.fcf_margin = round(report.free_cash_flow / revenue, 4)
        except Exception:
            pass

        # ── Historical Trends + CAGR ──────────────────────────────────────
        report.annual_revenue = self._extract_trend(raw.income_stmt, "Total Revenue")
        report.annual_net_income = self._extract_trend(raw.income_stmt, "Net Income")
        report.annual_fcf = self._compute_fcf_series(raw)
        report.annual_gross_margin = self._compute_margin_series(raw)

        if len(report.annual_revenue) >= 4:
            report.revenue_cagr_3yr = self._cagr(
                report.annual_revenue[-1]["value"], report.annual_revenue[0]["value"], 3
            )
        if len(report.annual_net_income) >= 4:
            report.earnings_cagr_3yr = self._cagr(
                report.annual_net_income[-1]["value"], report.annual_net_income[0]["value"], 3
            )

        # ── Analyst + Market ───────────────────────────────────────────────
        report.analyst_rating = info.get("recommendationKey")
        report.target_price = info.get("targetMeanPrice")
        report.analyst_count = info.get("numberOfAnalystOpinions")
        report.dividend_yield = info.get("dividendYield")
        report.beta = info.get("beta")
        report.short_interest = info.get("shortPercentOfFloat")
        report.week_52_high = info.get("fiftyTwoWeekHigh")
        report.week_52_low = info.get("fiftyTwoWeekLow")

        # ── News + Sentiment ──────────────────────────────────────────────
        if include_news:
            try:
                report.news = self.news_provider.get_company_news(symbol)
            except Exception:
                report.news = []
            try:
                report.sentiment = self.news_provider.get_sentiment(symbol)
            except Exception:
                report.sentiment = {}

        # ── Health Score ──────────────────────────────────────────────────
        report.health_score, report.health_grade = self._compute_health_score(report)

        return report

    def _extract_trend(self, df: pd.DataFrame, row: str) -> list[dict]:
        """Extract annual values for a given row from financial statements."""
        try:
            series = df.loc[row]
            return [
                {"year": col.year, "value": round(float(val) / 1e9, 2)}  # in billions
                for col, val in zip(series.index, series.values)
                if pd.notna(val)
            ][::-1]  # oldest first for charts
        except Exception:
            return []

    def _compute_fcf_series(self, raw: RawFundamentals) -> list[dict]:
        """Compute FCF = Operating CF - CapEx for each year."""
        try:
            ocf = raw.cash_flow.loc["Operating Cash Flow"]
            capex = raw.cash_flow.loc["Capital Expenditure"]
            return [
                {"year": col.year, "value": round((float(o) + float(c)) / 1e9, 2)}
                for col, o, c in zip(ocf.index, ocf.values, capex.values)
                if pd.notna(o) and pd.notna(c)
            ][::-1]
        except Exception:
            return []

    def _compute_margin_series(self, raw: RawFundamentals) -> list[dict]:
        """Compute gross margin % for each year."""
        try:
            rev = raw.income_stmt.loc["Total Revenue"]
            gp = raw.income_stmt.loc["Gross Profit"]
            return [
                {"year": col.year, "value": round(float(g) / float(r) * 100, 1)}
                for col, r, g in zip(rev.index, rev.values, gp.values)
                if pd.notna(r) and pd.notna(g) and float(r) > 0
            ][::-1]
        except Exception:
            return []

    def _cagr(self, end_val: float, start_val: float, years: int) -> Optional[float]:
        """Compute Compounded Annual Growth Rate."""
        try:
            if start_val <= 0 or end_val <= 0:
                return None
            return round((end_val / start_val) ** (1 / years) - 1, 4)
        except Exception:
            return None

    def _compute_health_score(self, r: FundamentalReport) -> tuple[float, str]:
        """
        Composite 0-100 health score weighted across 5 pillars.
        Each sub-metric is scored 0-10 then weighted.
        """
        score = 0.0
        max_score = 0.0

        def add(value, weight, low_good=False, thresholds=(0, 5, 10, 20)):
            """Score a metric. thresholds = (bad, ok, good, great)."""
            nonlocal score, max_score
            max_score += weight
            if value is None:
                return
            lo, ok, good, great = thresholds
            if low_good:  # Lower is better (D/E, P/E, short interest)
                pts = 10 if value <= lo else 7 if value <= ok else 4 if value <= good else 1
            else:
                pts = 10 if value >= great else 7 if value >= good else 4 if value >= ok else 1
            score += pts / 10 * weight

        # PROFITABILITY (30 pts)
        add(r.roe, 8, thresholds=(0.05, 0.1, 0.15, 0.25))
        add(r.net_margin, 7, thresholds=(0.02, 0.05, 0.1, 0.2))
        add(r.gross_margin, 7, thresholds=(0.2, 0.35, 0.5, 0.7))
        add(r.roa, 8, thresholds=(0.02, 0.05, 0.08, 0.15))

        # VALUATION (25 pts) — lower is better
        add(r.pe_ratio, 10, low_good=True, thresholds=(10, 15, 25, 40))
        add(r.peg_ratio, 8, low_good=True, thresholds=(0.5, 1.0, 1.5, 2.5))
        add(r.pb_ratio, 7, low_good=True, thresholds=(1, 2, 4, 8))

        # CASH FLOW (20 pts)
        add(r.fcf_margin, 10, thresholds=(0.02, 0.05, 0.1, 0.2))
        add(r.fcf_cagr_3yr, 10, thresholds=(0.0, 0.05, 0.1, 0.2))

        # SOLVENCY (15 pts)
        add(r.debt_to_equity, 8, low_good=True, thresholds=(0.3, 0.7, 1.5, 3.0))
        add(r.interest_coverage, 7, thresholds=(1, 2, 3, 5))

        # GROWTH (10 pts)
        add(r.revenue_cagr_3yr, 5, thresholds=(0.0, 0.05, 0.1, 0.2))
        add(r.earnings_cagr_3yr, 5, thresholds=(0.0, 0.05, 0.1, 0.2))

        final = round((score / max_score) * 100, 1) if max_score > 0 else 0
        grade = "A" if final >= 80 else "B" if final >= 65 else "C" if final >= 50 else "D" if final >= 35 else "F"
        return final, grade
```

---

### Step 5 — New FastAPI Routes in [main.py](file:///Users/anoop/Developer/Projects/TSRL/src/main.py)

```python
# Add to src/main.py

from src.application.services.fundamental_service import FundamentalService

fundamental_service = FundamentalService()

@app.get("/api/v1/fundamentals/{symbol}")
async def get_fundamentals(symbol: str, include_news: bool = True, background_tasks: BackgroundTasks = None):
    """Fetch complete fundamental analysis for a stock."""
    try:
        report = fundamental_service.analyze(symbol.upper(), include_news=include_news)
        return dataclasses.asdict(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fundamentals/{symbol}/compare")
async def compare_fundamentals(symbol: str, peers: str = Query(...)):
    """Compare fundamentals across multiple stocks."""
    symbols = [symbol.upper()] + [p.strip().upper() for p in peers.split(",")]
    reports = {}
    for s in symbols:
        try:
            r = fundamental_service.analyze(s, include_news=False)
            reports[s] = {
                "pe_ratio": r.pe_ratio, "roe": r.roe,
                "net_margin": r.net_margin, "debt_to_equity": r.debt_to_equity,
                "health_score": r.health_score, "health_grade": r.health_grade,
            }
        except Exception as e:
            reports[s] = {"error": str(e)}
    return {"symbols": symbols, "comparison": reports}
```

---

### Step 6 — Environment Variables

Add to [config/.env](file:///Users/anoop/Developer/Projects/TSRL/config/.env):
```env
FINNHUB_API_KEY=your_finnhub_key_here
# ALPHA_VANTAGE_API_KEY is already there (for news sentiment)
```

Get your **free** Finnhub key at: https://finnhub.io/register (free: 60 calls/min)

---

## Part 5: Frontend Implementation

### `FundamentalsPage.tsx` — 4-Tab Dashboard

```
Tab 1: Overview
  ├── Company Profile Card (name, sector, description, employee count)
  ├── MetricCard grid (8 key metrics: P/E, ROE, Margin, D/E, current ratio...)
  ├── Health Score Gauge (0-100, color-coded: green/yellow/red)
  └── Analyst consensus bar (Strong Buy → Strong Sell)

Tab 2: Financials
  ├── Multi-series Bar Chart: Revenue/Net Income/FCF over 5 years
  └── Gross Margin trend line chart

Tab 3: Ratios Deep-Dive
  ├── Radar/Spider chart comparing company against sector benchmarks
  └── Detailed ratio table with status indicators (✅ Good / ⚠️ Watch / ❌ Poor)

Tab 4: News & Sentiment
  ├── Sentiment score banner (Bullish/Neutral/Bearish with confidence)
  ├── News article feed (headline, source, time, link)
  └── Insider transactions table (executives buying/selling)
```

### `useFundamentals()` Hook

```typescript
// Add to src/hooks/apiHooks.ts

export function useFundamentals(symbol: string, enabled: boolean) {
  return useQuery({
    queryKey: ['fundamentals', symbol],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/fundamentals/${symbol}`);
      return data;
    },
    enabled: enabled && symbol.length > 0,
    staleTime: CACHE_TIMES.fundamentals,  // 1 hour cache — fundamentals don't change by the minute
  });
}

export function useCompareFundamentals() {
  return useMutation({
    mutationFn: async ({ symbol, peers }: { symbol: string; peers: string }) => {
      const { data } = await api.get(`/api/v1/fundamentals/${symbol}/compare?peers=${peers}`);
      return data;
    },
  });
}
```

---

## Part 6: Caching Strategy

Fundamental data is **slow to fetch** (3-5 API calls per stock). We implement a two-level caching strategy.

### Environment-Aware Caching

| Environment | Backend Cache | Frontend Cache | Refresh Button |
|------------|--------------|----------------|----------------|
| **Development** | Enabled (1 hour TTL) | React Query (5 min) | Clears current stock cache |
| **Production** | Disabled (bypassed) | Disabled | Fetches fresh every time |

### Configuration

```bash
# config/.env
ENVIRONMENT=development  # or "production"
```

### Backend Cache Behavior

| Scenario | Dev Environment | Production |
|----------|---------------|------------|
| Initial request | Check cache → use if fresh, else fetch | Always fetch fresh |
| Click Refresh | Clear current stock cache → fetch fresh | Fetch fresh |
| Cache expires | Returns stale for 1hr | N/A (not used) |

### API Changes

| Parameter | Type | Description |
|-----------|------|-------------|
| `use_cache` | bool | Bypass cache (default: true, ignored in production) |
| `from_cache` | bool | Indicates if response was from cache |

### Cache Invalidation

- **Scope**: Individual stock (not all stocks)
- **Method**: `queryClient.invalidateQueries()` for current symbol only
- **Backend**: `cache.invalidate(symbol, "full_report", source)`

### Rate Limit Handling

When APIs are rate-limited:
1. Backend returns cached data (if available)
2. Frontend shows yellow warning banner: "⚠️ API rate limit reached. Showing cached data from [timestamp]"
3. User can wait or refresh later

---

## Part 7: Complete Data Source Map

### "Where does each metric come from?" — Final Answer

| Metric | Raw Source | Python Code |
|---|---|---|
| P/E, P/B, P/S, Forward P/E | Yahoo Finance | `ticker.info["trailingPE"]` |
| Margins (gross/op/net) | Yahoo Finance | `ticker.info["grossMargins"]` |
| ROE, ROA | Yahoo Finance | `ticker.info["returnOnEquity"]` |
| Current Ratio, Quick Ratio | Yahoo Finance | `ticker.info["currentRatio"]` |
| Debt-to-Equity | Yahoo Finance | `ticker.info["debtToEquity"]` |
| Revenue, Net Income, EBIT | Yahoo Finance | `ticker.financials` DataFrame |
| Balance Sheet items | Yahoo Finance | `ticker.balance_sheet` DataFrame |
| Operating/Free Cash Flow | Yahoo Finance | `ticker.cashflow` DataFrame |
| CAGR (Revenue/Earnings/FCF) | Computed | Derived from 3-5 year financials |
| Interest Coverage | Computed | EBIT / Interest Expense |
| Free Cash Flow | Computed | Operating CF - CapEx |
| Analyst rating + price target | Yahoo Finance | `ticker.info["recommendationKey"]` |
| Beta, Dividend Yield, 52-week | Yahoo Finance | `ticker.info["beta"]` etc. |
| Company description + sector | Yahoo Finance | `ticker.info["longBusinessSummary"]` |
| Insider Transactions | Yahoo Finance | `ticker.insider_transactions` |

---

## Part 7b: Insider Trading Data Sources

Insider transactions are fetched from multiple providers with fallback logic:

| Provider | Priority | API | Rate Limit | Key Required |
|---------|----------|-----|------------|--------------|
| **Finnhub** | 1st | `/stock/insider-transactions` | 25 req/day (free) | `FINNHUB_API_KEY` |
| **Alpha Vantage** | 2nd | `INSIDER_TRANSACTIONS` | 25 req/day (free) | `ALPHA_VANTAGE_API_KEY` |
| **SEC EDGAR** | 3rd | Direct API | Strict rate limit | `SEC_EDGAR_USER_AGENT` |

### Current Configuration

```env
# config/.env
FINNHUB_API_KEY=d7esht1r01qi33g7gefgd  # Active
ALPHA_VANTAGE_API_KEY=H204V3BOKZ575M7X   # Active
SEC_EDGAR_USER_AGENT=TSRL anoop@example.com  # Fallback
```

### Files Involved

- `src/infrastructure/data_providers/insider_provider.py` - Provider with fallback logic
- `src/application/services/fundamental_service.py` - Calls InsiderProvider for `_populate_news()`
- `src/main.py` - `/fundamentals/{symbol}/insiders` endpoint

---

## Part 8: Implementation Checklist

### Backend ✅ COMPLETED
- [x] Create `src/infrastructure/data_providers/fundamental_provider.py`
- [x] Create `src/infrastructure/data_providers/news_provider.py`
- [x] Create `src/infrastructure/data_providers/insider_provider.py` (with Finnhub/AlphaVantage/SEC EDGAR fallback)
- [x] Add `FINNHUB_API_KEY` and `ALPHA_VANTAGE_API_KEY` to [config/.env](file:///Users/anoop/Developer/Projects/TSRL/config/.env)
- [x] Add `ENVIRONMENT` config for dev/prod caching
- [x] Create `src/domain/entities/fundamental.py` (dataclass `FundamentalReport`)
- [x] Create `src/application/services/fundamental_service.py`
- [x] Add routes to [src/main.py](file:///Users/anoop/Developer/Projects/TSRL/src/main.py):
  - `GET /api/v1/fundamentals/{symbol}` ✅
  - `GET /api/v1/fundamentals/{symbol}/news` ✅
  - `GET /api/v1/fundamentals/{symbol}/insiders` ✅
  - `GET /api/v1/fundamentals/compare` ✅
- [x] Implement caching with `src/infrastructure/data_providers/fundamental_cache.py`

### Frontend ✅ COMPLETED
- [x] Add `useFundamentals()` and `useCompareFundamentals()` to [apiHooks.ts](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/hooks/apiHooks.ts)
- [x] Add `FUNDAMENTALS` to `QUERY_KEYS` in `constants.ts`
- [x] Add `CACHE_TIMES.fundamentals = 60 * 60 * 1000` (1hr in ms)
- [x] Create `FundamentalsPage.tsx` (5-tab layout)
- [x] Create `FinancialTrendsChart.tsx` (grouped bar chart)
- [x] Create `RadarScoreChart.tsx` (spider chart for ratio comparison)
- [x] Create `NewsCard.tsx` (article feed with sentiment badge)
- [x] Create `InsiderTracker.tsx` (insider transactions table + chart)
- [x] Create `EpsSurpriseChart.tsx` (EPS surprise history)
- [x] Create `HealthScoreGauge.tsx` (0-100 health score)
- [x] Register `/fundamentals` route in [App.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/App.tsx)
- [x] Add "Fundamentals" nav item to [AppLayout.tsx](file:///Users/anoop/Developer/Projects/TSRL/frontend/src/components/layout/AppLayout.tsx)
- [x] Add Refresh button with loading state
- [x] Add Cache banner (shows when data is from cache)
- [x] Add `from_cache` to schema
