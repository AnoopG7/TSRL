"""Fundamental analysis service — computes all ratios, CAGR, and health score.

This is the orchestrator that:
1. Fetches raw data from FundamentalProvider (yfinance or FMP)
2. Fetches news from NewsProvider (Finnhub + Alpha Vantage)
3. Computes derived ratios not available in raw data
4. Calculates multi-year CAGR for growth trends
5. Generates a composite health score (0-100)
6. Returns a complete FundamentalReport
"""

import dataclasses
import logging
import os
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.domain.entities.fundamental import FundamentalReport
from src.infrastructure.data_providers.fundamental_provider import (
    FundamentalProvider,
    RawFundamentals,
)
from src.infrastructure.data_providers.news_provider import NewsProvider
from src.infrastructure.data_providers.fundamental_cache import get_fundamental_cache

logger = logging.getLogger(__name__)


class FundamentalService:
    """Orchestrates fundamental analysis for a given stock symbol.

    Supports two modes via `source` parameter:
    - "yfinance" (default): Free, good for development and personal use
    - "fmp": Paid (Financial Modeling Prep), better for production
    """

    def __init__(self, source: str = "yfinance"):
        self.provider = FundamentalProvider(source=source)
        self.news_provider = NewsProvider()
        self.cache = get_fundamental_cache()
        self.source = source

    def analyze(
        self,
        symbol: str,
        include_news: bool = True,
        use_cache: bool = True,
    ) -> dict:
        """Run complete fundamental analysis for a stock.

        Args:
            symbol: Stock ticker (e.g. "AAPL", "MSFT")
            include_news: Whether to fetch news + sentiment (adds latency)
            use_cache: Whether to check/update cache (bypassed in production)

        Returns:
            dict with 'report' (FundamentalReport) and 'from_cache' (bool)
        """
        symbol = symbol.upper()
        is_production = os.environ.get("ENVIRONMENT") == "production"

        # Bypass cache in production
        if is_production:
            use_cache = False

        # Check cache
        cached_data = None
        if use_cache:
            cached_data = self.cache.get(symbol, "full_report", self.source)
            if cached_data:
                logger.info(f"Returning cached report for {symbol}")
                report = FundamentalReport(**cached_data)
                return {"report": report, "from_cache": True}

        # Fetch raw data
        raw = self.provider.fetch(symbol)
        info = raw.info

        # Build report
        report = FundamentalReport(
            symbol=symbol,
            company_name=info.get("shortName", symbol),
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            description=info.get("longBusinessSummary", ""),
            market_cap=info.get("marketCap", 0) or 0,
            current_price=info.get("currentPrice", 0) or 0,
            currency=info.get("currency", "USD"),
            employees=info.get("fullTimeEmployees"),
            website=info.get("website"),
            exchange=info.get("exchange", ""),
            data_source=self.source,
            fetch_timestamp=datetime.now().isoformat(),
        )

        # Populate all pillars
        self._populate_valuation(report, info)
        self._populate_profitability(report, info)
        self._populate_liquidity(report, info)
        self._populate_solvency(report, info, raw)
        self._populate_cashflow(report, info, raw)
        self._populate_growth(report, info, raw)
        self._populate_trends(report, raw)
        self._populate_market_analyst(report, info)

        # News & sentiment (optional)
        if include_news:
            self._populate_news(report, symbol)

        # Quantitative quality scores
        self._compute_piotroski(report, raw)
        self._compute_altman_z(report, raw)
        self._fetch_eps_surprise(report, symbol)

        # Health score
        score, grade, breakdown = self._compute_health_score(report)
        report.health_score = score
        report.health_grade = grade
        report.score_breakdown = breakdown

        # Cache result
        if use_cache:
            try:
                report_dict = dataclasses.asdict(report)
                self.cache.set(symbol, report_dict, "full_report", self.source)
            except Exception as e:
                logger.warning(f"Failed to cache report for {symbol}: {e}")

        return {"report": report, "from_cache": False}

    # ════════════════════════════════════════════════════════════════════
    # Pillar population methods
    # ════════════════════════════════════════════════════════════════════

    def _populate_valuation(self, report: FundamentalReport, info: dict) -> None:
        """PILLAR 1: Valuation ratios from ticker.info."""
        report.pe_ratio = self._safe_float(info.get("trailingPE"))
        report.forward_pe = self._safe_float(info.get("forwardPE"))
        report.peg_ratio = self._safe_float(info.get("trailingPegRatio"))
        report.pb_ratio = self._safe_float(info.get("priceToBook"))
        report.ps_ratio = self._safe_float(info.get("priceToSalesTrailing12Months"))
        report.ev_ebitda = self._safe_float(info.get("enterpriseToEbitda"))
        report.ev_revenue = self._safe_float(info.get("enterpriseToRevenue"))

    def _populate_profitability(self, report: FundamentalReport, info: dict) -> None:
        """PILLAR 2: Profitability ratios from ticker.info."""
        report.gross_margin = self._safe_float(info.get("grossMargins"))
        report.operating_margin = self._safe_float(info.get("operatingMargins"))
        report.net_margin = self._safe_float(info.get("profitMargins"))
        report.ebitda_margin = self._safe_float(info.get("ebitdaMargins"))
        report.roe = self._safe_float(info.get("returnOnEquity"))
        report.roa = self._safe_float(info.get("returnOnAssets"))
        report.eps_trailing = self._safe_float(info.get("trailingEps"))
        report.eps_forward = self._safe_float(info.get("forwardEps"))
        report.revenue_growth = self._safe_float(info.get("revenueGrowth"))
        report.earnings_growth = self._safe_float(info.get("earningsGrowth"))

    def _populate_liquidity(self, report: FundamentalReport, info: dict) -> None:
        """PILLAR 3: Liquidity ratios from ticker.info."""
        report.current_ratio = self._safe_float(info.get("currentRatio"))
        report.quick_ratio = self._safe_float(info.get("quickRatio"))

    def _populate_solvency(
        self, report: FundamentalReport, info: dict, raw: RawFundamentals
    ) -> None:
        """PILLAR 4: Solvency ratios — some from info, some computed from statements."""
        # D/E from info (yfinance stores as percentage, e.g. 176.0 means 1.76)
        de = self._safe_float(info.get("debtToEquity"))
        if de is not None and raw.source == "yfinance" and de > 10:
            de = de / 100.0  # Normalize to ratio
        report.debt_to_equity = de

        # Interest Coverage = EBIT / Interest Expense (from income statement)
        if raw.income_stmt is not None:
            try:
                ebit = self._get_row_value(raw.income_stmt, ["EBIT", "Operating Income"])
                interest = self._get_row_value(
                    raw.income_stmt,
                    ["Interest Expense", "Interest Expense Non Operating"],
                )
                if ebit is not None and interest is not None and interest != 0:
                    report.interest_coverage = round(abs(ebit / interest), 2)
            except Exception:
                pass

        # Long-term Debt / Capital
        if raw.balance_sheet is not None:
            try:
                lt_debt = self._get_row_value(
                    raw.balance_sheet,
                    ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"],
                )
                equity = self._get_row_value(
                    raw.balance_sheet, ["Stockholders Equity", "Total Stockholder Equity"]
                )
                if lt_debt is not None and equity is not None and (lt_debt + equity) > 0:
                    report.long_term_debt_to_capital = round(lt_debt / (lt_debt + equity), 4)
            except Exception:
                pass

    def _populate_cashflow(
        self, report: FundamentalReport, info: dict, raw: RawFundamentals
    ) -> None:
        """PILLAR 5: Cash flow metrics — computed from cash flow statement."""
        if raw.cash_flow is None:
            return

        try:
            ocf = self._get_row_value(
                raw.cash_flow, ["Operating Cash Flow", "Total Cash From Operating Activities"]
            )
            capex = self._get_row_value(
                raw.cash_flow, ["Capital Expenditure", "Capital Expenditures"]
            )
            revenue = None
            if raw.income_stmt is not None:
                revenue = self._get_row_value(raw.income_stmt, ["Total Revenue"])
            net_income = None
            if raw.income_stmt is not None:
                net_income = self._get_row_value(raw.income_stmt, ["Net Income"])

            if ocf is not None:
                report.operating_cash_flow = float(ocf)

                if capex is not None:
                    fcf = ocf + capex  # capex is typically negative in yfinance
                    if raw.source == "fmp" and capex > 0:
                        fcf = ocf - capex  # FMP reports capex as positive
                    report.free_cash_flow = float(fcf)

                    if revenue and revenue > 0:
                        report.fcf_margin = round(fcf / revenue, 4)

                    # FCF yield = FCF per share / price
                    price = report.current_price
                    mcap = report.market_cap
                    if price and price > 0 and mcap and mcap > 0:
                        shares = mcap / price
                        fcf_per_share = fcf / shares if shares > 0 else 0
                        report.fcf_yield = round(fcf_per_share / price, 4)

                # Cash conversion = Operating CF / Net Income
                if net_income and net_income != 0:
                    report.cash_conversion = round(ocf / net_income, 2)

        except Exception as e:
            logger.warning(f"Error computing cash flow metrics: {e}")

    def _populate_growth(self, report: FundamentalReport, info: dict, raw: RawFundamentals) -> None:
        """PILLAR 6: Growth trends — compute CAGR from historical statements."""
        if raw.income_stmt is not None:
            rev_series = self._get_row_series(raw.income_stmt, ["Total Revenue"])
            if len(rev_series) >= 4:
                report.revenue_cagr_3yr = self._cagr(rev_series[-1], rev_series[0], 3)
            if len(rev_series) >= 6:
                report.revenue_cagr_5yr = self._cagr(rev_series[-1], rev_series[0], 5)

            ni_series = self._get_row_series(raw.income_stmt, ["Net Income"])
            if len(ni_series) >= 4:
                report.earnings_cagr_3yr = self._cagr(ni_series[-1], ni_series[0], 3)

        if raw.cash_flow is not None:
            ocf_series = self._get_row_series(
                raw.cash_flow, ["Operating Cash Flow", "Total Cash From Operating Activities"]
            )
            capex_series = self._get_row_series(
                raw.cash_flow, ["Capital Expenditure", "Capital Expenditures"]
            )
            if len(ocf_series) >= 4 and len(capex_series) >= 4:
                fcf_series = [o + c for o, c in zip(ocf_series, capex_series)]
                report.fcf_cagr_3yr = self._cagr(fcf_series[-1], fcf_series[0], 3)

    def _populate_trends(self, report: FundamentalReport, raw: RawFundamentals) -> None:
        """Extract annual time series for charting."""
        if raw.income_stmt is not None:
            report.annual_revenue = self._extract_trend(raw.income_stmt, ["Total Revenue"])
            report.annual_net_income = self._extract_trend(raw.income_stmt, ["Net Income"])
            report.annual_gross_margin = self._compute_margin_trend(
                raw.income_stmt, ["Gross Profit"], ["Total Revenue"]
            )
            report.annual_operating_margin = self._compute_margin_trend(
                raw.income_stmt, ["EBIT", "Operating Income"], ["Total Revenue"]
            )

        if raw.cash_flow is not None and raw.income_stmt is not None:
            report.annual_fcf = self._compute_fcf_trend(raw)

    def _populate_market_analyst(self, report: FundamentalReport, info: dict) -> None:
        """Market data and analyst opinions from ticker.info."""
        report.analyst_rating = info.get("recommendationKey")
        report.analyst_rating_score = self._safe_float(info.get("recommendationMean"))
        report.target_price = self._safe_float(info.get("targetMeanPrice"))
        report.target_high = self._safe_float(info.get("targetHighPrice"))
        report.target_low = self._safe_float(info.get("targetLowPrice"))
        report.analyst_count = info.get("numberOfAnalystOpinions")
        report.dividend_yield = self._safe_float(info.get("dividendYield"))
        report.payout_ratio = self._safe_float(info.get("payoutRatio"))
        report.beta = self._safe_float(info.get("beta"))
        report.short_interest = self._safe_float(info.get("shortPercentOfFloat"))

        high_str = info.get("fiftyTwoWeekHigh")
        low_str = info.get("fiftyTwoWeekLow")
        report.week_52_high = self._safe_float(high_str)
        report.week_52_low = self._safe_float(low_str)

    def _populate_news(self, report: FundamentalReport, symbol: str) -> None:
        """Fetch news and sentiment (PILLAR 7)."""
        try:
            report.news = self.news_provider.get_company_news(symbol)
        except Exception as e:
            logger.warning(f"News fetch failed for {symbol}: {e}")
            report.news = []

        try:
            report.sentiment = self.news_provider.get_sentiment(symbol)
        except Exception as e:
            logger.warning(f"Sentiment fetch failed for {symbol}: {e}")
            report.sentiment = {}

        # ── Insider Trading ─────────────────────────────────────────────────
        try:
            from src.infrastructure.data_providers.insider_provider import InsiderProvider

            insider_provider = InsiderProvider()
            txs = insider_provider.get_transactions(symbol)
            report.insider_transactions = txs
            report.insider_net_sentiment = insider_provider.compute_net_sentiment(txs)
            report.insider_net_buy_value = insider_provider.compute_net_buy_value(txs)
        except Exception as e:
            logger.warning(f"Insider fetch failed for {symbol}: {e}")
            report.insider_transactions = []
            report.insider_net_sentiment = None
            report.insider_net_buy_value = None

    # ════════════════════════════════════════════════════════════════
    # Piotroski F-Score
    # ════════════════════════════════════════════════════════════════════

    def _compute_piotroski(self, report: FundamentalReport, raw: "RawFundamentals") -> None:
        """Compute Piotroski F-Score (0-9) from financial statements.

        9 binary criteria — each scores 1 if met, 0 if not:
        Profitability (4): ROA>0, OCF>0, ROA_delta>0, Accruals<0
        Leverage/Liquidity (3): LT_Debt_delta<0, Current_Ratio_delta>0, No_Dilution
        Operating Efficiency (2): Gross_Margin_delta>0, Asset_Turnover_delta>0
        """
        if raw.income_stmt is None or raw.balance_sheet is None or raw.cash_flow is None:
            return

        breakdown: dict[str, int] = {}
        score = 0

        try:
            # Get current and prior year values
            def col(df, rows, idx=0):
                return self._get_row_value(df, rows, col_idx=idx)

            total_assets_0 = col(raw.balance_sheet, ["Total Assets"])
            total_assets_1 = col(raw.balance_sheet, ["Total Assets"], idx=1)
            net_income_0 = col(raw.income_stmt, ["Net Income"])
            ocf_0 = col(
                raw.cash_flow, ["Operating Cash Flow", "Total Cash From Operating Activities"]
            )
            revenue_0 = col(raw.income_stmt, ["Total Revenue"])
            revenue_1 = col(raw.income_stmt, ["Total Revenue"], idx=1)
            gross_profit_0 = col(raw.income_stmt, ["Gross Profit"])
            gross_profit_1 = col(raw.income_stmt, ["Gross Profit"], idx=1)
            lt_debt_0 = col(
                raw.balance_sheet, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"]
            )
            lt_debt_1 = col(
                raw.balance_sheet,
                ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"],
                idx=1,
            )
            current_assets_0 = col(raw.balance_sheet, ["Current Assets"])
            current_assets_1 = col(raw.balance_sheet, ["Current Assets"], idx=1)
            current_liab_0 = col(raw.balance_sheet, ["Current Liabilities"])
            current_liab_1 = col(raw.balance_sheet, ["Current Liabilities"], idx=1)
            shares_0 = col(raw.balance_sheet, ["Ordinary Shares Number", "Common Stock"])
            shares_1 = col(raw.balance_sheet, ["Ordinary Shares Number", "Common Stock"], idx=1)

            avg_assets = (
                (total_assets_0 + (total_assets_1 or total_assets_0)) / 2
                if total_assets_0
                else None
            )

            # ── F1: ROA > 0 ──
            roa_0 = net_income_0 / avg_assets if net_income_0 is not None and avg_assets else None
            f1 = 1 if (roa_0 is not None and roa_0 > 0) else 0
            breakdown["F1_roa_positive"] = f1
            score += f1

            # ── F2: Operating Cash Flow > 0 ──
            f2 = 1 if (ocf_0 is not None and ocf_0 > 0) else 0
            breakdown["F2_ocf_positive"] = f2
            score += f2

            # ── F3: ROA increased vs prior year ──
            roa_1 = None
            if net_income_0 is not None and total_assets_1 and total_assets_0:
                avg_assets_1 = (total_assets_1 + total_assets_0) / 2
                prior_ni = col(raw.income_stmt, ["Net Income"], idx=1)
                roa_1 = (
                    prior_ni / avg_assets_1 if prior_ni is not None and avg_assets_1 > 0 else None
                )
            f3 = 1 if (roa_0 is not None and roa_1 is not None and roa_0 > roa_1) else 0
            breakdown["F3_roa_improving"] = f3
            score += f3

            # ── F4: Accruals < 0 (OCF/assets > ROA = high earnings quality) ──
            f4 = (
                1
                if (
                    ocf_0 is not None
                    and avg_assets
                    and roa_0 is not None
                    and (ocf_0 / avg_assets) > roa_0
                )
                else 0
            )
            breakdown["F4_accruals_low"] = f4
            score += f4

            # ── F5: Long-term debt decreased ──
            f5 = 0
            if (
                lt_debt_0 is not None
                and lt_debt_1 is not None
                and total_assets_0
                and total_assets_1
            ):
                lev_0 = lt_debt_0 / total_assets_0
                lev_1 = lt_debt_1 / total_assets_1
                f5 = 1 if lev_0 < lev_1 else 0
            breakdown["F5_leverage_decreased"] = f5
            score += f5

            # ── F6: Current ratio improved ──
            f6 = 0
            if (
                current_assets_0
                and current_liab_0
                and current_assets_1
                and current_liab_1
                and current_liab_0 > 0
                and current_liab_1 > 0
            ):
                cr_0 = current_assets_0 / current_liab_0
                cr_1 = current_assets_1 / current_liab_1
                f6 = 1 if cr_0 > cr_1 else 0
            breakdown["F6_current_ratio_up"] = f6
            score += f6

            # ── F7: No share dilution ──
            f7 = (
                1 if (shares_0 is not None and shares_1 is not None and shares_0 <= shares_1) else 0
            )
            breakdown["F7_no_dilution"] = f7
            score += f7

            # ── F8: Gross margin improved ──
            f8 = 0
            if (
                gross_profit_0
                and revenue_0
                and gross_profit_1
                and revenue_1
                and revenue_0 > 0
                and revenue_1 > 0
            ):
                gm_0 = gross_profit_0 / revenue_0
                gm_1 = gross_profit_1 / revenue_1
                f8 = 1 if gm_0 > gm_1 else 0
            breakdown["F8_gross_margin_up"] = f8
            score += f8

            # ── F9: Asset turnover improved ──
            f9 = 0
            if revenue_0 and revenue_1 and total_assets_0 and total_assets_1:
                at_0 = revenue_0 / total_assets_0
                at_1 = revenue_1 / total_assets_1
                f9 = 1 if at_0 > at_1 else 0
            breakdown["F9_asset_turnover_up"] = f9
            score += f9

            report.piotroski_score = score
            report.piotroski_breakdown = breakdown

        except Exception as e:
            logger.warning(f"Piotroski computation failed: {e}")

    # ════════════════════════════════════════════════════════════════════
    # Altman Z-Score
    # ════════════════════════════════════════════════════════════════════

    def _compute_altman_z(self, report: FundamentalReport, raw: "RawFundamentals") -> None:
        """Compute Altman Z-Score for bankruptcy prediction.

        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        X1 = Working Capital / Total Assets
        X2 = Retained Earnings / Total Assets
        X3 = EBIT / Total Assets
        X4 = Market Cap / Total Liabilities
        X5 = Revenue / Total Assets

        Safe: Z > 2.99 | Grey: 1.81-2.99 | Distress: < 1.81
        """
        if raw.income_stmt is None or raw.balance_sheet is None:
            return

        try:

            def col(df, rows):
                return self._get_row_value(df, rows)

            total_assets = col(raw.balance_sheet, ["Total Assets"])
            current_assets = col(raw.balance_sheet, ["Current Assets"])
            current_liab = col(raw.balance_sheet, ["Current Liabilities"])
            retained_earnings = col(raw.balance_sheet, ["Retained Earnings"])
            total_liab = col(
                raw.balance_sheet, ["Total Liabilities Net Minority Interest", "Total Liabilities"]
            )
            ebit = col(raw.income_stmt, ["EBIT", "Operating Income"])
            revenue = col(raw.income_stmt, ["Total Revenue"])
            market_cap = report.market_cap

            if not total_assets or total_assets == 0:
                return

            x1 = ((current_assets or 0) - (current_liab or 0)) / total_assets
            x2 = (retained_earnings or 0) / total_assets
            x3 = (ebit or 0) / total_assets
            x4 = (market_cap or 0) / (total_liab or 1)  # avoid div by zero
            x5 = (revenue or 0) / total_assets

            z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
            report.altman_z_score = round(z, 3)

            if z > 2.99:
                report.altman_z_zone = "safe"
            elif z >= 1.81:
                report.altman_z_zone = "grey"
            else:
                report.altman_z_zone = "distress"

        except Exception as e:
            logger.warning(f"Altman Z-Score computation failed: {e}")

    # ════════════════════════════════════════════════════════════════════
    # EPS Surprise History
    # ════════════════════════════════════════════════════════════════════

    def _fetch_eps_surprise(self, report: FundamentalReport, symbol: str) -> None:
        """Fetch EPS surprise history from Finnhub (last 4 quarters).

        Finnhub endpoint: GET /stock/earnings?symbol={symbol}
        Returns: [{actual, estimate, surprise, surprisepct, period}]
        """
        import requests
        import os

        finnhub_key = os.environ.get("FINNHUB_API_KEY")
        if not finnhub_key:
            logger.debug("FINNHUB_API_KEY not set — skipping EPS surprise fetch")
            return

        try:
            url = (
                f"https://finnhub.io/api/v1/stock/earnings"
                f"?symbol={symbol.upper()}&token={finnhub_key}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return

            history = []
            for q in data[:8]:  # Last 8 quarters max
                actual = q.get("actual")
                estimate = q.get("estimate")
                if actual is None or estimate is None:
                    continue
                surprise = actual - estimate
                surprise_pct = (surprise / abs(estimate) * 100) if estimate != 0 else 0.0
                history.append(
                    {
                        "quarter": q.get("period", ""),
                        "actual": round(float(actual), 3),
                        "estimate": round(float(estimate), 3),
                        "surprise": round(float(surprise), 3),
                        "surprise_pct": round(float(surprise_pct), 2),
                    }
                )

            report.eps_surprise_history = history

        except Exception as e:
            logger.warning(f"EPS surprise fetch failed for {symbol}: {e}")

    # ════════════════════════════════════════════════════════════════════
    # Health Score Algorithm
    # ════════════════════════════════════════════════════════════════════

    def _compute_health_score(self, r: FundamentalReport) -> tuple[float, str, dict]:
        """Compute a composite 0-100 health score weighted across 5 pillars.

        Weight distribution:
        - Profitability: 30% (the most important — is it making money?)
        - Valuation:     25% (is the price reasonable?)
        - Cash Flow:     20% (does earnings = real cash?)
        - Solvency:      15% (can it survive long-term debt?)
        - Growth:        10% (is it improving?)

        Each sub-metric is scored 0-10, then weighted and normalized.
        """
        breakdown = {}
        pillar_scores = {}

        # ── PROFITABILITY (30 pts max) ──
        prof_score = 0.0
        prof_max = 0.0
        prof_metrics = {}

        def score_metric(
            value: Optional[float],
            weight: float,
            thresholds: tuple,
            lower_is_better: bool = False,
            name: str = "",
        ) -> tuple[float, float]:
            """Score a single metric. Returns (weighted_score, max_possible)."""
            if value is None:
                return 0.0, weight

            lo, ok, good, great = thresholds
            if lower_is_better:
                if value <= lo:
                    pts = 10
                elif value <= ok:
                    pts = 7
                elif value <= good:
                    pts = 4
                else:
                    pts = 1
            else:
                if value >= great:
                    pts = 10
                elif value >= good:
                    pts = 7
                elif value >= ok:
                    pts = 4
                else:
                    pts = 1

            return (pts / 10) * weight, weight

        # Profitability sub-metrics
        s, m = score_metric(r.roe, 8, (0.05, 0.1, 0.15, 0.25), name="ROE")
        prof_score += s
        prof_max += m
        prof_metrics["roe"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.net_margin, 7, (0.02, 0.05, 0.1, 0.2), name="Net Margin")
        prof_score += s
        prof_max += m
        prof_metrics["net_margin"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.gross_margin, 7, (0.2, 0.35, 0.5, 0.7), name="Gross Margin")
        prof_score += s
        prof_max += m
        prof_metrics["gross_margin"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.roa, 8, (0.02, 0.05, 0.08, 0.15), name="ROA")
        prof_score += s
        prof_max += m
        prof_metrics["roa"] = round(s / m * 100, 1) if m > 0 else 0

        pillar_scores["profitability"] = (
            round(prof_score / prof_max * 100, 1) if prof_max > 0 else 0
        )
        breakdown["profitability"] = {
            "score": pillar_scores["profitability"],
            "weight": 30,
            "metrics": prof_metrics,
        }

        # ── VALUATION (25 pts max) — lower is better ──
        val_score = 0.0
        val_max = 0.0
        val_metrics = {}

        s, m = score_metric(r.pe_ratio, 10, (10, 15, 25, 40), lower_is_better=True, name="P/E")
        val_score += s
        val_max += m
        val_metrics["pe_ratio"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.peg_ratio, 8, (0.5, 1.0, 1.5, 2.5), lower_is_better=True, name="PEG")
        val_score += s
        val_max += m
        val_metrics["peg_ratio"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.pb_ratio, 7, (1, 2, 4, 8), lower_is_better=True, name="P/B")
        val_score += s
        val_max += m
        val_metrics["pb_ratio"] = round(s / m * 100, 1) if m > 0 else 0

        pillar_scores["valuation"] = round(val_score / val_max * 100, 1) if val_max > 0 else 0
        breakdown["valuation"] = {
            "score": pillar_scores["valuation"],
            "weight": 25,
            "metrics": val_metrics,
        }

        # ── CASH FLOW (20 pts max) ──
        cf_score = 0.0
        cf_max = 0.0
        cf_metrics = {}

        s, m = score_metric(r.fcf_margin, 10, (0.02, 0.05, 0.1, 0.2), name="FCF Margin")
        cf_score += s
        cf_max += m
        cf_metrics["fcf_margin"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.fcf_cagr_3yr, 10, (0.0, 0.05, 0.1, 0.2), name="FCF Growth")
        cf_score += s
        cf_max += m
        cf_metrics["fcf_cagr_3yr"] = round(s / m * 100, 1) if m > 0 else 0

        pillar_scores["cash_flow"] = round(cf_score / cf_max * 100, 1) if cf_max > 0 else 0
        breakdown["cash_flow"] = {
            "score": pillar_scores["cash_flow"],
            "weight": 20,
            "metrics": cf_metrics,
        }

        # ── SOLVENCY (15 pts max) — lower D/E is better ──
        solv_score = 0.0
        solv_max = 0.0
        solv_metrics = {}

        s, m = score_metric(
            r.debt_to_equity, 8, (0.3, 0.7, 1.5, 3.0), lower_is_better=True, name="D/E"
        )
        solv_score += s
        solv_max += m
        solv_metrics["debt_to_equity"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.interest_coverage, 7, (1, 2, 3, 5), name="Interest Coverage")
        solv_score += s
        solv_max += m
        solv_metrics["interest_coverage"] = round(s / m * 100, 1) if m > 0 else 0

        pillar_scores["solvency"] = round(solv_score / solv_max * 100, 1) if solv_max > 0 else 0
        breakdown["solvency"] = {
            "score": pillar_scores["solvency"],
            "weight": 15,
            "metrics": solv_metrics,
        }

        # ── GROWTH (10 pts max) ──
        growth_score = 0.0
        growth_max = 0.0
        growth_metrics = {}

        s, m = score_metric(r.revenue_cagr_3yr, 5, (0.0, 0.05, 0.1, 0.2), name="Rev CAGR 3yr")
        growth_score += s
        growth_max += m
        growth_metrics["revenue_cagr_3yr"] = round(s / m * 100, 1) if m > 0 else 0

        s, m = score_metric(r.earnings_cagr_3yr, 5, (0.0, 0.05, 0.1, 0.2), name="Earnings CAGR 3yr")
        growth_score += s
        growth_max += m
        growth_metrics["earnings_cagr_3yr"] = round(s / m * 100, 1) if m > 0 else 0

        pillar_scores["growth"] = round(growth_score / growth_max * 100, 1) if growth_max > 0 else 0
        breakdown["growth"] = {
            "score": pillar_scores["growth"],
            "weight": 10,
            "metrics": growth_metrics,
        }

        # ── WEIGHTED FINAL SCORE ──
        total = 0.0
        total += pillar_scores["profitability"] * 0.30
        total += pillar_scores["valuation"] * 0.25
        total += pillar_scores["cash_flow"] * 0.20
        total += pillar_scores["solvency"] * 0.15
        total += pillar_scores["growth"] * 0.10

        final = round(total, 1)
        if final >= 80:
            grade = "A"
        elif final >= 65:
            grade = "B"
        elif final >= 50:
            grade = "C"
        elif final >= 35:
            grade = "D"
        else:
            grade = "F"

        return final, grade, breakdown

    # ════════════════════════════════════════════════════════════════════
    # Helper methods
    # ════════════════════════════════════════════════════════════════════

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert to float, returning None for invalid values."""
        if value is None:
            return None
        try:
            f = float(value)
            if np.isnan(f) or np.isinf(f):
                return None
            return round(f, 6)
        except (ValueError, TypeError):
            return None

    def _get_row_value(
        self, df: pd.DataFrame, row_names: list[str], col_idx: int = 0
    ) -> Optional[float]:
        """Get the most recent value for a row, trying multiple possible names.

        yfinance and FMP name rows differently. This handles both.
        """
        for name in row_names:
            if name in df.index:
                try:
                    val = float(df.loc[name].iloc[col_idx])
                    if not np.isnan(val):
                        return val
                except (IndexError, ValueError, TypeError):
                    continue
        return None

    def _get_row_series(self, df: pd.DataFrame, row_names: list[str]) -> list[float]:
        """Get the full time series for a row (most recent first → oldest first)."""
        for name in row_names:
            if name in df.index:
                try:
                    vals = df.loc[name].dropna().tolist()
                    return [float(v) for v in vals]
                except Exception:
                    continue
        return []

    def _cagr(self, end_val: float, start_val: float, years: int) -> Optional[float]:
        """Compute Compounded Annual Growth Rate."""
        try:
            if start_val <= 0 or end_val <= 0 or years <= 0:
                return None
            return round((end_val / start_val) ** (1 / years) - 1, 4)
        except Exception:
            return None

    def _extract_trend(self, df: pd.DataFrame, row_names: list[str]) -> list[dict]:
        """Extract annual values for charting: [{year, value (in billions)}]."""
        for name in row_names:
            if name in df.index:
                try:
                    series = df.loc[name]
                    points = []
                    for col, val in zip(series.index, series.values):
                        if pd.notna(val):
                            year = col.year if hasattr(col, "year") else str(col)
                            points.append(
                                {
                                    "year": year,
                                    "value": round(float(val) / 1e9, 2),  # Convert to billions
                                }
                            )
                    return points[::-1]  # Oldest first for charts
                except Exception:
                    continue
        return []

    def _compute_margin_trend(
        self,
        df: pd.DataFrame,
        numerator_names: list[str],
        denominator_names: list[str],
    ) -> list[dict]:
        """Compute a margin ratio trend: [{year, value (%)}]."""
        num_series = None
        den_series = None

        for name in numerator_names:
            if name in df.index:
                num_series = df.loc[name]
                break
        for name in denominator_names:
            if name in df.index:
                den_series = df.loc[name]
                break

        if num_series is None or den_series is None:
            return []

        points = []
        for col, n, d in zip(num_series.index, num_series.values, den_series.values):
            if pd.notna(n) and pd.notna(d) and float(d) > 0:
                year = col.year if hasattr(col, "year") else str(col)
                points.append(
                    {
                        "year": year,
                        "value": round(float(n) / float(d) * 100, 1),
                    }
                )
        return points[::-1]

    def _compute_fcf_trend(self, raw: RawFundamentals) -> list[dict]:
        """Compute annual FCF = Operating CF + CapEx trend."""
        ocf_names = ["Operating Cash Flow", "Total Cash From Operating Activities"]
        capex_names = ["Capital Expenditure", "Capital Expenditures"]

        ocf_series = None
        capex_series = None

        for name in ocf_names:
            if name in raw.cash_flow.index:
                ocf_series = raw.cash_flow.loc[name]
                break
        for name in capex_names:
            if name in raw.cash_flow.index:
                capex_series = raw.cash_flow.loc[name]
                break

        if ocf_series is None or capex_series is None:
            return []

        points = []
        for col, o, c in zip(ocf_series.index, ocf_series.values, capex_series.values):
            if pd.notna(o) and pd.notna(c):
                year = col.year if hasattr(col, "year") else str(col)
                fcf = float(o) + float(c)  # capex is negative in yfinance
                points.append(
                    {
                        "year": year,
                        "value": round(fcf / 1e9, 2),  # In billions
                    }
                )
        return points[::-1]
