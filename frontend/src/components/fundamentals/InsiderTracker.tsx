import { useInsiders } from '../../hooks/apiHooks';
import { MetricCard } from '../ui/MetricCard';
import { DollarSign, AlertTriangle, ShieldCheck, HandHeart } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface InsiderTransaction {
  name: string;
  position: string;
  transaction_type: string;
  shares: number;
  price: number;
  value: number;
  date: string;
  is_10b5_plan: boolean;
}

interface InsidersData {
  transactions: InsiderTransaction[];
  net_sentiment: number;
  net_buy_value: number;
}

interface Props {
  symbol: string;
  source?: 'yfinance' | 'fmp';
}

interface TooltipPayload {
  payload?: { month: string; buy: number; sell: number };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    if (!data) return null;
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-header">{label}</div>
        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">Buy</span>
          <span className="chart-tooltip-value positive">${data.buy.toLocaleString()}</span>
        </div>
        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">Sell</span>
          <span className="chart-tooltip-value negative">${data.sell.toLocaleString()}</span>
        </div>
      </div>
    );
  }
  return null;
};

export function InsiderTracker({ symbol, source = 'yfinance' }: Props) {
  const { data, isLoading, error } = useInsiders(symbol, source);

  if (isLoading) {
    return (
      <div className="skeleton" style={{ height: '400px', width: '100%', borderRadius: 'var(--radius-lg)' }} />
    );
  }

  if (error || !data) {
    return (
      <section className="card">
        <div className="card-content" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
          <AlertTriangle size={48} style={{ color: 'var(--color-warning)', margin: '0 auto var(--spacing-md)' }} />
          <h3 style={{ color: 'var(--color-text-primary)' }}>Failed to load Insider Data</h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
            Check your API keys or rate limits.
          </p>
        </div>
      </section>
    );
  }

  const txs = (data as InsidersData).transactions || [];
  const netSentiment = (data as InsidersData).net_sentiment;
  const netBuyValue = (data as InsidersData).net_buy_value;

  const formatCurrency = (val: number): string => {
    return `$${Math.abs(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  };

  const timelineData: { month: string; buy: number; sell: number }[] = [];
  const monthMap: Record<string, { month: string; buy: number; sell: number }> = {};
  
  txs.forEach((t: InsiderTransaction) => {
    if (t.is_10b5_plan) return;
    const month = t.date.substring(0, 7);
    if (!monthMap[month]) monthMap[month] = { month, buy: 0, sell: 0 };
    
    if (t.transaction_type === 'P') {
      monthMap[month].buy += t.value;
    } else {
      monthMap[month].sell += Math.abs(t.value);
    }
  });

  Object.values(monthMap).forEach((v) => timelineData.push(v));
  timelineData.sort((a, b) => a.month.localeCompare(b.month));

  const totalBuys = txs.filter((t: InsiderTransaction) => t.transaction_type === 'P').length;
  const totalSells = txs.filter((t: InsiderTransaction) => t.transaction_type === 'S').length;
  const sentimentLabel = netSentiment == null
    ? 'N/A'
    : netSentiment > 0.5 ? 'Strong Buy'
    : netSentiment > 0 ? 'Buy'
    : netSentiment < -0.5 ? 'Strong Sell'
    : netSentiment < 0 ? 'Sell'
    : 'Neutral';

  return (
    <section className="card animate-fadeIn">
      <div className="card-header">
        <h2 className="card-title">Insider Trading Activity</h2>
        <p className="card-description">SEC Form 4 filings - management conviction signal</p>
      </div>
      <div className="card-content">
        <div className="metric-grid" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <MetricCard
            label="Net Buy Value"
            value={netBuyValue != null ? formatCurrency(netBuyValue) : '—'}
            icon={<DollarSign size={16} />}
            positive={netBuyValue != null && netBuyValue > 0}
            negative={netBuyValue != null && netBuyValue < 0}
          />
          <MetricCard
            label="Total Buys"
            value={String(totalBuys)}
            icon={<ShieldCheck size={16} />}
            positive
          />
          <MetricCard
            label="Total Sells"
            value={String(totalSells)}
            icon={<HandHeart size={16} />}
            negative
          />
          <MetricCard
            label="Net Sentiment"
            value={sentimentLabel}
            icon={<AlertTriangle size={16} />}
            positive={netSentiment > 0}
            negative={netSentiment < 0}
          />
        </div>

        {timelineData.length > 0 && (
          <div className="chart-container" style={{ height: '250px', marginTop: 'var(--spacing-lg)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timelineData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border-default)" />
                <XAxis dataKey="month" tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
                <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'var(--color-bg-hover)' }} />
                <Bar dataKey="buy" stackId="a" fill="var(--color-positive)" radius={[2, 2, 0, 0]} name="Buy" />
                <Bar dataKey="sell" stackId="a" fill="var(--color-negative)" radius={[2, 2, 0, 0]} name="Sell" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div style={{ marginTop: 'var(--spacing-lg)', overflowX: 'auto' }} className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Insider</th>
                <th>Position</th>
                <th>Type</th>
                <th>Shares</th>
                <th style={{ textAlign: 'right' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {txs.slice(0, 15).map((t: InsiderTransaction, idx: number) => (
                <tr key={idx}>
                  <td>{t.date}</td>
                  <td>{t.name}</td>
                  <td>{t.position}</td>
                  <td>
                    <span className={`badge ${t.transaction_type === 'P' ? 'badge-success' : 'badge-danger'}`}>
                      {t.transaction_type === 'P' ? 'Buy' : 'Sell'}
                    </span>
                    {t.is_10b5_plan && <span className="badge" style={{ marginLeft: '4px', background: 'var(--color-bg-input)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-default)' }}>10b5-1</span>}
                  </td>
                  <td>{t.shares.toLocaleString()}</td>
                  <td style={{ textAlign: 'right' }}>{formatCurrency(t.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}