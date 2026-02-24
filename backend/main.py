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

# Configure CORS (still useful for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(api_router)

# Serve Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Backend is running, but index.html not found", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
