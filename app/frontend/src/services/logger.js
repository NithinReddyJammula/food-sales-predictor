const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

async function sendLog(level, message, context = {}) {
  // Always log to local console first
  const consoleMsg = `[Frontend Log] [${level.toUpperCase()}] ${message}`;
  if (level === 'error') {
    console.error(consoleMsg, context);
  } else if (level === 'warn' || level === 'warning') {
    console.warn(consoleMsg, context);
  } else {
    console.log(consoleMsg, context);
  }

  try {
    await fetch(`${API_BASE}/logs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level, message, context }),
    });
  } catch (err) {
    // Fail silently in browser to avoid infinite loop logging failures
    console.warn('Failed to send log to backend server:', err);
  }
}

export const logger = {
  info: (msg, ctx) => sendLog('info', msg, ctx),
  warn: (msg, ctx) => sendLog('warn', msg, ctx),
  error: (msg, ctx) => sendLog('error', msg, ctx),
};
