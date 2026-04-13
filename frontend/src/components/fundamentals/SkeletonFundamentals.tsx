export function SkeletonFundamentals() {
  return (
    <div className="animate-fadeIn">
      {/* Title block */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-content" style={{ padding: 'var(--spacing-lg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="skeleton" style={{ height: '32px', width: '200px', marginBottom: '8px', borderRadius: '4px' }} />
              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="skeleton" style={{ height: '20px', width: '120px', borderRadius: '4px' }} />
                <div className="skeleton" style={{ height: '20px', width: '150px', borderRadius: '4px' }} />
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="skeleton" style={{ height: '40px', width: '120px', marginBottom: '8px', borderRadius: '4px' }} />
              <div className="skeleton" style={{ height: '20px', width: '80px', borderRadius: '4px', marginLeft: 'auto' }} />
            </div>
          </div>
        </div>
      </section>

      {/* Tabs */}
      <div className="tab-nav" style={{ marginBottom: 'var(--spacing-lg)' }}>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="skeleton" style={{ height: '36px', width: '100px', borderRadius: 'var(--radius-md)' }} />
        ))}
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
        <div className="skeleton" style={{ height: '300px', borderRadius: 'var(--radius-lg)' }} />
        <div className="skeleton" style={{ height: '300px', borderRadius: 'var(--radius-lg)' }} />
      </div>
      
      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton" style={{ height: '100px', borderRadius: 'var(--radius-lg)' }} />
        ))}
      </div>
    </div>
  );
}
