from fastapi import FastAPI

from .auth import router as auth_router
from .database import create_tables
from .orders import router as orders_router
from .websocket import router as websocket_router


app = FastAPI(
    title="RealTime Food Ordering System"
)


# =========================
# Create Database Tables
# =========================

create_tables()


# =========================
# Register Routers
# =========================

app.include_router(auth_router)

app.include_router(orders_router)

app.include_router(websocket_router)


# =========================
# Health Check
# =========================

@app.get("/")
async def root():

    return {
        "message": "RealTime Food Ordering System is running"
    }

