import { z } from 'zod';

// ── Fundamental Report Schema ──────────────────────────────────────────

export const FundamentalReportSchema = z.object({
  status: z.string().optional(),
  from_cache: z.boolean().optional(),
  symbol: z.string(),
  company_name: z.string(),
  sector: z.string(),
  industry: z.string(),
  description: z.string(),
  market_cap: z.number(),
  current_price: z.number(),
  currency: z.string(),
  employees: z.number().nullable().optional(),
  website: z.string().nullable().optional(),
  exchange: z.string().nullable().optional(),

  // Valuation
  pe_ratio: z.number().nullable().optional(),
  forward_pe: z.number().nullable().optional(),
  peg_ratio: z.number().nullable().optional(),
  pb_ratio: z.number().nullable().optional(),
  ps_ratio: z.number().nullable().optional(),
  ev_ebitda: z.number().nullable().optional(),
  ev_revenue: z.number().nullable().optional(),

  // Profitability
  gross_margin: z.number().nullable().optional(),
  operating_margin: z.number().nullable().optional(),
  net_margin: z.number().nullable().optional(),
  ebitda_margin: z.number().nullable().optional(),
  roe: z.number().nullable().optional(),
  roa: z.number().nullable().optional(),
  eps_trailing: z.number().nullable().optional(),
  eps_forward: z.number().nullable().optional(),
  revenue_growth: z.number().nullable().optional(),
  earnings_growth: z.number().nullable().optional(),

  // Liquidity
  current_ratio: z.number().nullable().optional(),
  quick_ratio: z.number().nullable().optional(),

  // Solvency
  debt_to_equity: z.number().nullable().optional(),
  interest_coverage: z.number().nullable().optional(),
  long_term_debt_to_capital: z.number().nullable().optional(),

  // Cash Flow
  free_cash_flow: z.number().nullable().optional(),
  fcf_margin: z.number().nullable().optional(),
  fcf_yield: z.number().nullable().optional(),
  operating_cash_flow: z.number().nullable().optional(),
  cash_conversion: z.number().nullable().optional(),

  // Growth
  revenue_cagr_3yr: z.number().nullable().optional(),
  revenue_cagr_5yr: z.number().nullable().optional(),
  earnings_cagr_3yr: z.number().nullable().optional(),
  fcf_cagr_3yr: z.number().nullable().optional(),

  // Trends (for charts)
  annual_revenue: z.array(z.object({ year: z.union([z.number(), z.string()]), value: z.number() })).optional(),
  annual_net_income: z.array(z.object({ year: z.union([z.number(), z.string()]), value: z.number() })).optional(),
  annual_fcf: z.array(z.object({ year: z.union([z.number(), z.string()]), value: z.number() })).optional(),
  annual_gross_margin: z.array(z.object({ year: z.union([z.number(), z.string()]), value: z.number() })).optional(),
  annual_operating_margin: z.array(z.object({ year: z.union([z.number(), z.string()]), value: z.number() })).optional(),

  // Analyst
  analyst_rating: z.string().nullable().optional(),
  analyst_rating_score: z.number().nullable().optional(),
  target_price: z.number().nullable().optional(),
  target_high: z.number().nullable().optional(),
  target_low: z.number().nullable().optional(),
  analyst_count: z.number().nullable().optional(),
  dividend_yield: z.number().nullable().optional(),
  payout_ratio: z.number().nullable().optional(),
  beta: z.number().nullable().optional(),
  short_interest: z.number().nullable().optional(),
  week_52_high: z.number().nullable().optional(),
  week_52_low: z.number().nullable().optional(),

  // News & sentiment
  news: z.array(z.object({
    headline: z.string(),
    summary: z.string(),
    url: z.string(),
    datetime: z.string(),
    source: z.string(),
    category: z.string().optional(),
    image: z.string().optional(),
  })).optional(),
  sentiment: z.object({
    avg_sentiment: z.number(),
    label: z.string(),
    article_count: z.number(),
    confidence: z.number().optional(),
  }).optional(),

  // Health score
  health_score: z.number().nullable().optional(),
  health_grade: z.string().nullable().optional(),
  score_breakdown: z.record(
    z.string(),
    z.object({
      score: z.number(),
      weight: z.number(),
      metrics: z.record(z.string(), z.number()).optional(),
    })
  ).optional(),

  // Quantitative Quality Scores
  piotroski_score: z.number().nullable().optional(),
  piotroski_breakdown: z.record(z.string(), z.number()).optional(),
  altman_z_score: z.number().nullable().optional(),
  altman_z_zone: z.string().nullable().optional(),
  eps_surprise_history: z.array(z.object({
    quarter: z.string(),
    actual: z.number(),
    estimate: z.number(),
    surprise: z.number(),
    surprise_pct: z.number()
  })).default([]),

  // Insider Trading
  insider_transactions: z.array(z.object({
    name: z.string(),
    position: z.string(),
    transaction_type: z.string(),
    shares: z.number(),
    price: z.number(),
    value: z.number(),
    date: z.string(),
    is_10b5_plan: z.boolean(),
  })).default([]),
  insider_net_sentiment: z.number().nullable().optional(),
  insider_net_buy_value: z.number().nullable().optional(),

  // Provenance
  data_source: z.string().optional(),
  fetch_timestamp: z.string().nullable().optional(),
});

export type FundamentalReport = z.infer<typeof FundamentalReportSchema>;

// ── Comparison response ────────────────────────────────────────────────

export const FundamentalComparisonSchema = z.object({
  status: z.string(),
  symbols: z.array(z.string()),
  comparison: z.record(
    z.string(),
    z.object({
      company_name: z.string().optional(),
      sector: z.string().optional(),
      market_cap: z.number().optional(),
      current_price: z.number().optional(),
      pe_ratio: z.number().nullable().optional(),
      pb_ratio: z.number().nullable().optional(),
      ps_ratio: z.number().nullable().optional(),
      ev_ebitda: z.number().nullable().optional(),
      roe: z.number().nullable().optional(),
      roa: z.number().nullable().optional(),
      gross_margin: z.number().nullable().optional(),
      net_margin: z.number().nullable().optional(),
      debt_to_equity: z.number().nullable().optional(),
      current_ratio: z.number().nullable().optional(),
      fcf_margin: z.number().nullable().optional(),
      revenue_cagr_3yr: z.number().nullable().optional(),
      health_score: z.number().nullable().optional(),
      health_grade: z.string().nullable().optional(),
      error: z.string().optional(),
    })
  ),
});

export type FundamentalComparison = z.infer<typeof FundamentalComparisonSchema>;
