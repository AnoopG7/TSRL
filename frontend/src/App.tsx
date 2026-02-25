import { useEffect } from 'react';
import axios from 'axios';
import { Header } from './components/layout/Header';
import { BacktestPage } from './pages/BacktestPage';
import type { BacktestConfig } from './lib/schemas';
import { useBacktestStore } from './store';
import { useThemeStore } from './store/useThemeStore';
import './styles/index.css';

const defaultStrategies = [
  { name: 'ema_crossover', version: '1.0.0', type: 'momentum', description: 'EMA Crossover Strategy' },
  { name: 'rsi_mean_reversion', version: '1.0.0', type: 'mean_reversion', description: 'RSI Mean Reversion' },
  { name: 'breakout', version: '1.0.0', type: 'breakout', description: 'Breakout Strategy' },
];

function App() {
  const { setResult, setTrades, setLoading, setError } = useBacktestStore();
  const { theme } = useThemeStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const runBacktest = async (config: BacktestConfig) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/api/v1/backtests/run', {
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
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || (err as Error).message);
    } finally {
      setLoading(false);
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
      <main className="app-main">
        <BacktestPage
          strategies={defaultStrategies}
          onRunBacktest={runBacktest}
          onGenerateDemo={generateMockResult}
        />
      </main>
    </div>
  );
}

export default App;
