from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO: Add your routers here

app = FastAPI(title="Food Sales Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend running"}
