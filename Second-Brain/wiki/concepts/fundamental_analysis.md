# Fundamental Analysis

## Definition
Evaluation of a company's intrinsic value using financial statements, business metrics, and economic factors. Unlike technical analysis (price/volume), fundamental analysis asks: "What is this business worth?"

## Why It Matters
- **Long-term edge:** Fundamentals drive long-term returns
- **Risk assessment:** Avoid value traps and bankruptcies
- **Conviction sizing:** Larger positions in high-conviction names
- **Hybrid strategies:** Combine fundamentals with technical timing

## In My System

**Location:** 
- `src/application/services/fundamental_service.py` — Orchestration
- `src/domain/entities/fundamental.py` — FundamentalReport entity
- `src/infrastructure/data_providers/fundamental_provider.py` — Data fetching

**Data sources:**
- FMP (Financial Modeling Prep) — Primary
- yfinance — Fallback for missing data

---

## Health Score Framework

### Composite Score (0-100)
```python
@dataclass
class HealthScore:
    overall: int           # 0-100 composite
    profitability: int     # 0-100
    growth: int           # 0-100
    financial_health: int  # 0-100
    valuation: int         # 0-100
```

**Weighting:**
- Profitability: 30%
- Growth: 25%
- Financial Health: 25%
- Valuation: 20%

---

## Profitability Metrics

### Return on Equity (ROE)
```python
roe = net_income / shareholders_equity
```

**Interpretation:**
| ROE | Quality |
|-----|---------|
| > 20% | Excellent |
| 15-20% | Good |
| 10-15% | Average |
| < 10% | Poor |

**My implementation:**
```python
def score_roe(roe: float) -> int:
    if roe >= 0.20:
        return 100
    elif roe >= 0.15:
        return 80
    elif roe >= 0.10:
        return 60
    else:
        return 40
```

---

### Return on Assets (ROA)
```python
roa = net_income / total_assets
```

**Interpretation:**
| ROA | Quality |
|-----|---------|
| > 10% | Excellent |
| 5-10% | Good |
| 2-5% | Average |
| < 2% | Poor |

**Why it matters:** Measures asset efficiency (capital-light vs capital-heavy)

---

### Gross Margin
```python
gross_margin = gross_profit / revenue
```

**Interpretation:**
| Margin | Quality |
|--------|---------|
| > 40% | Excellent (software, pharma) |
| 25-40% | Good (consumer brands) |
| 15-25% | Average (manufacturing) |
| < 15% | Poor (commodities, retail) |

**Sector matters:** Software companies have higher margins than retailers

---

### Operating Margin
```python
operating_margin = operating_income / revenue
```

**Why it matters:** Shows pricing power and cost control

**Trend analysis:**
- Expanding margin = improving efficiency
- Contracting margin = competitive pressure

---

## Growth Metrics

### Revenue Growth (YoY)
```python
revenue_growth = (revenue_ttm - revenue_prev) / revenue_prev
```

**Interpretation:**
| Growth | Stage |
|--------|-------|
| > 20% | High growth |
| 10-20% | Growth |
| 5-10% | Mature |
| < 5% | Stagnant/declining |

**My implementation:** Score based on growth tier

---

### EPS Growth (YoY)
```python
eps_growth = (eps_ttm - eps_prev) / eps_prev
```

**Why it matters:** Bottom-line growth (includes buybacks, margin expansion)

**Red flag:** Revenue flat, EPS growing → financial engineering

---

### Book Value Growth
```python
bv_growth = (book_value_ps_ttm - book_value_ps_prev) / book_value_ps_prev
```

**Why it matters:** Organic value creation (not financial engineering)

---

## Financial Health Metrics

### Current Ratio
```python
current_ratio = current_assets / current_liabilities
```

**Interpretation:**
| Ratio | Health |
|-------|--------|
| > 2.0 | Excellent |
| 1.5-2.0 | Good |
| 1.0-1.5 | Adequate |
| < 1.0 | Risk (may struggle to pay bills) |

