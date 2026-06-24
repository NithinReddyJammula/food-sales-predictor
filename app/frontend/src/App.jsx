import { useState, useEffect, useMemo } from 'react';
import './index.css';
import { api } from './services/api.js';
import PredictionsView from './pages/PredictionsView.jsx';
import ComparisonView from './pages/ComparisonView.jsx';
import SimulatorView from './pages/SimulatorView.jsx';

const PREDICTION_SLOTS = [
  { slot: 1, start: '00:00', end: '02:00', label: '12–2 AM' },
  { slot: 2, start: '02:00', end: '04:00', label: '2–4 AM' },
  { slot: 3, start: '04:00', end: '06:00', label: '4–6 AM' },
  { slot: 4, start: '06:00', end: '08:00', label: '6–8 AM' },
  { slot: 5, start: '08:00', end: '10:00', label: '8–10 AM' },
  { slot: 6, start: '10:00', end: '12:00', label: '10–12 PM' },
  { slot: 7, start: '12:00', end: '14:00', label: '12–2 PM' },
  { slot: 8, start: '14:00', end: '16:00', label: '2–4 PM' },
  { slot: 9, start: '16:00', end: '18:00', label: '4–6 PM' },
  { slot: 10, start: '18:00', end: '20:00', label: '6–8 PM' },
  { slot: 11, start: '20:00', end: '22:00', label: '8–10 PM' },
  { slot: 12, start: '22:00', end: '00:00', label: '10–12 AM' },
];

const ITEMS_CONFIG = {
  categories: [
    {
      id: 'item-1', name: 'Wings', icon: '1',
      subtypes: [
        { id: 'item-1a', name: 'Item 1a' },
        { id: 'item-1b', name: 'Item 1b' },
        { id: 'item-1c', name: 'Item 1c' },
      ],
    },
    {
      id: 'item-2', name: 'Pizza', icon: '2',
      subtypes: [
        { id: 'item-2a', name: 'Item 2a' },
        { id: 'item-2b', name: 'Item 2b' },
        { id: 'item-2c', name: 'Item 2c' },
      ],
    },
    {
      id: 'item-3', name: 'Cookies', icon: '3',
      subtypes: [
        { id: 'item-3a', name: 'Item 3a' },
        { id: 'item-3b', name: 'Item 3b' },
        { id: 'item-3c', name: 'Item 3c' },
      ],
    },
    {
      id: 'item-4', name: 'Sandwich', icon: '4',
      subtypes: [
        { id: 'item-4a', name: 'Item 4a' },
        { id: 'item-4b', name: 'Item 4b' },
        { id: 'item-4c', name: 'Item 4c' },
      ],
    },
    {
      id: 'item-5', name: 'Breakfast', icon: '5',
      subtypes: [
        { id: 'item-5a', name: 'Item 5a' },
        { id: 'item-5b', name: 'Item 5b' },
        { id: 'item-5c', name: 'Item 5c' },
      ],
    },
  ],
};

function getCurrentSlot() {
  const hour = new Date().getHours();
  return Math.floor(hour / 2) + 1;
}

function getToday() {
  return new Date().toISOString().split('T')[0];
}

export default function App() {
  const [view, setView] = useState('predictions');
  const [selectedDate, setSelectedDate] = useState(getToday());
  const [selectedSlot, setSelectedSlot] = useState(null); // null = all slots
  const [predictions, setPredictions] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const currentSlot = getCurrentSlot();

  // Fetch predictions
  useEffect(() => {
    if (view !== 'predictions') return;
    setLoading(true);
    setError(null);

    const fetchData = async () => {
      try {
        let data;
        if (selectedSlot) {
          data = await api.getPredictionsBySlot(selectedDate, selectedSlot);
        } else {
          data = await api.getPredictions(selectedDate);
        }
        setPredictions(data);
      } catch (err) {
        console.error('Failed to fetch predictions:', err);
        // Set empty structure so UI works without data
        setPredictions({ slots: {} });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDate, selectedSlot, view]);

  // Fetch comparison
  useEffect(() => {
    if (view !== 'comparison') return;
    setLoading(true);
    setError(null);

    const fetchData = async () => {
      try {
        const data = await api.getComparison(selectedDate);
        setComparison(data);
      } catch (err) {
        console.error('Failed to fetch comparison:', err);
        setComparison([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDate, view]);

  // Stats
  const stats = useMemo(() => {
    if (!predictions || !predictions.slots) return null;
    let totalPredicted = 0;
    let totalItems = 0;
    let activeSlots = 0;

    Object.values(predictions.slots).forEach((slot) => {
      activeSlots++;
      Object.values(slot.items).forEach((item) => {
        totalPredicted += item.totalPredicted;
        totalItems += Object.keys(item.subtypes).length;
      });
    });

    return { totalPredicted, totalItems, activeSlots };
  }, [predictions]);

  return (
    <>
      {/* Navigation Bar */}
      <nav className="navbar" id="main-nav">
        <div className="navbar-inner">
          <div className="navbar-brand">
            <div className="navbar-logo">FS</div>
            <div>
              <div className="navbar-title">Food Forecast</div>
              <div className="navbar-subtitle">Smart Cooking Predictions</div>
            </div>
          </div>

          <div className="navbar-nav">
            <button
              id="nav-predictions"
              className={`nav-btn ${view === 'predictions' ? 'active' : ''}`}
              onClick={() => setView('predictions')}
            >
              📊 Predictions
            </button>
            <button
              id="nav-comparison"
              className={`nav-btn ${view === 'comparison' ? 'active' : ''}`}
              onClick={() => setView('comparison')}
            >
              ⚖️ Forecast vs Actual
            </button>
            <button
              id="nav-simulator"
              className={`nav-btn ${view === 'simulator' ? 'active' : ''}`}
              onClick={() => setView('simulator')}
            >
              🛒 Simulator
            </button>
          </div>

          <div className="date-picker-wrapper">
            <input
              id="date-picker"
              type="date"
              className="date-input"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="app-container">
        {view === 'predictions' && (
          <PredictionsView
            predictions={predictions}
            loading={loading}
            error={error}
            stats={stats}
            selectedDate={selectedDate}
            selectedSlot={selectedSlot}
            setSelectedSlot={setSelectedSlot}
            currentSlot={currentSlot}
            slots={PREDICTION_SLOTS}
            items={ITEMS_CONFIG}
          />
        )}

        {view === 'comparison' && (
          <ComparisonView
            comparison={comparison}
            loading={loading}
            error={error}
            selectedDate={selectedDate}
            items={ITEMS_CONFIG}
          />
        )}

        {view === 'simulator' && (
          <SimulatorView />
        )}
      </main>
    </>
  );
}

