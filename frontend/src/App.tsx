import { useEffect } from 'react';
import axios from 'axios';
import { Header } from './components/layout/Header';
import { BacktestPage } from './pages/BacktestPage';
import { ComparisonPage } from './pages/ComparisonPage';
import type { BacktestConfig } from './lib/schemas';
import { useBacktestStore } from './store';
import { useThemeStore } from './store/useThemeStore';
import './styles/index.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const {
    strategies, activeTab, setActiveTab,
    setResult, setTrades, setLoading, setError,
    setEquityCurve, setDrawdownSeries, setMonthlyReturns,
    setComparisonResult, setComparisonLoading,
  } = useBacktestStore();
  const { theme } = useThemeStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const runBacktest = async (config: BacktestConfig) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/v1/backtests/run`, {
        strategy_name: config.strategy_name,
        symbol: config.symbol,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        commission: 0.001,
        slippage: 0.0005,
      });
      setResult(response.data.results);
      setTrades(response.data.trades || []);
      setEquityCurve(response.data.equity_curve || []);
      setDrawdownSeries(response.data.drawdown_series || []);
      setMonthlyReturns(response.data.monthly_returns || []);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const compareStrategies = async (
    strategyNames: string[],
    config: { symbol: string; start_date: string; end_date: string; initial_capital: number }
  ) => {
    setComparisonLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/v1/backtests/compare`, {
        strategy_names: strategyNames,
        symbol: config.symbol,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        commission: 0.001,
        slippage: 0.0005,
      });
      setComparisonResult(response.data);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || (err as Error).message);
    } finally {
      setComparisonLoading(false);
    }
  };

  const generateMockResult = () => {
    const capital = 100000;
    const mockResult = {
      final_capital: capital * (1 + (Math.random() * 0.4 - 0.1)),
      total_return: Math.random() * 0.4 - 0.1,
      total_trades: Math.floor(Math.random() * 50) + 10,
      metrics: {
        sharpe_ratio: Math.random() * 3 - 1,
        max_drawdown_pct: Math.random() * 20 + 5,
        win_rate: Math.random() * 0.6 + 0.2,
        sortino_ratio: Math.random() * 4 - 1,
        profit_factor: Math.random() * 2 + 0.5,
      },
    };
    setResult(mockResult);

    // Generate mock chart data
    const days = 252;
    let equity = capital;
    const mockEquity = [];
    const mockDrawdown = [];
    let peak = equity;

    for (let i = 0; i < days; i++) {
      const date = new Date(2023, 0, 1);
      date.setDate(date.getDate() + i);
      equity *= (1 + (Math.random() * 0.04 - 0.018));
      if (equity > peak) peak = equity;
      const dd = ((equity - peak) / peak) * 100;

      mockEquity.push({ date: date.toISOString(), equity: Math.round(equity * 100) / 100 });
      mockDrawdown.push({ date: date.toISOString(), drawdown: Math.round(dd * 100) / 100 });
    }

    const mockMonthly = [];
    for (let m = 1; m <= 12; m++) {
      mockMonthly.push({ year: 2023, month: m, return_pct: Math.round((Math.random() * 10 - 4) * 100) / 100 });
    }

    setEquityCurve(mockEquity);
    setDrawdownSeries(mockDrawdown);
    setMonthlyReturns(mockMonthly);

    const mockTrades = Array.from({ length: mockResult.total_trades }, () => ({
      entry_time: new Date().toISOString(),
      exit_time: new Date().toISOString(),
      entry_price: 100 + Math.random() * 20,
      exit_price: 100 + Math.random() * 20,
      pnl: Math.random() * 2000 - 800,
      pnl_pct: Math.random() * 10 - 4,
      side: Math.random() > 0.5 ? 'LONG' : 'SHORT',
    }));
    setTrades(mockTrades);
  };

  return (
    <div className="app-layout">
      <Header
        title="Trading Strategy Research Lab"
        subtitle="AI-Powered Quantitative Trading Platform"
      />

      {/* Tab Navigation */}
      <div className="app-tabs">
        <div className="app-tabs-inner">
          <button
            className={`app-tab ${activeTab === 'backtest' ? 'app-tab-active' : ''}`}
            onClick={() => setActiveTab('backtest')}
          >
            Backtest
          </button>
          <button
            className={`app-tab ${activeTab === 'compare' ? 'app-tab-active' : ''}`}
            onClick={() => setActiveTab('compare')}
          >
            Compare
          </button>
        </div>
      </div>

      <main className="app-main">
        {activeTab === 'backtest' ? (
          <BacktestPage
            strategies={strategies}
            onRunBacktest={runBacktest}
            onGenerateDemo={generateMockResult}
          />
        ) : (
          <ComparisonPage
            strategies={strategies}
            onCompare={compareStrategies}
          />
        )}
      </main>
    </div>
  );
}

export default App;