---

### Debt-to-Equity
```python
debt_to_equity = total_debt / shareholders_equity
```

**Interpretation:**
| D/E | Risk |
|-----|------|
| < 0.5 | Low |
| 0.5-1.0 | Moderate |
| 1.0-2.0 | High |
| > 2.0 | Very high (distress risk) |

**Sector matters:** Utilities/banks have higher D/E naturally

---

### Interest Coverage
```python
interest_coverage = operating_income / interest_expense
```

**Interpretation:**
| Ratio | Safety |
|-------|--------|
| > 10x | Excellent |
| 5-10x | Good |
| 3-5x | Adequate |
| < 3x | Risk (may struggle to service debt) |

---

### Altman Z-Score
```python
z_score = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

Where:
X1 = Working Capital / Total Assets
X2 = Retained Earnings / Total Assets
X3 = EBIT / Total Assets
X4 = Market Equity / Total Liabilities
X5 = Sales / Total Assets
```

**Interpretation:**
| Z-Score | Risk |
|---------|------|
| > 3.0 | Safe (low bankruptcy risk) |
| 1.8-3.0 | Grey zone |
| < 1.8 | Distress (high bankruptcy risk) |

**My implementation:** `src/analytics/fundamental_analytics.py`

---

## Valuation Metrics

### P/E Ratio
```python
pe_ratio = price / eps_ttm
```

**Interpretation:**
| P/E | Valuation |
|-----|-----------|
| < 10 | Cheap (or value trap) |
| 10-15 | Fair |
| 15-25 | Premium |
| > 25 | Expensive (or high growth expected) |

**Context matters:** Compare to sector average

---

### PEG Ratio
```python
peg_ratio = pe_ratio / earnings_growth_rate
```

**Interpretation:**
| PEG | Valuation |
|-----|-----------|
| < 1.0 | Undervalued (growth not priced in) |
| 1.0-1.5 | Fair |
| > 1.5 | Overvalued |

**Why it matters:** Adjusts P/E for growth rate

---

### Price-to-Book
```python
pb_ratio = price / book_value_per_share
```

**Interpretation:**
| P/B | Valuation |
|-----|-----------|
| < 1.0 | Cheap (trading below asset value) |
| 1.0-2.0 | Fair |
| > 2.0 | Premium |

**Best for:** Asset-heavy businesses (banks, manufacturing)

---

### Price-to-Sales
```python
ps_ratio = market_cap / revenue_ttm
```

**Interpretation:**
| P/S | Valuation |
|-----|-----------|
| < 1.0 | Cheap |
| 1.0-3.0 | Fair |
| > 3.0 | Premium |

**Best for:** Unprofitable growth companies

---

### Free Cash Flow Yield
```python
fcf_yield = free_cash_flow / market_cap
```

**Interpretation:**
| FCF Yield | Valuation |
|-----------|-----------|
| > 8% | Excellent |
| 5-8% | Good |
| 3-5% | Fair |
| < 3% | Expensive |

**Why it matters:** Cash return to shareholders (buybacks, dividends)

---

## Piotroski F-Score

### 9-Point Checklist
```python
def calculate_piotroski_score(financials: dict) -> int:
    score = 0
    
    # Profitability (4 points)
    score += 1 if financials["net_income"] > 0 else 0
    score += 1 if financials["roa"] > 0 else 0
    score += 1 if financials["cfo"] > 0 else 0  # Cash flow from operations
    score += 1 if financials["cfo"] > financials["net_income"] else 0  # Quality
    
    # Leverage (3 points)
    score += 1 if financials["leverage"] < prev_leverage else 0
    score += 1 if financials["current_ratio"] > prev_cr else 0
    score += 1 if financials["shares_outstanding"] <= prev_shares else 0
    
    # Efficiency (2 points)
    score += 1 if financials["gross_margin"] > prev_gm else 0
    score += 1 if financials["asset_turnover"] > prev_at else 0
    
    return score
```

