# Food Sales Predictor 

An interactive React web application and POS simulator for predicting food sales.

## Project Structure

```
food-sales-predictor/
├── app/
│   ├── backend/            # Python FastAPI API (Scaffolding only)
│   │   ├── main.py         # Server entry point
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── config/         # DB configuration
│   └── frontend/           # React (Vite) web app
│       ├── src/
│       │   ├── pages/      # PredictionsView, ComparisonView, SimulatorView
│       │   ├── services/   # API client
│       │   └── data/       # Configs
├── api_contracts.md        # API Contract documentation
```

## Current State

The **Frontend** is fully functional but currently contains no local mock data. It is waiting to be connected to the backend APIs.

The **Backend** contains empty scaffolding (`backend/main.py`) using **Python FastAPI**. It is waiting for the logic to be built out to supply data to the frontend and handle Kafka streams to MySQL.

## Quick Start

### 1. Run the Frontend (React / Vite)
Open a new terminal tab and run:
```bash
cd app/frontend
npm install
VITE_API_URL=http://localhost:5001/api npm run dev -- --port 5173
```
*Note: The UI will load successfully, but the charts will be empty until the backend API is built.*

### 2. Run the Backend (Python FastAPI)
Open a second terminal tab and run:
```bash
cd app/backend
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pydantic

# Run the server
uvicorn main:app --port 5001 --host 0.0.0.0
```

## API Integration

See the [`api_contracts.md`](./api_contracts.md) file in the root of this project for the exact JSON payloads that the React frontend expects the backend to return. 

The frontend expects the backend to run on **Port 5001**.
