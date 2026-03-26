import React from 'react';
import { HelpCircle, Lightbulb, Settings } from 'lucide-react';

interface PageFooterProps {
  title: string;
  description: string;
  tips?: string[];
  parameters?: Array<{
    name: string;
    description: string;
  }>;
}

export const PageFooter: React.FC<PageFooterProps> = ({
  title,
  description,
  tips,
  parameters,
}) => {
  return (
    <footer className="page-footer">
      <div className="page-footer-content">
        <div className="page-footer-section">
          <h3 className="page-footer-title">
            <HelpCircle size={16} />
            About {title}
          </h3>
          <p className="page-footer-description">{description}</p>
        </div>

        {parameters && parameters.length > 0 && (
          <div className="page-footer-section">
            <h4 className="page-footer-subtitle">
              <Settings size={14} style={{ display: 'inline', marginRight: '0.25rem', verticalAlign: 'middle' }} />
              Key Parameters
            </h4>
            <dl className="page-footer-params">
              {parameters.map((param) => (
                <div key={param.name}>
                  <dt>{param.name}</dt>
                  <dd>{param.description}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {tips && tips.length > 0 && (
          <div className="page-footer-section">
            <h4 className="page-footer-subtitle">
              <Lightbulb size={14} style={{ display: 'inline', marginRight: '0.25rem', verticalAlign: 'middle' }} />
              Tips
            </h4>
            <ul className="page-footer-tips">
              {tips.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </footer>
  );
};
