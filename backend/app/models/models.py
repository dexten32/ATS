from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    content = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata extracted
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)  # List of skills
    experience_years = Column(Float, nullable=True)
    
    results = relationship("AnalysisResult", back_populates="resume")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    raw_text = Column(Text)
    extracted_features = Column(JSON, nullable=True) # {required_skills: [], min_exp: 0, etc.}
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship("AnalysisResult", back_populates="job_description")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"))
    
    overall_score = Column(Float)
    skill_score = Column(Float)
    experience_score = Column(Float)
    confidence_level = Column(String)
    
    feedback = Column(JSON) # {missing_skills: [], suggestions: [], strengths: []}
    metadata_info = Column(JSON) # {algo_version: "1.0", timestamp: ""}
    
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="results")
    job_description = relationship("JobDescription", back_populates="results")
