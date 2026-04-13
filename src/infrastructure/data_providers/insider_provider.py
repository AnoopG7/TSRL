"""Insider Trading data provider — SEC Form 4 via Finnhub, FMP, or direct SEC EDGAR."""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from xml.etree import ElementTree as ET

import requests

logger = logging.getLogger(__name__)

# SEC EDGAR tickers to CIK mapping (pre-loaded popular tickers)
_TICKER_TO_CIK = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "TSLA": "0001318605",
    "NVDA": "0001045810",
    "AMD": "0000002488",
    "NFLX": "0001065280",
    "DIS": "0001744489",
    "V": "0001403161",
    "MA": "0001141391",
    "PYPL": "0001623913",
    "INTC": "0000086473",
    "IBM": "0000051143",
    "CSCO": "0000858877",
    "ORCL": "0000732717",
    "CRM": "0001108523",
    "ADBE": "0000796343",
    "PEP": "0000077476",
    "KO": "0000021344",
    "MCD": "0000063908",
    "NKE": "0000320187",
    "SBUX": "0000829212",
    "WMT": "0000104169",
    "TGT": "0000027899",
    "COST": "0000908832",
    "HD": "0000354950",
    "LOW": "0000060635",
    "BA": "0000012927",
    "CAT": "0000018230",
    "GE": "0000040545",
    "Ford": "0000037769",
    "GM": "0001467858",
    "TM": "0001094517",
    "JPM": "0000019617",
    "BAC": "0000070858",
    "WFC": "0000729107",
    "GS": "0000886257",
    "MS": "0000895421",
    "C": "0000017208",
}


@dataclass
class InsiderTransaction:
    name: str
    position: str
    transaction_type: str  # "P" (Purchase) or "S" (Sale)
    shares: int
    price: float
    value: float
    date: str
    is_10b5_plan: bool = False  # True if pre-planned sale


