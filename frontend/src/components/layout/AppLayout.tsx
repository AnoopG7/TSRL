import { useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Header } from './Header';
import { useThemeStore } from '../../store/useThemeStore';

export function AppLayout() {
  const { theme } = useThemeStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `app-tab ${isActive ? 'app-tab-active' : ''}`;

  return (
    <div className="app-layout">
      <Header
        title="Trading Strategy Research Lab"
        subtitle="AI-Powered Quantitative Trading Platform"
      />

      {/* Tab Navigation */}
      <div className="app-tabs">
        <div className="app-tabs-inner">
          <NavLink to="/" className={navLinkClass} end>Backtest</NavLink>
          <NavLink to="/compare" className={navLinkClass}>Compare</NavLink>
          <NavLink to="/portfolio" className={navLinkClass}>Portfolio</NavLink>
          <NavLink to="/optimization" className={navLinkClass}>Optimization</NavLink>
          <NavLink to="/walkforward" className={navLinkClass}>Walk-Forward</NavLink>
        </div>
      </div>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
