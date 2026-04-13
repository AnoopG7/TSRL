import { ExternalLink } from 'lucide-react';

interface Article {
  headline: string;
  summary: string;
  url: string;
  datetime: string;
  source: string;
  image?: string;
}

interface Props {
  article: Article;
}

export function NewsCard({ article }: Props) {
  const timeAgo = (isoDate: string) => {
    if (!isoDate) return '';
    try {
      const date = new Date(isoDate);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);

      if (diffDays > 7) return date.toLocaleDateString();
      if (diffDays > 0) return `${diffDays}d ago`;
      if (diffHours > 0) return `${diffHours}h ago`;
      return 'Just now';
    } catch {
      return '';
    }
  };

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: 'flex',
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-md)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        textDecoration: 'none',
        color: 'inherit',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
      className="news-card-link"
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-accent-400)';
        (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--color-surface-hover)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-border)';
        (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
      }}
    >
      {/* Thumbnail */}
      {article.image && (
        <div style={{
          width: 80, height: 60, borderRadius: 'var(--radius-sm)',
          overflow: 'hidden', flexShrink: 0,
        }}>
          <img
            src={article.image}
            alt=""
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontWeight: 600, fontSize: '0.875rem', lineHeight: 1.4,
          marginBottom: '4px',
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {article.headline}
        </div>
        {article.summary && (
          <div style={{
            fontSize: '0.8rem', color: 'var(--color-text-secondary)',
            lineHeight: 1.4, marginBottom: '4px',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {article.summary}
          </div>
        )}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)',
          fontSize: '0.75rem', color: 'var(--color-text-tertiary)',
        }}>
          <span>{article.source}</span>
          <span>·</span>
          <span>{timeAgo(article.datetime)}</span>
          <ExternalLink size={10} style={{ marginLeft: 'auto', opacity: 0.5 }} />
        </div>
      </div>
    </a>
  );
}
