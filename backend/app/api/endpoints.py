from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from app.services.ingestion import IngestionService
from app.services.parsing import ParsingService
from app.services.scoring import ScoringService, FeedbackService, AuditorService
import json
import os
import sys
import asyncio
import subprocess
from datetime import datetime, timedelta
from pydantic import BaseModel

from typing import Optional

class ScrapeRequest(BaseModel):
    keyword: str = "Web Developer"
    location: str = "India"
    max_jobs: int = 10
    resume_id: Optional[int] = None

router = APIRouter(prefix="/api/v1")

# Helper to get the correct base directory in both dev and frozen modes
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Professional standard: store data in Local AppData
        safe_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ATS_Pro_AI')
        os.makedirs(safe_dir, exist_ok=True)
        return safe_dir
    # 3 levels up from backend/app/api/endpoints.py to root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from pydantic import BaseModel

class Constraints(BaseModel):
    can_learn_skills: bool = True
    can_add_projects: bool = True

class AnalysisRequest(BaseModel):
    resume_id: int
    job_description: str
    constraints: Optional[Constraints] = None

@router.post("/analyze")
async def analyze_resume(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Analysis request received for ID: {request.resume_id}")
    # 1. Fetch Resume from DB
    db_resume = db.query(models.Resume).filter(models.Resume.id == request.resume_id).first()
    if not db_resume:
        print(f"DEBUG: Resume with ID {request.resume_id} not found in DB")
        raise HTTPException(status_code=404, detail="Resume not found")
        
    print(f"DEBUG: Resume found: {db_resume.filename}")
    resume_text = db_resume.content
    job_description = request.job_description
    print(f"DEBUG: JD length: {len(job_description) if job_description else 0}")

    
    # Pre-extract features if not already in DB (or just use stored ones)
    skills = db_resume.skills or []
    exp = db_resume.experience_years or 0
    contact = {"email": db_resume.email, "phone": db_resume.phone}
    domain = db_resume.domain or "General"
    seniority = "Mid" # Placeholder if not in DB
    
    # 4. Handle 'Audit Mode' if JD is empty
    if not job_description or not job_description.strip() or job_description.strip().lower() == "general":
        try:
            resume_data = {
                "skills": skills, 
                "experience_years": exp,
                "domain": domain,
                "seniority": seniority,
                "contacts_found": contact["email"] is not None
            }
            constraints = request.constraints.dict() if request.constraints else {"can_learn_skills": True, "can_add_projects": True}
            audit_results = AuditorService.audit(resume_text, resume_data, constraints)
            
            return {
                "mode": "audit",
                "overall_score": audit_results["overall_score"],
                "success_prediction": audit_results["success_prediction"],
                "remedies": audit_results["remedies"],
                "impact_metrics": audit_results["impact_metrics"],
                "verb_strength": audit_results["verb_strength"],
                "keyword_cloud": audit_results["keyword_cloud"],
                "section_health": audit_results["section_health"],
                "domain_prediction": audit_results["domain_prediction"],
                "resume_id": db_resume.id,
                "skills_found": skills,
                "experience_years": exp
            }
        except Exception as e:
            print(f"ERROR: Audit failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


    # 5. Parse Job Description (Standard Matching Mode)
    jd_features = ParsingService.parse_job_description(job_description)
    db_jd = models.JobDescription(
        title="Dynamic Analysis",
        raw_text=job_description,
        extracted_features=jd_features
    )
    db.add(db_jd)
    db.commit()
    db.refresh(db_jd)
    
    # 6. Score & Feedback
    resume_data = {
        "skills": skills, 
        "experience_years": exp,
        "domain": domain,
        "seniority": seniority,
        "contacts_found": contact["email"] is not None
    }
    match_results = ScoringService.calculate_score(resume_data, jd_features, resume_text, job_description)
    feedback = FeedbackService.generate_feedback(match_results)
    
    # 7. Save Result
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
        "mode": "match",
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

@router.delete("/resume/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    # Delete associated file
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception as e:
            print(f"Error deleting file {resume.file_path}: {e}")
            
    # Delete related analysis results
    try:
        db.query(models.AnalysisResult).filter(models.AnalysisResult.resume_id == resume_id).delete()
    except Exception as e:
        print(f"Error deleting related analysis results: {e}")
        
    # Delete resume from db
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}


@router.get("/resume/all/")
async def get_all_resumes(db: Session = Depends(get_db)):
    resumes_db = db.query(models.Resume).order_by(models.Resume.uploaded_at.desc()).all()
    
    resumes = []
    for r in resumes_db:
        filename = r.filename
        # Logic to extract display name from stored filename or use stored one
        display_name = filename
        # If the file_path contains a UUID, we might want to use that for logic, 
        # but the model stores original filename in 'filename'
        
        timestamp_val = 0
        if r.uploaded_at:
            try:
                timestamp_val = r.uploaded_at.timestamp()
            except:
                pass
                
        resumes.append({
            "id": r.id,
            "filename": filename, 
            "display_name": display_name, 
            "file_type": r.file_type or "unknown",
            "domain": r.domain or "Software Engineering",
            "skills": r.skills or [],
            "timestamp": timestamp_val
        })
        
    return {"resumes": resumes}

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    results = db.query(models.AnalysisResult).order_by(models.AnalysisResult.created_at.desc()).limit(10).all()
    return results

@router.get("/jobs")
def get_scraped_jobs(resume_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        # Construct path to master_scraped_jobs.json safely
        base_dir = get_base_dir()
        jobs_file = os.path.join(base_dir, "data", "master_scraped_jobs.json")
        if not os.path.exists(jobs_file):
            return []
            
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            
        cutoff_time = datetime.now() - timedelta(hours=20)
        recent_jobs = []
        
        for j in jobs:
            ts = j.get("timestamp")
            if ts:
                try:
                    job_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if job_time.tzinfo:
                        job_time = job_time.replace(tzinfo=None)
                        
                    if job_time >= cutoff_time:
                        recent_jobs.append(j)
                except ValueError:
                    pass
                    
        updated = False
        if resume_id:
            resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
            if resume:
                resume_data = {
                    "skills": resume.skills or [],
                    "experience_years": resume.experience_years or 0,
                    "domain": resume.domain or "Software Engineering",
                    "seniority": ParsingService.detect_seniority(resume.content) if resume.content else "Junior",
                    "contacts_found": bool(resume.email)
                }
                for job in recent_jobs:
                    if job.get("score", 0) == 0:
                        jd_text = job.get("full_description", "")
                        if jd_text and jd_text != "Description not found":
                            try:
                                jd_features = ParsingService.parse_job_description(jd_text)
                                match_results = ScoringService.calculate_score(resume_data, jd_features, resume.content, jd_text)
                                job["score"] = match_results["overall_score"]
                                updated = True
                            except Exception as ex:
                                print(f"Dynamic scoring error for job: {ex}")
                                
        if updated:
            with open(jobs_file, "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=4, ensure_ascii=False)
                
        return sorted(recent_jobs, key=lambda x: (x.get("score", 0), x.get("timestamp", "")), reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import BackgroundTasks

scraper_is_running = False

import contextlib
from scripts.scraping import main as scraping_main

async def run_scraper_task(keyword: str, location: str, max_jobs: int, base_dir: str, resume_id: Optional[int] = None):
    global scraper_is_running
    scraper_is_running = True
    log_file_path = os.path.join(base_dir, "data", "scraper.log")
    
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        with open(log_file_path, "w", encoding="utf-8", buffering=1) as log_file:
            with contextlib.redirect_stdout(log_file):
                print(f"Starting direct scraping task for {keyword} in {location}...")
                await scraping_main(keyword, location, max_jobs)
                print(f"Direct scraping completed successfully.")
            
            # Post-scraping: Scoring (this logic was already here, let's keep it)
            if resume_id:
                try:
                    with next(get_db()) as db:
                        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
                        if resume:
                            resume_data = {
                                "skills": resume.skills or [],
                                "experience_years": resume.experience_years or 0,
                                "domain": resume.domain or "Software Engineering",
                                "seniority": ParsingService.detect_seniority(resume.content) if resume.content else "Junior",
                                "contacts_found": bool(resume.email)
                            }
                            
                            jobs_file = os.path.join(base_dir, "data", "master_scraped_jobs.json")
                            if os.path.exists(jobs_file):
                                with open(jobs_file, "r", encoding="utf-8") as f:
                                    jobs = json.load(f)
                                    
                                updated = False
                                for job in jobs:
                                    # Only score jobs from this recent batch or jobs that don't have a score yet
                                    # To be comprehensive, we can just score the ones matching keyword/location
                                    if job.get("keyword", "").lower() == keyword.lower() and job.get("location", "").lower() == location.lower():
                                        jd_text = job.get("full_description", "")
                                        if jd_text and jd_text != "Description not found":
                                            jd_features = ParsingService.parse_job_description(jd_text)
                                            match_results = ScoringService.calculate_score(resume_data, jd_features, resume.content, jd_text)
                                            job["score"] = match_results["overall_score"]
                                            updated = True
                                
                                if updated:
                                    with open(jobs_file, "w", encoding="utf-8") as f:
                                        json.dump(jobs, f, indent=4, ensure_ascii=False)
                                    print("Scores updated successfully.")
                except Exception as ex:
                    print(f"Error during post-scraping scoring: {ex}")
    except Exception as e:
        log_file_path = os.path.join(base_dir, "data", "scraper.log")
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\nCRITICAL ERROR: {str(e)}\n")
        print(f"Background scraping error: {str(e)}")
    finally:
        scraper_is_running = False

@router.delete("/jobs/clear")
async def clear_jobs():
    base_dir = get_base_dir()
    file_path = os.path.join(base_dir, "data", "master_scraped_jobs.json")
    log_file = os.path.join(base_dir, "data", "scraper.log")
    
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(log_file):
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Jobs cleared by user.\n")
        
    return {"status": "success", "message": "Scraped jobs and logs cleared"}

@router.get("/scraper/status")
def get_scraper_status():
    global scraper_is_running
    base_dir = get_base_dir()
    log_file_path = os.path.join(base_dir, "data", "scraper.log")
    logs = []
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                logs = [line.strip() for line in lines[-50:]]
        except:
            pass
    return {"is_running": scraper_is_running, "logs": logs}

@router.post("/jobs/scrape")
async def scrape_jobs_endpoint(req: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        base_dir = get_base_dir()
        jobs_file = os.path.join(base_dir, "data", "master_scraped_jobs.json")
        
        # Check cache if data exists
        if os.path.exists(jobs_file):
            with open(jobs_file, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
                
            matched_jobs = [
                j for j in existing_jobs 
                if j.get("keyword", "").lower() == req.keyword.lower() 
                and j.get("location", "").lower() == req.location.lower()
            ]
            
            if matched_jobs:
                latest_job = max(matched_jobs, key=lambda x: x.get("timestamp", "2000-01-01"))
                if "timestamp" in latest_job:
                    last_time = datetime.fromisoformat(latest_job["timestamp"])
                    if datetime.now() - last_time < timedelta(minutes=30):
                        return {"message": "Using cached results (last updated < 30 mins ago).", "cached": True}

        # Trigger background scraping
        background_tasks.add_task(run_scraper_task, req.keyword, req.location, req.max_jobs, base_dir, req.resume_id)
        
        return {"message": "Scraping started in background. Results will be available shortly.", "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
