import React from 'react';
import { Activity } from 'lucide-react';
import { ThemeToggle } from '../ui/ThemeToggle';
import { DataSourceSelector } from '../forms/DataSourceSelector';

interface HeaderProps {
  title: string;
  subtitle: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="app-header">
      <div className="app-header-content">
        <div className="header-inner">
          <div className="header-brand">
            <div className="header-icon">
              <Activity size={24} color="white" />
            </div>
            <div>
              <h1 className="header-title">{title}</h1>
              <p className="header-subtitle">{subtitle}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <DataSourceSelector />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
};