**Interpretation:**
| Score | Quality |
|-------|---------|
| 8-9 | Excellent (strong fundamentals) |
| 6-7 | Good |
| 4-5 | Average |
| 0-3 | Poor (financial distress likely) |

**My implementation:** `src/analytics/fundamental_analytics.py::calculate_piotroski_score`

---

## Usage Examples

### API
```python
# Get fundamental analysis for single stock
GET /api/v1/fundamentals/AAPL

# Compare multiple stocks
GET /api/v1/fundamentals/compare?symbols=AAPL,MSFT,GOOGL

# Get insider trading data
GET /api/v1/fundamentals/AAPL/insiders
```

### Python
```python
from src.application.services.fundamental_service import FundamentalService

fundamental_service = FundamentalService()

# Get full fundamental report
report = fundamental_service.get_fundamental_analysis("AAPL")
print(f"Overall Health Score: {report.health_score.overall}")
print(f"Piotroski F-Score: {report.piotroski_score}")
print(f"Valuation: {report.health_score.valuation}/100")

# Compare multiple stocks
comparison = fundamental_service.compare_symbols(["AAPL", "MSFT", "GOOGL"])
```

---

## Failure Cases & Edge Cases

### 1. Value Trap
**Symptom:** Low P/E, low P/B, but stock keeps falling

**Cause:** Fundamentals deteriorating (not temporary)

**Detection:**
- Declining revenue (3+ consecutive quarters)
- Negative free cash flow
- Rising debt levels

**Mitigation:** Avoid stocks with negative revenue growth

---

### 2. Growth Trap
**Symptom:** High revenue growth, but stock crashes

**Cause:** Growth at all costs (no path to profitability)

**Detection:**
- Revenue growth > 50%, but margins contracting
- Negative free cash flow
- Dilution (shares outstanding increasing)

**Mitigation:** Require positive FCF or clear path to profitability

---

### 3. Financial Engineering
**Symptom:** EPS growing faster than revenue

**Cause:** Buybacks masking organic decline

**Detection:**
- EPS growth > revenue growth by 10%+
- Shares outstanding decreasing > 5%/year
- Operating margin contracting

**Mitigation:** Focus on revenue + FCF, not just EPS

---

### 4. Sector Mismatch
**Symptom:** Good company scores poorly on metrics

**Cause:** Metrics not appropriate for sector

**Example:**
- Software company: Low P/B (asset-light) ≠ undervalued
- Bank: High D/E (normal for banking) ≠ risky

**Mitigation:** Compare to sector peers, not absolute thresholds

---

## Key Insights

### The Quality Triangle
```
Profitability + Growth + Valuation = Quality Score

High profitability + Low valuation = Value opportunity
High growth + High valuation = Growth stock (fairly priced)
Low profitability + High valuation = Avoid (worst of both)
```

---

### The Red Flag Checklist
Before investing, check:
- [ ] Revenue declining (3+ quarters)
- [ ] Negative free cash flow
- [ ] Debt/Equity > 2.0
- [ ] Interest coverage < 3x
- [ ] Piotroski F-Score < 4
- [ ] Altman Z-Score < 1.8

**Any yes = high risk**

---

### The Fundamental-Technical Hybrid
```
Fundamental analysis: WHAT to buy (which stocks)
Technical analysis: WHEN to buy (entry timing)

Example:
- Fundamental: AAPL scores 80/100 (buy)
- Technical: Wait for EMA crossover or RSI oversold
```

**In my system:** Combine fundamental scores with strategy signals

---

## Related Concepts
- [[Risk Metrics]] — Fundamental risk factors
- [[Portfolio Metrics]] — Fundamental-weighted portfolios
- [[Strategy Design]] — Fundamental-based strategies

## Implementation References
- `src/application/services/fundamental_service.py` — Orchestration
- `src/domain/entities/fundamental.py` — FundamentalReport entity
- `src/infrastructure/data_providers/fundamental_provider.py` — Data fetching
- `src/analytics/fundamental_analytics.py` — Score calculations
