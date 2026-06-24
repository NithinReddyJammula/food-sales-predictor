/**
 * PredictionsView — main dashboard showing AI predictions
 * categorized by item type and subtypes for each 2-hour time slot.
 */

export default function PredictionsView({
  predictions,
  loading,
  error,
  stats,
  selectedDate,
  selectedSlot,
  setSelectedSlot,
  currentSlot,
  slots,
  items,
}) {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div className="loading-text">Loading predictions…</div>
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

  const slotData = predictions?.slots || {};

  // Get items for the currently selected slot (or aggregate all)
  const displaySlots = selectedSlot
    ? { [selectedSlot]: slotData[selectedSlot] }
    : slotData;

  return (
    <>
      {/* Page Header */}
      <div className="page-header fade-in">
        <div>
          <h1 className="page-title" id="predictions-title">
            Today's <span>Predictions</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 4 }}>
            {selectedDate} · {selectedSlot ? `Slot ${selectedSlot}` : 'All Slots'} ·
            Model: {predictions?.modelVersion || '—'}
          </p>
        </div>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="stats-bar slide-up">
          <div className="stat-card" id="stat-total-predicted">
            <div className="stat-label">Total Predicted</div>
            <div className="stat-value accent">{stats.totalPredicted}</div>
          </div>
          <div className="stat-card" id="stat-active-slots">
            <div className="stat-label">Active Slots</div>
            <div className="stat-value">{stats.activeSlots}</div>
          </div>
          <div className="stat-card" id="stat-item-count">
            <div className="stat-label">Item Predictions</div>
            <div className="stat-value">{stats.totalItems}</div>
          </div>
          <div className="stat-card" id="stat-current-slot">
            <div className="stat-label">Current Slot</div>
            <div className="stat-value accent">
              {slots.find((s) => s.slot === currentSlot)?.label || '—'}
            </div>
          </div>
        </div>
      )}

      {/* Slot Tabs */}
      <div className="slot-tabs" id="slot-tabs">
        <button
          className={`slot-tab ${selectedSlot === null ? 'active' : ''}`}
          onClick={() => setSelectedSlot(null)}
        >
          All Slots
        </button>
        {slots.map((s) => (
          <button
            key={s.slot}
            id={`slot-tab-${s.slot}`}
            className={`slot-tab ${selectedSlot === s.slot ? 'active' : ''} ${
              s.slot === currentSlot ? 'current' : ''
            }`}
            onClick={() => setSelectedSlot(s.slot)}
          >
            {s.label}
            {s.slot === currentSlot && ' ●'}
          </button>
        ))}
      </div>

      {/* Category Sections */}
      <div className="categories-grid" id="categories-grid">
        {Object.entries(displaySlots).map(([slotNum, slotInfo]) => {
          if (!slotInfo) return null;
          const slotLabel = slots.find((s) => s.slot === parseInt(slotNum))?.label || `Slot ${slotNum}`;

          return (
            <div key={slotNum}>
              {!selectedSlot && (
                <h2
                  style={{
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: 12,
                    marginTop: 8,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      display: 'inline-block',
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background:
                        parseInt(slotNum) === currentSlot
                          ? 'var(--accent-primary)'
                          : 'var(--text-muted)',
                      boxShadow:
                        parseInt(slotNum) === currentSlot
                          ? '0 0 12px var(--accent-primary-glow)'
                          : 'none',
                    }}
                  />
                  {slotLabel}
                  {parseInt(slotNum) === currentSlot && (
                    <span
                      style={{
                        fontSize: '0.7rem',
                        background: 'var(--accent-primary)',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontWeight: 700,
                      }}
                    >
                      NOW
                    </span>
                  )}
                </h2>
              )}

              {items.categories.map((category, catIdx) => {
                const catData = slotInfo.items?.[category.id];
                if (!catData) return null;

                return (
                  <div
                    key={`${slotNum}-${category.id}`}
                    className="category-section"
                    id={`category-${category.id}-slot-${slotNum}`}
                  >
                    <div className="category-header">
                      <div className="category-info">
                        <div className={`category-icon cat-${catIdx + 1}`}>
                          {category.icon || (catIdx + 1)}
                        </div>
                        <div>
                          <div className="category-name">{category.name}</div>
                          <div className="category-subtitle">
                            {category.subtypes.length} subtypes ·{' '}
                            {selectedSlot ? slotLabel : `Slot ${slotNum}`}
                          </div>
                        </div>
                      </div>
                      <div className="category-total">
                        <div className="category-total-label">Total to Cook</div>
                        <div className="category-total-value">
                          {catData.totalPredicted}
                        </div>
                      </div>
                    </div>

                    <div className="subtypes-grid">
                      {category.subtypes.map((subtype, stIdx) => {
                        const stData = catData.subtypes?.[subtype.id];
                        const dotClass = ['a', 'b', 'c'][stIdx % 3];

                        return (
                          <div
                            key={subtype.id}
                            className="subtype-card"
                            id={`subtype-${subtype.id}-slot-${slotNum}`}
                          >
                            <div className="subtype-info">
                              <div className={`subtype-dot ${dotClass}`} />
                              <div className="subtype-name">{subtype.name}</div>
                            </div>
                            <div className="subtype-prediction">
                              <div className="prediction-count">
                                {stData?.predictedQuantity ?? '—'}
                              </div>
                              <div className="prediction-label">units</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </>
  );
}
