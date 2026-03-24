import { useEffect } from 'react';
import axios from 'axios';
import { Header } from './components/layout/Header';
import { BacktestPage } from './pages/BacktestPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { PortfolioPage } from './pages/PortfolioPage';
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
    setStrategies,
  } = useBacktestStore();
  const { theme } = useThemeStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Fetch strategies from API on load, fall back to hardcoded list if API fails
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/strategies`);
        if (res.data.strategies && res.data.strategies.length > 0) {
          setStrategies(res.data.strategies);
        }
      } catch (err: unknown) {
        console.error('Failed to fetch strategies from API:', err);
      }
    };
    fetchStrategies();
  }, [setStrategies]);

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

  const runPortfolioBacktest = async (config: {
    strategy_name: string;
    symbols: string;
    weights: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    rebalance_frequency: string;
    rebalance_threshold: string;
    benchmark_symbol: string;
  }) => {
    try {
      // Parse symbols from comma-separated string
      const symbolList = config.symbols.split(',').map(s => s.trim()).filter(Boolean);

      // Parse weights if provided
      let weightsDict: Record<string, number> | undefined;
      if (config.weights.trim()) {
        const weightValues = config.weights.split(',').map(w => parseFloat(w.trim()));
        if (weightValues.length === symbolList.length) {
          weightsDict = {};
          symbolList.forEach((sym, i) => {
            weightsDict![sym] = weightValues[i];
          });
        }
      }

      const response = await axios.post(`${API_URL}/api/v1/backtests/portfolio`, {
        strategy_name: config.strategy_name,
        symbols: symbolList,
        weights: weightsDict,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        rebalance_frequency: config.rebalance_frequency,
        rebalance_threshold: config.rebalance_threshold ? parseFloat(config.rebalance_threshold) : undefined,
        benchmark_symbol: config.benchmark_symbol || undefined,
      });

      return {
        symbols: response.data.symbols,
        weights: response.data.weights,
        results: {
          total_return: response.data.results?.total_return || 0,
          total_trades: response.data.results?.total_trades || 0,
          sharpe_ratio: response.data.results?.sharpe_ratio || 0,
          max_drawdown: response.data.results?.max_drawdown || 0,
          win_rate: response.data.results?.win_rate || 0,
          execution_time_ms: response.data.results?.execution_time_ms || 0,
        },
        rebalancing: {
          total_events: response.data.rebalancing?.total_events || 0,
          total_cost: response.data.rebalancing?.total_cost || 0,
        },
        portfolio_metrics: response.data.portfolio_metrics || null,
        equity_curve: response.data.equity_curve || [],
        per_asset_results: response.data.per_asset_results || {},
      };
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      throw new Error(axiosError.response?.data?.detail || (err as Error).message);
    }
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
          <button
            className={`app-tab ${activeTab === 'portfolio' ? 'app-tab-active' : ''}`}
            onClick={() => setActiveTab('portfolio')}
          >
            Portfolio
          </button>
        </div>
      </div>

      <main className="app-main">
        {activeTab === 'backtest' && (
          <BacktestPage
            strategies={strategies}
            onRunBacktest={runBacktest}
          />
        )}
        {activeTab === 'compare' && (
          <ComparisonPage
            strategies={strategies}
            onCompare={compareStrategies}
          />
        )}
        {activeTab === 'portfolio' && (
          <PortfolioPage
            strategies={strategies}
            onRunPortfolio={runPortfolioBacktest}
          />
        )}
      </main>
    </div>
  );
}

export default App;
