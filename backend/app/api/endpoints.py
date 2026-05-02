from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from app.services.ingestion import IngestionService
from app.services.parsing import ParsingService
from app.services.scoring import ScoringService, FeedbackService
import json

router = APIRouter(prefix="/api/v1")

@router.post("/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Ingestion & Validation
    IngestionService.validate_file(resume_file)
    file_path = IngestionService.save_file(resume_file)
    
    # 2. Extract Text
    resume_text = IngestionService.extract_text(file_path)
    resume_text = IngestionService.sanitize_text(resume_text)
    
    # 3. Parse Resume
    skills = ParsingService.extract_skills(resume_text)
    exp = ParsingService.extract_experience_years(resume_text)
    contact = ParsingService.extract_contact_info(resume_text)
    domain = ParsingService.classify_domain(resume_text)
    seniority = ParsingService.detect_seniority(resume_text)
    
    # Save Resume to DB
    db_resume = models.Resume(
        filename=resume_file.filename,
        file_path=file_path,
        content=resume_text,
        skills=skills,
        experience_years=exp,
        email=contact["email"],
        phone=contact["phone"]
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    # 4. Parse Job Description
    jd_features = ParsingService.parse_job_description(job_description)
    db_jd = models.JobDescription(
        title="Dynamic Analysis",
        raw_text=job_description,
        extracted_features=jd_features
    )
    db.add(db_jd)
    db.commit()
    db.refresh(db_jd)
    
    # 5. Score & Feedback
    resume_data = {
        "skills": skills, 
        "experience_years": exp,
        "domain": domain,
        "seniority": seniority,
        "contacts_found": contact["email"] is not None
    }
    match_results = ScoringService.calculate_score(resume_data, jd_features, resume_text, job_description)
    feedback = FeedbackService.generate_feedback(match_results)
    
    # 6. Save Result
    db_result = models.AnalysisResult(
        resume_id=db_resume.id,
        jd_id=db_jd.id,
        overall_score=match_results["overall_score"],
        skill_score=match_results["skill_score"],
        experience_score=match_results["experience_score"],
        confidence_level=match_results["confidence_level"],
        feedback=feedback,
        metadata_info={"algo_version": "1.1", "semantic_score": match_results["semantic_score"]}
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    return {
        "score": match_results["overall_score"],
        "confidence": match_results["confidence_level"],
        "confidence_value": match_results["confidence_value"],
        "skill_match": match_results["skill_score"],
        "exp_match": match_results["experience_score"],
        "semantic_match": match_results["semantic_score"],
        "domain_seniority_match": match_results["domain_seniority_score"],
        "maturity_match": match_results["maturity_score"],
        "detailed_maturity": match_results["detailed_maturity"],
        "feedback": feedback,
        "resume_id": db_resume.id,
        "analysis_id": db_result.id
    }

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    results = db.query(models.AnalysisResult).order_by(models.AnalysisResult.created_at.desc()).limit(10).all()
    return results

@router.get("/jobs")
def get_scraped_jobs():
    try:
        # Construct path to scraped_jobs.json at the root of the ATS project
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        jobs_file = os.path.join(base_dir, "data", "scraped_jobs.json")
        if not os.path.exists(jobs_file):
            return []
        with open(jobs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
