import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.monitoring import Observability
from routers import logs

# Initialize Observability (which configures OpenTelemetry exporters if endpoint is set)
Observability.initialize()

app = FastAPI(title="Food Sales Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(logs.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend running"}

@app.on_event("shutdown")
def shutdown_event():
    Observability.shutdown()
