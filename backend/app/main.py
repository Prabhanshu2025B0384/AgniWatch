from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import health, payments, hotspots, analysis, agent, demo_wallet

app = FastAPI(
    title="AgniWatch API",
    description="Backend for AgniWatch agentic satellite-thermal-intelligence platform",
    version="0.1.0",
)

# CORS configuration
origins = [
    "http://localhost:5173",
]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(payments.router, prefix="/api/payments")
app.include_router(hotspots.router, prefix="/api/hotspots")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(agent.router, prefix="/api/agent")
app.include_router(demo_wallet.router, prefix="/api/demo")

@app.get("/")
def read_root():
    return {"message": "Welcome to AgniWatch API"}
