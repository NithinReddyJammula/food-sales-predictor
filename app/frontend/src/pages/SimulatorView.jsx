/**
 * SimulatorView — POS Sales Simulator for TPC-DS store transactions.
 * Select a store, browse items by category, enter quantities, and submit.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api.js';
import { STORES, FLAT_ITEMS as ITEMS, getItemsByCategory, CATEGORY_COLORS } from '../data/food-data.js';

const CATEGORIES = getItemsByCategory();

export default function SimulatorView() {
  // ── State ──────────────────────────────────────────
  const [selectedStore, setSelectedStore] = useState(STORES[0]?.s_store_sk || '');
  const [expandedCats, setExpandedCats] = useState(CATEGORIES[0] ? { [CATEGORIES[0].category]: true } : {});
  const [quantities, setQuantities] = useState({}); // { item_sk: 'qty string' }
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({ totalTransactions: 0, totalItemsSold: 0, totalRevenue: 0 });
  const [submitting, setSubmitting] = useState({}); // { item_sk: true/false }
  const [successItems, setSuccessItems] = useState({}); // { item_sk: true } for flash
  const [toast, setToast] = useState(null);

  const feedRef = useRef(null);

  // ── Toast ──────────────────────────────────────────
  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2200);
  }, []);

  // ── Toggle category ────────────────────────────────
  const toggleCat = useCallback((cat) => {
    setExpandedCats((p) => ({ ...p, [cat]: !p[cat] }));
  }, []);

  // ── Quantity handler ───────────────────────────────
  const setQty = useCallback((sk, val) => {
    setQuantities((p) => ({ ...p, [sk]: val.replace(/\D/g, '') }));
  }, []);

  // ── Submit transaction ─────────────────────────────
  const handleAdd = useCallback(async (item) => {
    const qty = parseInt(quantities[item.i_item_sk], 10);
    if (!qty || qty <= 0) return;

    setSubmitting((p) => ({ ...p, [item.i_item_sk]: true }));
    const salesPrice = +(item.i_current_price * 0.92).toFixed(2);

    const payload = {
      ss_item_sk: item.i_item_sk,
      ss_store_sk: selectedStore,
      ss_quantity: qty,
      ss_wholesale_cost: item.i_wholesale_cost,
      ss_list_price: item.i_current_price,
      ss_sales_price: salesPrice,
    };

    try {
      const result = await api.submitTransaction(payload);
      const entry = {
        ...result,
        _name: item.i_product_name,
        _cat: item.i_category,
        _cls: item.i_class,
        _time: new Date(),
      };
      setTransactions((p) => [entry, ...p]);
      setStats((p) => ({
        totalTransactions: p.totalTransactions + 1,
        totalItemsSold: p.totalItemsSold + qty,
        totalRevenue: +(p.totalRevenue + (result.ss_ext_sales_price || qty * salesPrice)).toFixed(2),
      }));
      setQuantities((p) => ({ ...p, [item.i_item_sk]: '' }));
      flashSuccess(item.i_item_sk);
      showToast(`✓ ${qty}× ${item.i_product_name} added`);
    } catch {
      showToast(`❌ Failed to add ${item.i_product_name} (API Error)`);
    } finally {
      setSubmitting((p) => ({ ...p, [item.i_item_sk]: false }));
    }
  }, [quantities, selectedStore, transactions.length, showToast]);

  const flashSuccess = (sk) => {
    setSuccessItems((p) => ({ ...p, [sk]: true }));
    setTimeout(() => setSuccessItems((p) => ({ ...p, [sk]: false })), 1200);
  };

  // ── Key handler for quantity input ─────────────────
  const handleKeyDown = (e, item) => {
    if (e.key === 'Enter') handleAdd(item);
  };

  // ── Time ago ───────────────────────────────────────
  const timeAgo = (d) => {
    const s = Math.floor((Date.now() - new Date(d)) / 1000);
    if (s < 10) return 'just now';
    if (s < 60) return `${s}s ago`;
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    return `${Math.floor(s / 3600)}h ago`;
  };

  // Counts per category in this session
  const catCounts = transactions.reduce((acc, t) => {
    if (t._cat) acc[t._cat] = (acc[t._cat] || 0) + (t.ss_quantity || 0);
    return acc;
  }, {});

  // ── Refresh time-ago every 10s ─────────────────────
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  // ── Render ─────────────────────────────────────────
  const selectedStoreObj = STORES.find((s) => s.s_store_sk === selectedStore);

  return (
    <>
      {/* Toast */}
      {toast && (
        <div className="sim-toast sim-toast-show" id="sim-toast">
          {toast}
        </div>
      )}

      {/* Page Header */}
      <div className="page-header fade-in">
        <div>
          <h1 className="page-title" id="simulator-title">
            Sales <span>Simulator</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 4 }}>
            TPC-DS Store Transactions · {new Date().toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Store Selector */}
      <div className="sim-store-selector fade-in" id="store-selector">
        <div className="sim-store-label">
          <span className="sim-store-icon">🏪</span>
          <span>Select Store</span>
        </div>
        <select
          className="sim-store-select"
          id="store-select"
          value={selectedStore}
          onChange={(e) => setSelectedStore(Number(e.target.value))}
        >
          {STORES.map((s) => (
            <option key={s.s_store_sk} value={s.s_store_sk}>
              Store #{s.s_store_sk} — {s.s_store_name} ({s.s_city}, {s.s_state}) [{s.s_store_id}]
            </option>
          ))}
        </select>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar slide-up" id="sim-stats">
        <div className="stat-card">
          <div className="stat-label">Transactions</div>
          <div className="stat-value accent">{stats.totalTransactions}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Items Sold</div>
          <div className="stat-value">{stats.totalItemsSold}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Revenue</div>
          <div className="stat-value accent">
            ${stats.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active Store</div>
          <div className="stat-value" style={{ fontSize: '1.1rem' }}>
            #{selectedStore} · {selectedStoreObj?.s_store_name}
          </div>
        </div>
      </div>

      {/* Category Sections */}
      <div className="categories-grid" id="sim-categories">
        {CATEGORIES.map((catGroup, catIdx) => {
          const isOpen = expandedCats[catGroup.category];
          const count = catCounts[catGroup.category] || 0;

          return (
            <div
              key={catGroup.category}
              className="category-section"
              style={{ '--cat-color': catGroup.color }}
            >
              {/* Category Header */}
              <div
                className="category-header"
                id={`sim-cat-${catGroup.category.toLowerCase()}`}
                onClick={() => toggleCat(catGroup.category)}
              >
                <div className="category-info">
                  <div
                    className="category-icon"
                    style={{ background: catGroup.color }}
                  >
                    {catGroup.icon}
                  </div>
                  <div>
                    <div className="category-name">{catGroup.category}</div>
                    <div className="category-subtitle">
                      {catGroup.items.length} items ·{' '}
                      {new Set(catGroup.items.map((i) => i.i_class)).size} classes
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {count > 0 && (
                    <span
                      className="sim-cat-badge"
                      style={{
                        background: catGroup.color + '25',
                        color: catGroup.color,
                      }}
                    >
                      {count} sold
                    </span>
                  )}
                  <span className="sim-chevron">{isOpen ? '▼' : '▶'}</span>
                </div>
              </div>

              {/* Item Rows */}
              {isOpen && (
                <div className="sim-items-list">
                  {catGroup.items.map((item) => {
                    const isSuccess = successItems[item.i_item_sk];
                    const isLoading = submitting[item.i_item_sk];

                    return (
                      <div
                        key={item.i_item_sk}
                        className={`sim-item-row ${isSuccess ? 'sim-item-success' : ''}`}
                        id={`sim-item-${item.i_item_sk}`}
                      >
                        <div className="sim-item-info">
                          <div className="sim-item-name">{item.i_product_name}</div>
                          <div className="sim-item-meta">
                            {item.i_class} · {item.i_item_id}
                          </div>
                        </div>
                        <div className="sim-item-price">
                          ${item.i_current_price.toFixed(2)}
                        </div>
                        <div className="sim-item-actions">
                          <input
                            type="text"
                            inputMode="numeric"
                            className="sim-qty-input"
                            placeholder="Qty"
                            value={quantities[item.i_item_sk] || ''}
                            onChange={(e) => setQty(item.i_item_sk, e.target.value)}
                            onKeyDown={(e) => handleKeyDown(e, item)}
                            maxLength={4}
                            id={`sim-qty-${item.i_item_sk}`}
                          />
                          <button
                            className={`sim-add-btn ${isSuccess ? 'sim-add-success' : ''} ${isLoading ? 'sim-add-loading' : ''}`}
                            onClick={() => handleAdd(item)}
                            disabled={isLoading}
                            id={`sim-add-${item.i_item_sk}`}
                          >
                            {isSuccess ? '✓' : isLoading ? '…' : '+'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Transaction Feed */}
      <div className="sim-feed-section" id="sim-feed" ref={feedRef}>
        <div className="sim-feed-header">
          <div className="sim-feed-title">📋 Recent Transactions</div>
          <div className="sim-feed-count">{transactions.length} total</div>
        </div>

        {transactions.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px 20px' }}>
            <div className="empty-state-icon">🛒</div>
            <p style={{ marginBottom: 4 }}>No transactions yet</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select a store, enter a quantity, and click + to begin
            </p>
          </div>
        ) : (
          <div className="sim-feed-list">
            {transactions.slice(0, 50).map((txn, idx) => (
              <div
                key={`${txn.ss_ticket_number}-${idx}`}
                className="sim-txn-row sim-txn-slide-in"
                style={{ animationDelay: `${idx * 0.03}s` }}
              >
                <div className="sim-txn-left">
                  <span className="sim-txn-ticket">#{txn.ss_ticket_number}</span>
                  <div>
                    <div className="sim-txn-name">{txn._name}</div>
                    <div className="sim-txn-meta">
                      {txn._cat} · {txn._cls}
                      {txn._offline ? ' · ⚡ offline' : ''}
                    </div>
                  </div>
                </div>
                <div className="sim-txn-right">
                  <span className="sim-txn-qty">×{txn.ss_quantity}</span>
                  <span className="sim-txn-price">
                    ${(txn.ss_ext_sales_price || 0).toFixed(2)}
                  </span>
                  <span className="sim-txn-time">{timeAgo(txn._time)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ height: 48 }} />
    </>
  );
}
