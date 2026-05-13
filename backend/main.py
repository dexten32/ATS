from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from datetime import datetime
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
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8001", "http://127.0.0.1:8001", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/upload-resume")
async def upload_resume_only_main(
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from app.services.ingestion import IngestionService
    from app.services.parsing import ParsingService
    import os
    
    # 1. Validate
    ext = IngestionService.validate_file(resume_file)
    
    file_path = None
    try:
        # 2. Save File to System
        file_path = IngestionService.save_file(resume_file)
        
        # 3. Extract and Parse
        resume_text = IngestionService.extract_text(file_path)
        resume_text = IngestionService.sanitize_text(resume_text)
        
        skills = ParsingService.extract_skills(resume_text)
        domain = ParsingService.classify_domain(resume_text)
        contact = ParsingService.extract_contact_info(resume_text)
        exp = ParsingService.extract_experience_years(resume_text)
        
        # 4. Save to Database (Transaction)
        db_resume = models.Resume(
            filename=resume_file.filename,
            file_type=ext.replace(".", ""),
            file_path=file_path,
            content=resume_text,
            skills=skills,
            domain=domain,
            email=contact["email"],
            phone=contact["phone"],
            experience_years=exp
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return {
            "message": "Resume successfully uploaded, parsed, and recorded", 
            "filename": resume_file.filename, 
            "file_type": db_resume.file_type,
            "domain": db_resume.domain,
            "skills_count": len(skills),
            "timestamp": db_resume.uploaded_at.isoformat() if db_resume.uploaded_at else datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Rollback logic: if anything fails, delete the file if it was created
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

# Include Router
app.include_router(api_router)

# Serve Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

# Mount root static files and serve index.html automatically
# Mount root static files
app.mount("/static", StaticFiles(directory=frontend_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
