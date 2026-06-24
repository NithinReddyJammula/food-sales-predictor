import.meta.env.VITE_API_URL = undefined;
/**
 * API Service — handles all backend communication.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

async function request(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Unknown error');
  return data.data;
}

async function post(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Unknown error');
  return data.data;
}

export const api = {
  // Items
  getItems: () => request('/items'),

  // Predictions
  getPredictionsToday: () => request('/predictions/today'),
  getPredictions: (date) => request(`/predictions/${date}`),
  getPredictionsBySlot: (date, slot) => request(`/predictions/${date}/${slot}`),
  getCategoryPredictions: (categoryId, date) =>
    request(`/items/${categoryId}/predictions?date=${date}`),
  uploadPredictions: (predictions) =>
    post('/predictions/upload', { predictions }),

  // Comparisons
  getComparison: (date) => request(`/comparison/${date}`),
  getMonthlyComparison: (month) => request(`/comparison/monthly/${month}`),

  // Actuals
  getActuals: (date) => request(`/actuals/${date}`),

  // Health
  health: () => request('/health'),

  // Simulator
  submitTransaction: (txn) => post('/simulator/transactions', txn),
  getTransactions: () => request('/simulator/transactions'),
  getTransactionStats: () => request('/simulator/stats'),
  clearTransactions: () => {
    return fetch(`${API_BASE}/simulator/transactions`, { method: 'DELETE' })
      .then(r => r.json())
      .then(d => d.data);
  },
};
