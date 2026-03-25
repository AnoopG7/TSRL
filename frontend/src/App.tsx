import { Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { BacktestPage } from './pages/BacktestPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { WalkForwardPage } from './pages/WalkForwardPage';
import './styles/index.css';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<BacktestPage />} />
        <Route path="/compare" element={<ComparisonPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/optimization" element={<OptimizationPage />} />
        <Route path="/walkforward" element={<WalkForwardPage />} />
      </Route>
    </Routes>
  );
}

export default App;
