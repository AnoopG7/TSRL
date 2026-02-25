import React from 'react';
import { Activity } from 'lucide-react';
import { ThemeToggle } from '../ui/ThemeToggle';

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
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};
