import { useEffect, useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  Activity, LayoutGrid, FlaskConical, GitCompareArrows, PieChart,
  SlidersHorizontal, Footprints, BrainCircuit, Building2, Menu, X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useThemeStore } from '../../store/useThemeStore';
import { MarketSelector } from '../ui/MarketSelector';
import { ThemeToggle } from '../ui/ThemeToggle';
import { DataSourceSelector } from '../forms/DataSourceSelector';
import { ApiStatus } from '../ui/ApiStatus';

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  tag?: string;
}

const NAV: { group: string; items: NavItem[] }[] = [
  {
    group: 'Start',
    items: [{ to: '/', label: 'Overview', icon: LayoutGrid }],
  },
  {
    group: 'Research',
    items: [
      { to: '/backtest', label: 'Backtest', icon: FlaskConical },
      { to: '/compare', label: 'Compare strategies', icon: GitCompareArrows },
      { to: '/portfolio', label: 'Portfolio', icon: PieChart },
    ],
  },
  {
    group: 'Validate',
    items: [
      { to: '/optimization', label: 'Optimize parameters', icon: SlidersHorizontal },
      { to: '/walkforward', label: 'Walk-forward', icon: Footprints },
    ],
  },
  {
    group: 'Models',
    items: [{ to: '/ml', label: 'ML Lab', icon: BrainCircuit, tag: 'ML' }],
  },
  {
    group: 'Markets',
    items: [{ to: '/fundamentals', label: 'Fundamentals', icon: Building2 }],
  },
];

const ALL_ITEMS = NAV.flatMap((g) => g.items.map((i) => ({ ...i, group: g.group })));

export function AppLayout() {
  const { theme } = useThemeStore();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  const current = ALL_ITEMS.find((i) =>
    i.to === '/' ? location.pathname === '/' : location.pathname.startsWith(i.to),
  );

  useEffect(() => {
    document.title = current && current.to !== '/'
      ? `${current.label} · TSRL`
      : 'TSRL · Trading Strategy Research Lab';
  }, [current]);

  return (
    <div className="shell">
      <aside className={`sidebar ${navOpen ? 'open' : ''}`} aria-label="Primary">
        <NavLink to="/" className="brand" aria-label="TSRL home" onClick={() => setNavOpen(false)}>
          <span className="brand-mark"><Activity size={19} strokeWidth={2.4} /></span>
          <span>
            <span className="brand-name">TSRL</span>
            <span className="brand-sub">Trading Strategy Research Lab</span>
          </span>
        </NavLink>

        <nav className="nav">
          {NAV.map((g) => (
            <div className="nav-group" key={g.group}>
              <span className="nav-group-label">{g.group}</span>
              {g.items.map(({ to, label, icon: Icon, tag }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  onClick={() => setNavOpen(false)}
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon size={17} />
                  {label}
                  {tag && <span className="nav-tag">{tag}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-foot">
          Market data from Yahoo Finance, NSE, Alpha Vantage,{' '}
          <a href="https://financialmodelingprep.com/" target="_blank" rel="noopener noreferrer">FMP</a> and{' '}
          <a href="https://finnhub.io/" target="_blank" rel="noopener noreferrer">Finnhub</a>.
          Research tool, not financial advice.
        </div>
      </aside>
      {navOpen && <div className="scrim" onClick={() => setNavOpen(false)} aria-hidden />}

      <div className="main-col">
        <header className="topbar">
          <button
            className="icon-btn menu-btn"
            onClick={() => setNavOpen((o) => !o)}
            aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
          >
            {navOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="topbar-title">
            {current && current.to !== '/' ? (
              <><span className="hide-sm">{current.group}</span><span className="hide-sm" aria-hidden>/</span><strong>{current.label}</strong></>
            ) : (
              <strong>Overview</strong>
            )}
          </div>
          <div className="topbar-actions">
            <span className="hide-sm"><ApiStatus /></span>
            <MarketSelector />
            <span className="hide-sm"><DataSourceSelector /></span>
            <ThemeToggle />
          </div>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
