"""Domain entity for fundamental analysis reports."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FundamentalReport:
    """Complete fundamental analysis report for a single stock.

    Contains valuation, profitability, liquidity, solvency, cash flow metrics,
    historical trends, analyst data, news, and a composite health score.
    """

    # ── Company Identification ──────────────────────────────────────────
    symbol: str = ""
    company_name: str = ""
    sector: str = ""
    industry: str = ""
    description: str = ""
    market_cap: float = 0.0
    current_price: float = 0.0
    currency: str = "USD"
    employees: Optional[int] = None
    website: Optional[str] = None
    exchange: Optional[str] = None

    # ── Valuation Ratios ────────────────────────────────────────────────
    pe_ratio: Optional[float] = None           # Trailing P/E
    forward_pe: Optional[float] = None         # Forward P/E
    peg_ratio: Optional[float] = None          # P/E to EPS growth
    pb_ratio: Optional[float] = None           # Price to Book
    ps_ratio: Optional[float] = None           # Price to Sales (TTM)
    ev_ebitda: Optional[float] = None          # Enterprise Value / EBITDA
    ev_revenue: Optional[float] = None         # Enterprise Value / Revenue

    # ── Profitability ───────────────────────────────────────────────────
    gross_margin: Optional[float] = None       # Gross Profit / Revenue
    operating_margin: Optional[float] = None   # EBIT / Revenue
    net_margin: Optional[float] = None         # Net Income / Revenue
    ebitda_margin: Optional[float] = None      # EBITDA / Revenue
    roe: Optional[float] = None                # Return on Equity
    roa: Optional[float] = None                # Return on Assets
    eps_trailing: Optional[float] = None       # Trailing EPS
    eps_forward: Optional[float] = None        # Forward EPS (analyst est.)
    revenue_growth: Optional[float] = None     # YoY revenue growth
    earnings_growth: Optional[float] = None    # YoY earnings growth

    # ── Liquidity ───────────────────────────────────────────────────────
    current_ratio: Optional[float] = None      # Current Assets / Current Liabilities
    quick_ratio: Optional[float] = None        # (CA - Inventory) / CL

    # ── Solvency ────────────────────────────────────────────────────────
    debt_to_equity: Optional[float] = None     # Total Debt / Equity (yfinance: /100)
    interest_coverage: Optional[float] = None  # EBIT / Interest Expense
    long_term_debt_to_capital: Optional[float] = None

    # ── Cash Flow ───────────────────────────────────────────────────────
    free_cash_flow: Optional[float] = None      # Operating CF - CapEx
    fcf_margin: Optional[float] = None          # FCF / Revenue
    fcf_yield: Optional[float] = None           # FCF per share / Price
    operating_cash_flow: Optional[float] = None
    cash_conversion: Optional[float] = None     # Operating CF / Net Income

    # ── Growth (CAGR) ──────────────────────────────────────────────────
    revenue_cagr_3yr: Optional[float] = None
    revenue_cagr_5yr: Optional[float] = None
    earnings_cagr_3yr: Optional[float] = None
    fcf_cagr_3yr: Optional[float] = None

    # ── Historical Trends (for charts) ─────────────────────────────────
    annual_revenue: list = field(default_factory=list)         # [{year, value}] in billions
    annual_net_income: list = field(default_factory=list)
    annual_fcf: list = field(default_factory=list)
    annual_gross_margin: list = field(default_factory=list)    # [{year, value}] as %
    annual_operating_margin: list = field(default_factory=list)

    # ── Analyst & Market ───────────────────────────────────────────────
    analyst_rating: Optional[str] = None       # "strong_buy"/"buy"/"hold"/"sell"/"strong_sell"
    analyst_rating_score: Optional[float] = None  # 1.0 (strong buy) - 5.0 (strong sell)
    target_price: Optional[float] = None       # Mean analyst target
    target_high: Optional[float] = None
    target_low: Optional[float] = None
    analyst_count: Optional[int] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    beta: Optional[float] = None
    short_interest: Optional[float] = None     # Short % of float
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    # ── News & Sentiment ───────────────────────────────────────────────
    news: list = field(default_factory=list)    # [{headline, summary, url, datetime, source}]
    sentiment: dict = field(default_factory=dict)  # {avg_sentiment, label, article_count}

    # ── Health Score ───────────────────────────────────────────────────
    health_score: Optional[float] = None       # 0-100 composite score
    health_grade: Optional[str] = None         # A, B, C, D, F
    score_breakdown: dict = field(default_factory=dict)  # Per-pillar scores

    # ── Quantitative Quality Scores ─────────────────────────────────────
    # Piotroski F-Score (0-9): binary financial health checklist
    piotroski_score: Optional[int] = None
    piotroski_breakdown: dict = field(default_factory=dict)  # per-criterion {name: 0|1}

    # Altman Z-Score: bankruptcy predictor (>2.99 safe, 1.81-2.99 grey, <1.81 distress)
    altman_z_score: Optional[float] = None
    altman_z_zone: Optional[str] = None        # "safe" | "grey" | "distress"

    # EPS Surprise history (last 4-8 quarters)
    eps_surprise_history: list = field(default_factory=list)
    # [{quarter, actual, estimate, surprise, surprise_pct}]

    # ── Insider Trading ─────────────────────────────────────────────────
    insider_transactions: list = field(default_factory=list)
    # [{name, position, transaction_type, shares, price, value, date, is_10b5_plan}]
    insider_net_sentiment: Optional[float] = None  # +1.0=all buys, -1.0=all sells
    insider_net_buy_value: Optional[float] = None  # net $ bought - $ sold (6 months)

    # ── Data Provenance ────────────────────────────────────────────────
    data_source: str = "yfinance"              # "yfinance" or "fmp"
    fetch_timestamp: Optional[str] = None

