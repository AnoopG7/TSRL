import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  kicker: string;
  icon?: LucideIcon;
  title: string;
  lede?: React.ReactNode;
  tone?: 'default' | 'model';
  aside?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ kicker, icon: Icon, title, lede, tone = 'default', aside }) => (
  <header className="page-header">
    <div>
      <div className={`page-kicker ${tone === 'model' ? 'model' : ''}`}>
        {Icon && <Icon size={15} />}
        {kicker}
      </div>
      <h1 className="page-title">{title}</h1>
      {lede && <p className="page-lede">{lede}</p>}
    </div>
    {aside && <div className="page-header-aside">{aside}</div>}
  </header>
);
