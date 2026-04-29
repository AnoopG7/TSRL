import { useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Header } from './Header';
import { useThemeStore } from '../../store/useThemeStore';
import { MarketSelector } from '../ui/MarketSelector';

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

      {/* Tab Navigation Grouped */}
      <div className="app-tabs">
        <div className="app-tabs-inner" style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', borderRight: '1px solid var(--color-border)', paddingRight: 'var(--spacing-md)' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginRight: 'var(--spacing-sm)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quant
            </span>
            <NavLink to="/" className={navLinkClass} end>Backtest</NavLink>
            <NavLink to="/compare" className={navLinkClass}>Compare</NavLink>
            <NavLink to="/portfolio" className={navLinkClass}>Portfolio</NavLink>
            <NavLink to="/optimization" className={navLinkClass}>Optimization</NavLink>
            <NavLink to="/walkforward" className={navLinkClass}>Walk-Forward</NavLink>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginRight: 'var(--spacing-sm)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Research
              </span>
              <NavLink to="/fundamentals" className={navLinkClass}>Fundamentals</NavLink>
            </div>
            <MarketSelector />
          </div>
        </div>
      </div>

      <main className="app-main" style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 120px)' }}>
        <div style={{ flex: 1 }}>
          <Outlet />
        </div>
        
        {/* Attribution Footer */}
        <footer style={{ 
          marginTop: 'auto', 
          paddingTop: 'var(--spacing-xl)', 
          paddingBottom: 'var(--spacing-md)',
          textAlign: 'center', 
          fontSize: '0.75rem', 
          color: 'var(--color-text-muted)' 
        }}>
          Trading Strategy Research Lab © {new Date().getFullYear()}
          <div style={{ marginTop: '4px' }}>
            Data provided by <a href="https://financialmodelingprep.com/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Financial Modeling Prep</a>, <a href="https://finnhub.io/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Finnhub</a>, and Yahoo Finance. 
            Not intended as financial advice.
          </div>
        </footer>
      </main>
    </div>
  );
}
