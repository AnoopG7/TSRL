"""Fundamental data provider — dual source: yfinance (free) + FMP (paid).

Usage:
    provider = FundamentalProvider(source="yfinance")  # free / dev
    provider = FundamentalProvider(source="fmp")        # paid / production
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class RawFundamentals:
    """Raw financial data collected from a provider."""

    info: dict = field(default_factory=dict)
    income_stmt: Optional[pd.DataFrame] = None       # Annual
    balance_sheet: Optional[pd.DataFrame] = None      # Annual
    cash_flow: Optional[pd.DataFrame] = None          # Annual
    quarterly_income: Optional[pd.DataFrame] = None
    quarterly_balance: Optional[pd.DataFrame] = None
    quarterly_cashflow: Optional[pd.DataFrame] = None
    source: str = "yfinance"


class FundamentalProviderError(Exception):
    """Raised when fundamental data fetch fails."""
    pass


class YFinanceFundamentalProvider:
    """Free data source — fetches fundamentals from Yahoo Finance via yfinance."""

    def fetch(self, symbol: str) -> RawFundamentals:
        """Fetch all fundamental data for a symbol from Yahoo Finance.

        Returns a RawFundamentals object with:
        - info: dict with 100+ fields (P/E, margins, ROE, market cap, etc.)
        - income_stmt: Annual income statement (rows = line items, cols = dates)
        - balance_sheet: Annual balance sheet
        - cash_flow: Annual cash flow statement
        - quarterly_*: Same for quarterly periods
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            if not info.get("shortName"):
                raise FundamentalProviderError(
                    f"No data found for symbol '{symbol}'. "
                    "It may be invalid, delisted, or Yahoo Finance is unavailable."
                )

            return RawFundamentals(
                info=info,
                income_stmt=self._safe_df(ticker.financials),
                balance_sheet=self._safe_df(ticker.balance_sheet),
                cash_flow=self._safe_df(ticker.cashflow),
                quarterly_income=self._safe_df(ticker.quarterly_financials),
                quarterly_balance=self._safe_df(ticker.quarterly_balance_sheet),
                quarterly_cashflow=self._safe_df(ticker.quarterly_cashflow),
                source="yfinance",
            )
        except FundamentalProviderError:
            raise
        except Exception as e:
            raise FundamentalProviderError(
                f"Failed to fetch fundamentals for {symbol} from yfinance: {e}"
            ) from e

    def _safe_df(self, df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Return the DataFrame if it has data, else None."""
        if df is None or df.empty:
            return None
        return df


class FMPFundamentalProvider:
    """Paid data source — fetches fundamentals from Financial Modeling Prep API.

    Sign up at financialmodelingprep.com/developer/docs
    Free tier: 250 calls/day, 5yr history
    Starter ($19/mo): 300 calls/min, 5yr history, full ratios
    Premium ($49/mo): 30yr history, global coverage
    """

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FMP_API_KEY")
        if not self.api_key:
            raise FundamentalProviderError(
                "FMP API key is required. Set FMP_API_KEY in config/.env "
                "or pass api_key to FMPFundamentalProvider(). "
                "Get one at: https://financialmodelingprep.com/developer/docs"
            )

    def fetch(self, symbol: str) -> RawFundamentals:
        """Fetch all fundamental data from FMP.

        FMP returns pre-computed ratios, structured financial statements,
        and company profile data in clean JSON format.
        """
        try:
            profile = self._get(f"/profile/{symbol}")
            income = self._get(f"/income-statement/{symbol}?limit=5")
            balance = self._get(f"/balance-sheet-statement/{symbol}?limit=5")
            cashflow = self._get(f"/cash-flow-statement/{symbol}?limit=5")
            ratios = self._get(f"/ratios/{symbol}?limit=5")
            key_metrics = self._get(f"/key-metrics/{symbol}?limit=5")

            # Build unified info dict from FMP's profile + ratios
            info = self._build_info(profile, ratios, key_metrics)

            # Convert FMP statement lists to DataFrames matching yfinance shape
            income_df = self._statements_to_df(income) if income else None
            balance_df = self._statements_to_df(balance) if balance else None
            cashflow_df = self._statements_to_df(cashflow) if cashflow else None

            return RawFundamentals(
                info=info,
                income_stmt=income_df,
                balance_sheet=balance_df,
                cash_flow=cashflow_df,
                quarterly_income=None,
                quarterly_balance=None,
                quarterly_cashflow=None,
                source="fmp",
            )
        except FundamentalProviderError:
            raise
        except Exception as e:
            raise FundamentalProviderError(
                f"Failed to fetch fundamentals for {symbol} from FMP: {e}"
            ) from e

    def _get(self, endpoint: str) -> list | dict:
        """Make an authenticated GET request to FMP API."""
        separator = "&" if "?" in endpoint else "?"
        url = f"{self.BASE_URL}{endpoint}{separator}apikey={self.api_key}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "Error Message" in data:
            raise FundamentalProviderError(f"FMP API error: {data['Error Message']}")

        return data

    def _build_info(
        self,
        profile: list | dict,
        ratios: list | dict,
        key_metrics: list | dict,
    ) -> dict:
        """Build a unified info dict from FMP endpoints, mapped to yfinance-compatible keys.

        This ensures that FundamentalService can use the same field names
        regardless of whether yfinance or FMP is the data source.
        """
        p = profile[0] if isinstance(profile, list) and profile else (profile or {})
        r = ratios[0] if isinstance(ratios, list) and ratios else {}
        km = key_metrics[0] if isinstance(key_metrics, list) and key_metrics else {}

        return {
            # Company
            "shortName": p.get("companyName", ""),
            "longBusinessSummary": p.get("description", ""),
            "sector": p.get("sector", ""),
            "industry": p.get("industry", ""),
            "website": p.get("website", ""),
            "fullTimeEmployees": p.get("fullTimeEmployees"),
            "exchange": p.get("exchangeShortName", ""),
            "currency": p.get("currency", "USD"),
            # Market
            "marketCap": p.get("mktCap", 0),
            "currentPrice": p.get("price", 0),
            "beta": p.get("beta"),
            "fiftyTwoWeekHigh": p.get("range", "0-0").split("-")[-1] if p.get("range") else None,
            "fiftyTwoWeekLow": p.get("range", "0-0").split("-")[0] if p.get("range") else None,
            "volume": p.get("volAvg"),
            # Valuation (from ratios endpoint)
            "trailingPE": r.get("priceEarningsRatio"),
            "forwardPE": r.get("priceEarningsToGrowthRatio"),  # PEG stored here
            "trailingPegRatio": r.get("priceEarningsToGrowthRatio"),
            "priceToBook": r.get("priceToBookRatio"),
            "priceToSalesTrailing12Months": r.get("priceToSalesRatio"),
            "enterpriseToEbitda": km.get("enterpriseValueOverEBITDA"),
            "enterpriseToRevenue": km.get("evToSales"),
            # Profitability
            "grossMargins": r.get("grossProfitMargin"),
            "operatingMargins": r.get("operatingProfitMargin"),
            "profitMargins": r.get("netProfitMargin"),
            "ebitdaMargins": km.get("ebitdaPerShare"),  # approx
            "returnOnEquity": r.get("returnOnEquity"),
            "returnOnAssets": r.get("returnOnAssets"),
            "trailingEps": p.get("eps") if "eps" in p else km.get("netIncomePerShare"),
            # Liquidity
            "currentRatio": r.get("currentRatio"),
            "quickRatio": r.get("quickRatio"),
            # Solvency
            "debtToEquity": r.get("debtEquityRatio"),
            # Dividends
            "dividendYield": r.get("dividendYield"),
            "payoutRatio": r.get("payoutRatio"),
            # Analyst
            "recommendationKey": None,  # FMP doesn't provide this in free tier
            "targetMeanPrice": p.get("dcf"),  # DCF value as proxy
            "numberOfAnalystOpinions": None,
            # Short
            "shortPercentOfFloat": None,
        }

    def _statements_to_df(self, statements: list[dict]) -> Optional[pd.DataFrame]:
        """Convert FMP's list of statement dicts into a pandas DataFrame.

        FMP returns: [{date, revenue, costOfRevenue, ...}, ...]
        We pivot so rows = line items, columns = dates (matching yfinance format).
        """
        if not statements:
            return None

        try:
            df = pd.DataFrame(statements)
            if "date" not in df.columns:
                return None

            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").T

            # Remove non-numeric metadata rows
            drop_rows = [
                "date", "symbol", "reportedCurrency", "cik", "fillingDate",
                "acceptedDate", "calendarYear", "period", "link", "finalLink",
            ]
            df = df.drop(index=[r for r in drop_rows if r in df.index], errors="ignore")

            # Convert to numeric
            df = df.apply(pd.to_numeric, errors="coerce")

            # Map FMP column names to yfinance-compatible row names
            fmp_to_yf = {
                "revenue": "Total Revenue",
                "grossProfit": "Gross Profit",
                "operatingIncome": "EBIT",
                "netIncome": "Net Income",
                "ebitda": "EBITDA",
                "interestExpense": "Interest Expense",
                "totalCurrentAssets": "Total Current Assets",
                "totalCurrentLiabilities": "Total Current Liabilities",
                "inventory": "Inventory",
                "cashAndCashEquivalents": "Cash And Cash Equivalents",
                "totalStockholdersEquity": "Stockholders Equity",
                "longTermDebt": "Long Term Debt",
                "totalDebt": "Total Debt",
                "totalAssets": "Total Assets",
                "operatingCashFlow": "Operating Cash Flow",
                "capitalExpenditure": "Capital Expenditure",
                "freeCashFlow": "Free Cash Flow",
            }
            df = df.rename(index=fmp_to_yf)

            return df

        except Exception as e:
            logger.warning(f"Failed to convert FMP statements to DataFrame: {e}")
            return None


class FundamentalProvider:
    """Unified provider that delegates to yfinance (free) or FMP (paid).

    Usage:
        # Development (free)
        provider = FundamentalProvider(source="yfinance")
        raw = provider.fetch("AAPL")

        # Production (paid, better reliability)
        provider = FundamentalProvider(source="fmp")
        raw = provider.fetch("AAPL")
    """

    def __init__(self, source: str = "yfinance"):
        self.source = source
        if source == "fmp":
            self._provider = FMPFundamentalProvider()
        else:
            self._provider = YFinanceFundamentalProvider()

    def fetch(self, symbol: str) -> RawFundamentals:
        """Fetch fundamental data from the configured source."""
        return self._provider.fetch(symbol.upper())