class InsiderProvider:
    """Fetches Form 4 insider transaction data.

    Supports Finnhub (free tier, 25 requests/day limit) and FMP (paid).
    If Finnhub fails due to limit, returns empty list.
    """

    def __init__(self, source: str = "finnhub"):
        self.source = source
        self.finnhub_key = os.environ.get("FINNHUB_API_KEY")
        self.fmp_key = os.environ.get("FMP_API_KEY")
        self.alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

    def get_transactions(self, symbol: str, limit: int = 50) -> list[InsiderTransaction]:
        """Fetch recent insider transactions for a given stock."""
        # Prioritize FMP if requested and key available
        if self.source == "fmp" and self.fmp_key:
            return self._fetch_fmp(symbol, limit)

        # Fallback to Finnhub
        if self.finnhub_key:
            return self._fetch_finnhub(symbol, limit)

        # Free fallback: Alpha Vantage (uses the already-configured key)
        if self.alpha_key:
            return self._fetch_alpha_vantage(symbol.upper(), limit)

        # Free fallback: SEC EDGAR (no API key required)
        if symbol.upper() in _TICKER_TO_CIK:
            return self._fetch_edgar(symbol.upper(), limit)

        logger.warning(f"No API key configured for insider data (source={self.source})")
        return []

    def _fetch_finnhub(self, symbol: str, limit: int) -> list[InsiderTransaction]:
        """Fetch from Finnhub /stock/insider-transactions."""
        try:
            url = (
                f"https://finnhub.io/api/v1/stock/insider-transactions"
                f"?symbol={symbol.upper()}&token={self.finnhub_key}"
            )
            response = requests.get(url, timeout=15)

            if response.status_code == 429:
                logger.warning("Finnhub rate limit hit for insider data.")
                return []

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict) or "data" not in data:
                return []

            transactions = []
            for t in data.get("data", [])[:limit]:
                # Finnhub returns negative shares for sales sometimes.
                # We normalize it to positive and rely on 'transaction_type' or 'change' direction.
                change = float(t.get("change", 0))
                if change == 0:
                    continue

                t_type = "P" if change > 0 else "S"
                shares = abs(int(change))
                price = float(t.get("transactionPrice", 0))
                value = shares * price

                transactions.append(
                    InsiderTransaction(
                        name=t.get("name", "Unknown").title(),
                        position=self._normalize_position(t.get("name", "")),
                        transaction_type=t_type,
                        shares=shares,
                        price=round(price, 2),
                        value=round(value, 2),
                        date=t.get("transactionDate", ""),
                        is_10b5_plan=False,
                    )
                )

            return transactions

        except Exception as e:
            logger.warning(f"Finnhub insider fetch failed for {symbol}: {e}")
            return []

    def _fetch_fmp(self, symbol: str, limit: int) -> list[InsiderTransaction]:
        """Fetch from FMP /v4/insider-trading."""
        try:
            url = (
                f"https://financialmodelingprep.com/api/v4/insider-trading"
                f"?symbol={symbol.upper()}&limit={limit}&apikey={self.fmp_key}"
            )
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return []

            transactions = []
            for t in data:
                acq_disp = t.get("acqOrDisp")
                if not acq_disp:
                    continue

                t_type = "P" if acq_disp == "A" else "S"
                shares = int(t.get("securitiesTransacted", 0))
                price = float(t.get("price", 0))

                transactions.append(
                    InsiderTransaction(
                        name=t.get("reportingName", "Unknown").title(),
                        position=self._normalize_position(t.get("typeOfOwner", "Insider")),
                        transaction_type=t_type,
                        shares=shares,
                        price=round(price, 2),
                        value=round(shares * price, 2),
                        date=t.get("transactionDate", ""),
                        is_10b5_plan="10b5" in str(t.get("transactionType", "")).lower(),
                    )
                )

            return transactions

        except Exception as e:
            logger.warning(f"FMP insider fetch failed for {symbol}: {e}")
            return []

    def _fetch_alpha_vantage(self, symbol: str, limit: int) -> list[InsiderTransaction]:
        """Fetch from Alpha Vantage INSIDER_TRANSACTIONS endpoint."""
        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=INSIDER_TRANSACTIONS"
                f"&symbol={symbol.upper()}"
                f"&apikey={self.alpha_key}"
            )
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if "Note" in data or "Information" in data:
                logger.warning("Alpha Vantage rate limit or premium required.")
                return []

            transactions = []
            for t in data.get("data", [])[:limit]:
                acq_disp = t.get("acquisition_or_disposal", "")
                if not acq_disp:
                    continue

                # "A" = Acquisition (buy), "D" = Disposal (sell)
                t_type = "P" if acq_disp.upper() == "A" else "S"
                shares_str = t.get("shares", "0")
                shares = int(float(shares_str)) if shares_str else 0
                price_str = t.get("share_price", "0")
                price = float(price_str) if price_str else 0.0

                transactions.append(
                    InsiderTransaction(
                        name=t.get("executive", "Unknown").title(),
                        position=t.get("executive_title", "Insider"),
                        transaction_type=t_type,
                        shares=shares,
                        price=round(price, 2),
                        value=round(shares * price, 2),
                        date=t.get("transaction_date", ""),
                        is_10b5_plan=False,
                    )
                )

            return transactions

        except Exception as e:
            logger.warning(f"Alpha Vantage insider fetch failed for {symbol}: {e}")
            return []

    def compute_net_sentiment(self, transactions: list[InsiderTransaction]) -> Optional[float]:
        """Compute net sentiment score: (Buys - Sells) / Total
        Filters out 10b5-1 automated sales since they are less informative.
        Returns +1.0 (all buys) down to -1.0 (all sells).
        """
        if not transactions:
            return None

        valid = [t for t in transactions if not t.is_10b5_plan]
        if not valid:
            return 0.0

        buys = sum(1 for t in valid if t.transaction_type == "P")
        sells = sum(1 for t in valid if t.transaction_type == "S")
        return (buys - sells) / len(valid)

    def compute_net_buy_value(
        self, transactions: list[InsiderTransaction], months=6
    ) -> Optional[float]:
        """Compute net dollar value bought/sold over the trailing `months`."""
        if not transactions:
            return None

        cutoff = datetime.now() - timedelta(days=30 * months)
        net = 0.0

        for t in transactions:
            if t.is_10b5_plan:
                continue

            try:
                date = datetime.strptime(t.date, "%Y-%m-%d")
                if date >= cutoff:
                    if t.transaction_type == "P":
                        net += t.value
                    elif t.transaction_type == "S":
                        net -= t.value
            except ValueError:
                continue

        return round(net, 2)

    def _normalize_position(self, raw_role: str) -> str:
        """Attempt to extract standard titles from messy legal strings."""
        r = raw_role.lower()
        if "chief executive" in r or "ceo" in r:
            return "CEO"
        if "chief financial" in r or "cfo" in r:
            return "CFO"
        if "director" in r:
            return "Director"
        if "officer" in r:
            return "Officer"
        if "10%" in r or "ten percent" in r:
            return "10% Owner"
        return "Insider"

    def _fetch_edgar(self, symbol: str, limit: int) -> list[InsiderTransaction]:
        """Fetch Form 4 filings directly from SEC EDGAR (free, no API key).

        Uses SEC's company tickers endpoint to find CIK,
        then fetches Form 4 ownership filings.
        """
        cik = _TICKER_TO_CIK.get(symbol.upper())
        if not cik:
            return []

        # SEC requires a User-Agent per their Fair Access policy
        user_agent = os.environ.get("SEC_EDGAR_USER_AGENT", "TSRL python@example.com")
        headers = {"User-Agent": user_agent}

        try:
            # SEC EDGAR submissions API — correct endpoint with CIK
            url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"

            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            recent = data.get("filings", {}).get("recent", {})

            # recent is a dict of parallel arrays: form[], accessionNumber[], filingDate[], primaryDocument[]
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            filing_dates = recent.get("filingDate", [])
            primary_docs = recent.get("primaryDocument", [])

            # Find Form 4 indices
            form4_indices = [
                i for i, f in enumerate(forms)
                if f == "4" and i < len(accessions)
            ][:limit]

            if not form4_indices:
                return []

            # Step 2: Fetch details for each Form 4 (XML)
            transactions = []
            for idx in form4_indices:
                accession = accessions[idx]
                primary_doc = primary_docs[idx] if idx < len(primary_docs) else ""
                filing_date = filing_dates[idx] if idx < len(filing_dates) else ""

                if not accession or not primary_doc:
                    continue

                # Build XML URL
                # Format: https://www.sec.gov/Archives/edgar/data/cik/accession/primarydocument
                cik_padded = cik.zfill(10)
                xml_url = (
                    f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/"
                    f"{accession.replace('-', '')}/{primary_doc}"
                )

                try:
                    xml_resp = requests.get(xml_url, headers=headers, timeout=10)
                    if xml_resp.status_code != 200:
                        continue

                    # Parse XML
                    root = ET.fromstring(xml_resp.text)

                    # Navigate to ownership document
                    ns = {"ns": "http://www.sec.gov/ns/owner#"}
                    for owner in root.findall(".//ns:ownerStatement", ns) or root.findall(
                        ".//ownerStatement"
                    ):
                        # Get reporting person
                        reporting = owner.find(".//ns:reportingOwner", ns) or owner.find(
                            ".//reportingOwner"
                        )
                        if reporting is None:
                            continue

                        # Get name and title
                        name_elem = reporting.find(".//ns:ownerName", ns) or reporting.find(
                            ".//ownerName"
                        )
                        title_elem = reporting.find(".//ns:ownerTitle", ns) or reporting.find(
                            ".//ownerTitle"
                        )
                        name = (
                            name_elem.text
                            if name_elem is not None and name_elem.text
                            else "Unknown"
                        )
                        position = (
                            title_elem.text
                            if title_elem is not None and title_elem.text
                            else "Insider"
                        )

                        # Get transactions (non-derivative)
                        for txn in owner.findall(
                            ".//ns:nonDerivativeTransaction", ns
                        ) or owner.findall(".//nonDerivativeTransaction"):
                            try:
                                # Transaction code: "P" = Purchase, "S" = Sale
                                code_elem = txn.find(".//ns:transactionCode", ns) or txn.find(
                                    ".//transactionCode"
                                )
                                if code_elem is None or code_elem.text not in ("P", "S"):
                                    continue
                                t_type = code_elem.text  # "P" or "S" directly

                                # Shares transacted (NOT sharesOwnedFollowingTransaction)
                                shares_elem = txn.find(
                                    ".//ns:sharesTransacted", ns
                                ) or txn.find(".//sharesTransacted")
                                if shares_elem is None:
                                    # Fallback: try sharesAmount inside transactionAmounts
                                    shares_elem = txn.find(
                                        ".//ns:sharesAmount", ns
                                    ) or txn.find(".//sharesAmount")
                                if shares_elem is None or not shares_elem.text:
                                    continue
                                shares = int(float(shares_elem.text))

                                # Price (if available)
                                price = 0.0
                                price_elem = txn.find(
                                    ".//ns:transactionPricePerShare", ns
                                ) or txn.find(".//transactionPricePerShare")
                                if price_elem is not None and price_elem.text:
                                    price = float(price_elem.text)

                                # Value
                                value = shares * price if price > 0 else 0



                                transactions.append(
                                    InsiderTransaction(
                                        name=name.title(),
                                        position=self._normalize_position(position),
                                        transaction_type=t_type,
                                        shares=shares,
                                        price=round(price, 2),
                                        value=round(value, 2),
                                        date=filing_date,
                                        is_10b5_plan=False,
                                    )
                                )
                            except Exception:
                                continue

                    if len(transactions) >= limit:
                        break

                except Exception as e:
                    logger.debug(f"Failed to parse Form 4 XML for {symbol}: {e}")
                    continue

            return transactions[:limit]

        except Exception as e:
            logger.warning(f"SEC EDGAR fetch failed for {symbol}: {e}")
            return []
