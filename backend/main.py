from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.database import engine, Base, get_db
from app.models import models
from app.api.endpoints import router as api_router

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Advanced Resume ATS API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include Router
app.include_router(api_router)

# Serve Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

# Mount root static files and serve index.html automatically
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
