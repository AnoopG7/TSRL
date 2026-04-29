import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Search, Building2, TrendingUp, TrendingDown, DollarSign, BarChart3,
  Newspaper, Activity, ShieldCheck, AlertTriangle, ArrowUpRight, ArrowDownRight,
  ExternalLink, Globe, Users, Briefcase, Lock, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { useFundamentals, useCompareFundamentals } from '../hooks/apiHooks';
import { useDataSourceStore } from '../store/useDataSourceStore';
import { formatCurrency, formatLargeCurrency } from '../lib/utils';
import { MetricCard } from '../components/ui/MetricCard';
import { FinancialTrendsChart } from '../components/charts/FinancialTrendsChart';
import { RadarScoreChart } from '../components/charts/RadarScoreChart';
import { HealthScoreGauge } from '../components/fundamentals/HealthScoreGauge';
import { RatioTable } from '../components/fundamentals/RatioTable';
import { NewsCard } from '../components/fundamentals/NewsCard';
import { QualityScores } from '../components/fundamentals/QualityScores';
import { EpsSurpriseChart } from '../components/charts/EpsSurpriseChart';
import { InsiderTracker } from '../components/fundamentals/InsiderTracker';
import { ComparisonTable } from '../components/fundamentals/ComparisonTable';
import { SkeletonFundamentals } from '../components/fundamentals/SkeletonFundamentals';
import type { FundamentalReport, FundamentalComparison } from '../lib/schemas/fundamental.schema';

type TabKey = 'overview' | 'financials' | 'ratios' | 'news' | 'insiders';

