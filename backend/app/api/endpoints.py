from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from app.services.ingestion import IngestionService
from app.services.parsing import ParsingService
from app.services.scoring import ScoringService, FeedbackService
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
        # Construct path to master_scraped_jobs.json at the root of the ATS project
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

async def run_scraper_task(keyword: str, location: str, max_jobs: int, base_dir: str, resume_id: Optional[int] = None):
    global scraper_is_running
    scraper_is_running = True
    script_path = os.path.join(base_dir, "scripts", "scraping.py")
    log_file_path = os.path.join(base_dir, "data", "scraper.log")
    
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", script_path,
                "--keyword", keyword,
                "--location", location,
                "--max_jobs", str(max_jobs),
                stdout=log_file, stderr=subprocess.STDOUT
            )
            await process.wait()
            
            if process.returncode != 0:
                print(f"Background scraping failed")
            else:
                print(f"Background scraping completed for {keyword} in {location}")
            
            # Post-scraping: Scoring
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
        print(f"Background scraping error: {str(e)}")
    finally:
        scraper_is_running = False

@router.get("/scraper/status")
def get_scraper_status():
    global scraper_is_running
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
