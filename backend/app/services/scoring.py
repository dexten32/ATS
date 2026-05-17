import re
import sys
import os
import pickle
from typing import Dict, Any, List
from app.services.parsing import ParsingService
from app.services.matching import SemanticMatchingService
from app.core.constants import POWER_VERBS, WEAK_VERBS, INDUSTRY_DOMAINS
from app.services.scorer.career_scorer import CareerScorer
from app.services.scorer.depth_scorer import DepthScorer
from app.services.scorer.foundation_scorer import FoundationScorer
from app.services.scorer.penalty_engine import PenaltyEngine

class AuditorService:
    @staticmethod
    def audit(text: str, resume_data: Dict[str, Any] = None) -> Dict[str, Any]:
        text_lower = text.lower()
        word_count = len(text.split())
        
        # 1. Parsing & Extraction
        struct = ParsingService.check_employment_structure(text)
        exp_data = ParsingService.extract_experience_years(text)
        exp_years = resume_data.get("experience_years") if resume_data and resume_data.get("experience_years") is not None else exp_data["total_years"]
        power_verbs_count = sum(1 for v in POWER_VERBS if v.lower() in text_lower)
        
        # 2. Section Detection
        has_contact = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+|\d{10}', text_lower))
        has_exp = bool(re.search(r'experience|employment|work\s+experience|professional\s+experience|career\s+history', text_lower))
        has_edu = bool(re.search(r'education|university|college|degree', text_lower))
        has_skills = bool(re.search(r'skills|technologies|tools', text_lower))
        has_proj = bool(re.search(r'project|portfolio|github', text_lower))
        has_cert = bool(re.search(r'certification|certified', text_lower))
        
        sections_found = sum([has_exp, has_edu, has_skills, has_proj, has_cert])
        completeness_penalty = max(0, (4 - sections_found) * 10)

        # 3. Component Scoring (Delegated to Sub-Services)
        career_res = CareerScorer.calculate_career_score(exp_years, text_lower, struct["confidence"], power_verbs_count)
        career_points = career_res["score"]
        
        depth_res = DepthScorer.calculate_technical_depth(text_lower, power_verbs_count)
        depth_points = depth_res["total_depth"]
        
        foundation_points = FoundationScorer.calculate_foundation(text_lower, has_edu, has_cert)
        
        # 4. Global Logic & Penalties
        base_score = (career_points * 0.4) + (foundation_points * 0.2) + (depth_points * 0.4)
        
        penalties_res = PenaltyEngine.calculate_penalties(text_lower, exp_years, depth_res["tool_hits"], word_count)
        total_inflation_penalty = penalties_res["inflation"]
        
        raw_score = PenaltyEngine.apply_graduated_multipliers(base_score, power_verbs_count)
        
        overall_score = raw_score - completeness_penalty - total_inflation_penalty
        
        # Experience Lift (Gated by Confidence)
        if struct["confidence"] == "HIGH":
            high_tier = any(k in text_lower for k in ["oracle 19c", "data guard", "rman", "asm", "rac"])
            final_exp = exp_years + (1.0 if high_tier else 0)
            exp_lift = min(10, (final_exp - 2) * 2) if final_exp > 2 else 0
            overall_score += exp_lift
        else:
            final_exp = exp_years
            
        overall_score = PenaltyEngine.apply_junior_cap(overall_score, final_exp, depth_res["tool_hits"])
        overall_score = max(0, min(100, overall_score))

        # 5. Strategic Remedies
        remedies = AuditorService._generate_remedies(exp_years, struct["confidence"], depth_points, has_exp, has_proj, has_edu, completeness_penalty)

        # 6. Success Prediction (Legacy/ML Integration)
        success_data = AuditorService._predict_success_fallback(overall_score)
        
        return {
            "mode": "audit",
            "overall_score": round(overall_score, 2),
            "career_evidence": career_points,
            "foundation_strength": foundation_points,
            "technical_depth": round(depth_points, 2),
            "penalties_applied": round(completeness_penalty + total_inflation_penalty, 2),
            "remedies": remedies[:3],
            "credibility_level": success_data["prediction"],
            "credibility_value": round(overall_score * 0.85, 2),
            "impact_metrics": depth_res["impact_score"] * 4,
            "verb_strength": min(100, (power_verbs_count * 10)),
            "keyword_cloud": [t.title() for t in depth_res["verified_tools"][:10]],
            "section_health": {k: ("Pass" if v else "Fail") for k, v in {"Contact": has_contact, "Exp": has_exp, "Edu": has_edu}.items()},
            "domain_prediction": resume_data.get("domain", "General Tech") if resume_data else "General Tech",
            "experience_intervals": exp_data.get("intervals", [])
        }

    @staticmethod
    def _generate_remedies(exp_years, confidence, depth_points, has_exp, has_proj, has_edu, completeness_penalty):
        remedies = []
        if not has_exp and not has_proj:
            remedies.append({"type": "Critical Gap", "text": "Career Evidence Missing: Add either professional experience or personal projects.", "impact": "+40%"})
        if confidence == "LOW" and exp_years > 0:
            remedies.append({"type": "Credibility", "text": "Low Confidence Extraction: Work experience structure is unclear. Use standard chronology.", "impact": "+15%"})
        if exp_years < 2:
            remedies.append({"type": "Seniority Boost", "text": "Junior Capping Active: Explicitly highlight 'Lead' ownership in projects.", "impact": "+15%"})
        if depth_points < 60:
            remedies.append({"type": "Technical Depth", "text": "Thin Tech Stack: Add specific versions and architecture details.", "impact": "+20%"})
        if not has_edu and exp_years < 3:
            remedies.append({"type": "Foundation", "text": "Academic Gap: Education section is mandatory for juniors.", "impact": "+20%"})
        if completeness_penalty > 0:
            remedies.append({"type": "Formatting", "text": "Profile Hygiene: Fix missing sections and contact info.", "impact": "+25%"})
        if not remedies:
            remedies.append({"type": "Optimization", "text": "Elite Tier: Focus on 'Impact Metrics' to reach 95%+.", "impact": "+5%"})
        return remedies

    @staticmethod
    def _predict_success_fallback(overall_score):
        # Placeholder for ML model integration
        return {"prediction": round(overall_score * 0.9, 1)}
