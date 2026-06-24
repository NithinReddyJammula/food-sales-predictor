/**
 * ComparisonView — shows AI predictions vs actual sales comparison.
 */

import { useMemo, useState } from 'react';

export default function ComparisonView({
  comparison,
  loading,
  error,
  selectedDate,
  items,
}) {
  const [filterCategory, setFilterCategory] = useState(null);

  const data = comparison || [];

  const filteredData = filterCategory
    ? data.filter((r) => r.item_type === filterCategory)
    : data;

  // Summary stats — must be called unconditionally (React hooks rule)
  const summary = useMemo(() => {
    if (!data.length) return null;
    const avgAccuracy =
      data.reduce((sum, r) => sum + (r.accuracy_pct || 0), 0) / data.length;
    const totalPredicted = data.reduce((sum, r) => sum + r.predicted_quantity, 0);
    const totalActual = data.reduce((sum, r) => sum + r.actual_quantity, 0);
    const overPredicted = data.filter((r) => r.difference > 0).length;
    const underPredicted = data.filter((r) => r.difference < 0).length;
    const exact = data.filter((r) => r.difference === 0).length;

    return {
      avgAccuracy: avgAccuracy.toFixed(1),
      totalPredicted,
      totalActual,
      overPredicted,
      underPredicted,
      exact,
      total: data.length,
    };
  }, [comparison]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div className="loading-text">Loading comparison data…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <>
      {/* Page Header */}
      <div className="page-header fade-in">
        <div>
          <h1 className="page-title" id="comparison-title">
            Forecast vs <span>Actual</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 4 }}>
            {selectedDate} · {data.length} data points
          </p>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="stats-bar slide-up">
          <div className="stat-card" id="stat-avg-accuracy">
            <div className="stat-label">Avg Accuracy</div>
            <div className="stat-value accent">{summary.avgAccuracy}%</div>
          </div>
          <div className="stat-card" id="stat-total-predicted-comp">
            <div className="stat-label">Total Predicted</div>
            <div className="stat-value">{summary.totalPredicted}</div>
          </div>
          <div className="stat-card" id="stat-total-actual">
            <div className="stat-label">Total Actual</div>
            <div className="stat-value">{summary.totalActual}</div>
          </div>
          <div className="stat-card" id="stat-over-under">
            <div className="stat-label">Over / Under / Exact</div>
            <div className="stat-value" style={{ fontSize: '1.25rem' }}>
              <span className="diff-positive">{summary.overPredicted}</span>
              {' / '}
              <span className="diff-negative">{summary.underPredicted}</span>
              {' / '}
              <span style={{ color: 'var(--text-primary)' }}>{summary.exact}</span>
            </div>
          </div>
        </div>
      )}

      {/* Category Filter */}
      <div className="slot-tabs" id="category-filter-tabs">
        <button
          className={`slot-tab ${filterCategory === null ? 'active' : ''}`}
          onClick={() => setFilterCategory(null)}
        >
          All Items
        </button>
        {items.categories.map((cat) => (
          <button
            key={cat.id}
            className={`slot-tab ${filterCategory === cat.name ? 'active' : ''}`}
            onClick={() => setFilterCategory(cat.name)}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Comparison Table */}
      <div
        className="category-section fade-in"
        style={{ overflow: 'auto', maxHeight: '70vh' }}
      >
        <table className="comparison-table" id="comparison-table">
          <thead>
            <tr>
              <th>Slot</th>
              <th>Item Type</th>
              <th>Subtype</th>
              <th>Predicted</th>
              <th>Actual</th>
              <th>Diff</th>
              <th>Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, idx) => {
              const accuracyClass =
                row.accuracy_pct >= 85
                  ? 'high'
                  : row.accuracy_pct >= 60
                  ? 'medium'
                  : 'low';

              return (
                <tr key={idx}>
                  <td>
                    <span
                      style={{
                        color: 'var(--text-muted)',
                        fontSize: '0.8rem',
                      }}
                    >
                      {row.slot_label || `Slot ${row.prediction_slot}`}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{row.item_type}</td>
                  <td>{row.item_subtype}</td>
                  <td style={{ fontWeight: 700 }}>{row.predicted_quantity}</td>
                  <td style={{ fontWeight: 700 }}>{row.actual_quantity}</td>
                  <td>
                    <span
                      className={
                        row.difference > 0
                          ? 'diff-positive'
                          : row.difference < 0
                          ? 'diff-negative'
                          : ''
                      }
                      style={{ fontWeight: 600 }}
                    >
                      {row.difference > 0 ? '+' : ''}
                      {row.difference}
                    </span>
                  </td>
                  <td>
                    <span className={`accuracy-badge ${accuracyClass}`}>
                      {row.accuracy_pct}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredData.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <p>No comparison data available for this date.</p>
          </div>
        )}
      </div>
    </>
  );
}