export function FundamentalsPage() {
  const [symbol, setSymbol] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [source, setSource] = useState<'yfinance' | 'fmp'>('yfinance');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();
  const { market } = useDataSourceStore();
  
  // Single Stock Mode
  const { data, isLoading: singleLoading, error: singleError, refetch } = useFundamentals(symbol, source, !symbol.includes(','), true);
  
  // Handle refresh
  const handleRefresh = async () => {
    if (!symbol || symbol.includes(',')) return;
    setIsRefreshing(true);
    queryClient.invalidateQueries({ queryKey: ['fundamentals', symbol, source] });
    await refetch();
    setIsRefreshing(false);
    toast.success('Data refreshed!');
  };
  
  // Comparison Mode
  const [isCompareMode, setIsCompareMode] = useState(false);
  const { mutate: fetchCompare, data: compareData, isPending: compareLoading, error: compareError } = useCompareFundamentals();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const sym = searchInput.trim().toUpperCase();
    if (!sym) {
      toast.error('Enter a stock symbol');
      return;
    }
    
    // Check if it's a comma separated list for comparison
    const symList = sym.split(',').map(s => s.trim()).filter(Boolean);
    
    if (symList.length > 1) {
      setIsCompareMode(true);
      setSymbol(symList.join(',')); // Just for UI syncing
      fetchCompare({ symbols: symList.join(','), source });
    } else {
      setIsCompareMode(false);
      setSymbol(symList[0]);
      setActiveTab('overview');
    }
  };

  const handleRemoveTicker = (symToRemove: string) => {
    if (!compareData) return;
    const newList = compareData.symbols.filter((s: string) => s !== symToRemove);
    if (newList.length > 1) {
      setSearchInput(newList.join(', '));
      setSymbol(newList.join(','));
      fetchCompare({ symbols: newList.join(','), source });
    } else if (newList.length === 1) {
      setSearchInput(newList[0]);
      setIsCompareMode(false);
      setSymbol(newList[0]);
    } else {
      setIsCompareMode(false);
      setSymbol('');
      setSearchInput('');
    }
  };

  const isLoading = isCompareMode ? compareLoading : singleLoading;
  const error = isCompareMode ? compareError : singleError;

  const report = data as FundamentalReport | undefined;
  const comparisonData = compareData as FundamentalComparison | undefined;

  const formatPct = (value: number | null | undefined) => {
    if (value == null) return '—';
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatRatio = (value: number | null | undefined) => {
    if (value == null) return '—';
    return value.toFixed(2);
  };

  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <Building2 size={14} /> },
    { key: 'financials', label: 'Financials', icon: <BarChart3 size={14} /> },
    { key: 'ratios', label: 'Ratios', icon: <Activity size={14} /> },
    { key: 'news', label: 'News & Sentiment', icon: <Newspaper size={14} /> },
    { key: 'insiders', label: 'Insiders', icon: <Lock size={14} /> },
  ];

  return (
    <div className="animate-fadeIn">
      {/* Search Bar */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <Search size={20} style={{ color: 'var(--color-accent-400)' }} />
            <h2 className="card-title">Fundamental Analysis</h2>
          </div>
          <p className="card-description">
            Enter a stock symbol to analyze company fundamentals, financial health, and market sentiment
          </p>
        </div>
        <div className="card-content">
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 'var(--spacing-sm)' }}>
            <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
              <label className="form-label" style={{ marginBottom: '2px' }}>Stock Symbol(s)</label>
              <input
                type="text"
                className="form-input"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL, MSFT, GOOGL"
                style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}
              />
            </div>
            
            <div className="form-group">
              <label className="form-label" style={{ marginBottom: '2px' }}>Data Source</label>
              <div className="tab-nav" style={{ height: '40px', alignItems: 'center' }}>
                <button
                  type="button"
                  className={`tab-item ${source === 'yfinance' ? 'tab-active' : ''}`}
                  onClick={() => setSource('yfinance')}
                  style={{ height: '32px' }}
                >
                  Yahoo (Free)
                </button>
                <button
                  type="button"
                  className={`tab-item ${source === 'fmp' ? 'tab-active' : ''}`}
                  onClick={() => setSource('fmp')}
                  style={{ height: '32px' }}
                >
                  FMP (Paid)
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--spacing-sm)', height: '40px', alignItems: 'center' }}>
              <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ height: '40px' }}>
                {isLoading ? 'Analyzing...' : 'Analyze'}
              </button>
              {report && !isLoading && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  title="Force Refresh"
                  style={{ height: '40px' }}
                >
                  <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </button>
              )}
            </div>
          </form>

          {/* Cache Banner */}
          {report?.from_cache && (
            <div style={{
              marginTop: 'var(--spacing-md)',
              padding: 'var(--spacing-sm) var(--spacing-md)',
              background: 'var(--color-warning-bg, rgba(251, 191, 36, 0.1))',
              border: '1px solid var(--color-warning, #f59e0b)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              fontSize: '0.875rem',
              color: 'var(--color-warning, #f59e0b)'
            }}>
              <AlertTriangle size={16} />
              <span>Showing cached data from {report.fetch_timestamp ? new Date(report.fetch_timestamp).toLocaleString() : 'unknown time'}</span>
            </div>
          )}

          {error && (
            <div className="error-message" style={{ marginTop: 'var(--spacing-md)' }}>
              <AlertTriangle size={16} />
              {error instanceof Error ? error.message : 'Failed to fetch data'}
            </div>
          )}
        </div>
      </section>

      {/* Loading State */}
      {isLoading && <SkeletonFundamentals />}

      {/* Comparison Results */}
      {isCompareMode && !isLoading && comparisonData && (
        <ComparisonTable data={comparisonData} onRemoveTicker={handleRemoveTicker} market={market} />
      )}

      {/* Single Results */}
      {!isCompareMode && !isLoading && report && (
        <>
          {/* Company Header */}
          <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <div className="card-content" style={{ padding: 'var(--spacing-lg)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
                <div>
                  <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 'var(--spacing-xs)' }}>
                    {report.company_name}
                    <span style={{ color: 'var(--color-accent-400)', marginLeft: 'var(--spacing-sm)', fontSize: '1rem', fontWeight: 500 }}>
                      {report.symbol}
                    </span>
                  </h1>
                  <div style={{ display: 'flex', gap: 'var(--spacing-lg)', flexWrap: 'wrap', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                    <span className="badge badge-success" style={{ background: 'var(--color-bg-input)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-default)' }}>
                      Source: {report.data_source === 'fmp' ? 'FMP API' : 'Yahoo Finance'}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Briefcase size={14} /> {report.sector} · {report.industry}
                    </span>
                    {report.employees && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Users size={14} /> {report.employees.toLocaleString()} employees
                      </span>
                    )}
                    {report.website && (
                      <a href={report.website} target="_blank" rel="noopener noreferrer"
                        style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-accent-400)' }}>
                        <Globe size={14} /> Website <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 700 }}>
                    {formatCurrency(report.current_price)}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    Mkt Cap: {formatLargeCurrency(report.market_cap)}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Tab Navigation */}
          <div className="tab-nav" style={{ marginBottom: 'var(--spacing-lg)' }}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`tab-item ${activeTab === tab.key ? 'tab-active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="animate-fadeIn">
              {/* Health Score + Key Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                <HealthScoreGauge
                  score={report.health_score}
                  grade={report.health_grade}
                  breakdown={report.score_breakdown}
                />
                <section className="card">
                  <div className="card-header">
                    <h2 className="card-title">Key Metrics</h2>
                  </div>
                  <div className="card-content">
                    <div className="metric-grid">
                      <MetricCard label="P/E Ratio" value={formatRatio(report.pe_ratio)} icon={<DollarSign size={16} />} />
                      <MetricCard label="ROE" value={formatPct(report.roe)}
                        icon={report.roe && report.roe >= 0.15 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                        positive={report.roe != null && report.roe >= 0.15} />
                      <MetricCard label="Net Margin" value={formatPct(report.net_margin)}
                        positive={report.net_margin != null && report.net_margin > 0.1} />
                      <MetricCard label="D/E Ratio" value={formatRatio(report.debt_to_equity)}
                        negative={report.debt_to_equity != null && report.debt_to_equity > 1.5} />
                      <MetricCard label="Current Ratio" value={formatRatio(report.current_ratio)}
                        positive={report.current_ratio != null && report.current_ratio >= 1.5} />
                      <MetricCard label="FCF Margin" value={formatPct(report.fcf_margin)}
                        positive={report.fcf_margin != null && report.fcf_margin > 0.1} />
                      <MetricCard label="Rev Growth 3yr" value={formatPct(report.revenue_cagr_3yr)}
                        icon={report.revenue_cagr_3yr && report.revenue_cagr_3yr > 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        positive={report.revenue_cagr_3yr != null && report.revenue_cagr_3yr > 0.05} />
                      <MetricCard label="Beta" value={formatRatio(report.beta)} />
                    </div>
                  </div>
                </section>
              </div>

              {/* Analyst & 52-week */}
              <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                <div className="card-header">
                  <h2 className="card-title">Analyst Consensus & Market Position</h2>
                </div>
                <div className="card-content">
                  <div className="metric-grid">
                    <MetricCard label="Analyst Rating" value={report.analyst_rating?.replace('_', ' ').toUpperCase() || '—'}
                      icon={<ShieldCheck size={16} />}
                      positive={report.analyst_rating === 'buy' || report.analyst_rating === 'strong_buy'} />
                    <MetricCard label="Price Target" value={formatCurrency(report.target_price)} />
                    <MetricCard label="Analysts" value={String(report.analyst_count ?? '—')} />
                    <MetricCard label="Dividend Yield" value={formatPct(report.dividend_yield)} />
                    <MetricCard label="52W High" value={formatCurrency(report.week_52_high)} />
                    <MetricCard label="52W Low" value={formatCurrency(report.week_52_low)} />
                    <MetricCard label="Short Interest" value={formatPct(report.short_interest)}
                      negative={report.short_interest != null && report.short_interest > 0.1} />
                    <MetricCard label="EPS (TTM)" value={formatCurrency(report.eps_trailing)} />
                  </div>
                </div>
              </section>

              {/* Quality Scores */}
              <QualityScores report={report} />

              {/* Description */}
              {report.description && (
                <section className="card">
                  <div className="card-header">
                    <h2 className="card-title">About {report.company_name}</h2>
                  </div>
                  <div className="card-content">
                    <p style={{ lineHeight: 1.7, color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                      {report.description.length > 600 ? report.description.slice(0, 600) + '...' : report.description}
                    </p>
                  </div>
                </section>
              )}
            </div>
          )}

          {activeTab === 'financials' && (
            <div className="animate-fadeIn">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
                <FinancialTrendsChart
                  revenue={report.annual_revenue || []}
                  netIncome={report.annual_net_income || []}
                  fcf={report.annual_fcf || []}
                  grossMargin={report.annual_gross_margin || []}
                  operatingMargin={report.annual_operating_margin || []}
                  companyName={report.company_name}
                />
                <EpsSurpriseChart history={report.eps_surprise_history || []} market={market} />
              </div>
            </div>
          )}

          {activeTab === 'ratios' && (
            <div className="animate-fadeIn">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                <RadarScoreChart breakdown={report.score_breakdown} />
                <HealthScoreGauge score={report.health_score} grade={report.health_grade} breakdown={report.score_breakdown} />
              </div>
              <RatioTable report={report} market={market} />
            </div>
          )}

          {activeTab === 'news' && (
            <div className="animate-fadeIn">
              {/* Sentiment Banner */}
              {report.sentiment && (
                <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                  <div className="card-content" style={{ padding: 'var(--spacing-lg)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
                      <div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                          Market Sentiment
                        </div>
                        <div style={{
                          fontSize: '1.5rem', fontWeight: 700,
                          color: report.sentiment.label === 'Bullish' ? 'var(--color-positive)' :
                                 report.sentiment.label === 'Bearish' ? 'var(--color-negative)' :
                                 'var(--color-text-secondary)',
                        }}>
                          {report.sentiment.label}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 'var(--spacing-lg)' }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Score</div>
                          <div style={{ fontWeight: 600 }}>{report.sentiment.avg_sentiment?.toFixed(3) ?? '—'}</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Articles</div>
                          <div style={{ fontWeight: 600 }}>{report.sentiment.article_count ?? 0}</div>
                        </div>
                        {report.sentiment.confidence != null && (
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Confidence</div>
                            <div style={{ fontWeight: 600 }}>{(report.sentiment.confidence * 100).toFixed(0)}%</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </section>
              )}

              {/* News Feed */}
              <section className="card">
                <div className="card-header">
                  <h2 className="card-title">Recent News</h2>
                  <p className="card-description">Latest headlines from Finnhub</p>
                </div>
                <div className="card-content">
                  {report.news && report.news.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                      {report.news.map((article, idx: number) => (
                        <NewsCard key={idx} article={article} />
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                      No news available. Make sure FINNHUB_API_KEY is set in config/.env
                    </p>
                  )}
                </div>
              </section>
            </div>
          )}

          {activeTab === 'insiders' && (
            <div className="animate-fadeIn">
              <InsiderTracker symbol={report.symbol} source={source} market={market} />
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!report && !isLoading && !error && (
        <section className="card">
          <div className="card-content" style={{ textAlign: 'center', padding: 'var(--spacing-xl) var(--spacing-lg)' }}>
            <Building2 size={48} style={{ color: 'var(--color-text-tertiary)', margin: '0 auto var(--spacing-md)' }} />
            <h3 style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-sm)' }}>
              Enter a symbol to start analysis
            </h3>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>
              Try AAPL, MSFT, GOOGL, TSLA, AMZN, NVDA, or any listed stock
            </p>
          </div>
        </section>
      )}

      {/* Fundamentals Data Attribution Footer (Plan Item 8) */}
      {report && !isCompareMode && (
        <footer style={{
          marginTop: 'var(--spacing-xl)',
          padding: 'var(--spacing-lg)',
          borderTop: '1px solid var(--color-border-default)',
          fontSize: '0.75rem',
          color: 'var(--color-text-tertiary)',
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Price & Ratios</div>
              <div>{report.data_source === 'fmp' ? 'Financial Modeling Prep' : 'Yahoo Finance'} · ~15 min delay</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Financial Statements</div>
              <div>{report.data_source === 'fmp' ? 'Financial Modeling Prep' : 'Yahoo Finance'} · Quarterly updates</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>News & Sentiment</div>
              <div>Finnhub · Real-time</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Insider Transactions</div>
              <div>Finnhub / FMP / SEC EDGAR · Within 2 business days of filing</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>EPS Surprise</div>
              <div>Finnhub · Post-earnings (last 4 quarters)</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Health & Quality Scores</div>
              <div>Computed server-side · Recalculated per request</div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-sm)', paddingTop: 'var(--spacing-sm)', borderTop: '1px solid var(--color-border-default)' }}>
            <span>
              {report.fetch_timestamp
                ? `Last updated: ${new Date(report.fetch_timestamp).toLocaleString()}`
                : 'Fundamental data cached for 1 hour · Use Refresh to force a live fetch'}
            </span>
            <span style={{ color: 'var(--color-text-tertiary)' }}>
              For research purposes only · Not financial advice
            </span>
          </div>
        </footer>
      )}
    </div>
  );
}
