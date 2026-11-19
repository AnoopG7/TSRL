import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { BacktestPage } from './pages/BacktestPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { WalkForwardPage } from './pages/WalkForwardPage';
import { MLLabPage } from './pages/MLLabPage';
import { FundamentalsPage } from './pages/FundamentalsPage';
import './styles/index.css';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="/compare" element={<ComparisonPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/optimization" element={<OptimizationPage />} />
        <Route path="/walkforward" element={<WalkForwardPage />} />
        <Route path="/ml" element={<MLLabPage />} />
        <Route path="/fundamentals" element={<FundamentalsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
