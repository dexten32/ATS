from typing import List, Dict, Any, Tuple
from .matching import SemanticMatchingService
from app.core.constants import SKILL_GROUPS
from .parsing import ParsingService

# Weights (Maturity-Core Pillar)
SKILL_WEIGHT = 0.3
MATURITY_WEIGHT = 0.35 # Core pillar
SEMANTIC_WEIGHT = 0.2
EXP_WEIGHT = 0.1
DS_WEIGHT = 0.05

class ScoringService:
    @staticmethod
    def calculate_score(resume_data: Dict[str, Any], jd_data: Dict[str, Any], resume_text: str = "", jd_text: str = "") -> Dict[str, Any]:
        resume_skills = set(resume_data.get("skills", []))
        mandatory_jd_skills = set(jd_data.get("required_skills", []))
        preferred_jd_skills = set(jd_data.get("preferred_skills", []))
        
        resume_maturity = ParsingService.extract_maturity_signals(resume_text)
        jd_maturity = jd_data.get("maturity_requirements", {})
        
        # 1. Skill Match
        skill_score_res = ScoringService._calculate_skill_score(resume_skills, mandatory_jd_skills, preferred_jd_skills)
        
        # 2. Maturity & Depth Analysis
        maturity_score_res = ScoringService._calculate_maturity_score(resume_maturity, jd_maturity)
        
        # 3. Experience Match
        resume_exp = resume_data.get("experience_years", 0.0)
        min_exp = jd_data.get("min_experience", 0.0)
        max_exp = jd_data.get("max_experience")
        exp_score = ScoringService._calculate_experience_score(resume_exp, min_exp, max_exp)
            
        # 4. Domain & Seniority Alignment
        resume_domain = resume_data.get("domain", "General Tech")
        jd_domain = jd_data.get("domain", "General Tech")
        resume_seniority = resume_data.get("seniority", "Junior")
        expected_seniority = jd_data.get("expected_seniority", "Junior")
        ds_score = ScoringService._calculate_domain_seniority_score(resume_domain, jd_domain, resume_seniority, expected_seniority)

        # 5. Semantic Match
        semantic_score = SemanticMatchingService.get_contextual_similarity(resume_text, jd_text)
        
        # 6. Overall Score
        overall_score = (skill_score_res["score"] * SKILL_WEIGHT) + \
                        (maturity_score_res["score"] * MATURITY_WEIGHT) + \
                        (semantic_score * SEMANTIC_WEIGHT) + \
                        (exp_score * EXP_WEIGHT) + \
                        (ds_score * DS_WEIGHT)
        
        # 7. Confidence Score
        confidence_res = ScoringService._calculate_confidence_score(
            resume_exp, len(resume_skills), resume_data.get("contacts_found"),
            resume_seniority, resume_maturity, resume_domain == jd_domain
        )
            
        return {
            "overall_score": round(overall_score, 2),
            "skill_score": round(skill_score_res["score"], 2),
            "experience_score": round(exp_score, 2),
            "semantic_score": round(semantic_score, 2),
            "maturity_score": round(maturity_score_res["score"], 2),
            "detailed_maturity": maturity_score_res["details"],
            "domain_seniority_score": round(ds_score, 2),
            "confidence_level": confidence_res["level"],
            "confidence_value": confidence_res["value"],
            "matched_skills": skill_score_res["matched_skills"],
            "missing_mandatory": skill_score_res["missing_mandatory"],
            "missing_preferred": skill_score_res["missing_preferred"],
            "alternative_matches": skill_score_res["alternative_matches"],
            "resume_exp": resume_exp,
            "min_exp": min_exp,
            "max_exp": max_exp,
            "resume_domain": resume_domain,
            "jd_domain": jd_domain,
            "resume_seniority": resume_seniority,
            "jd_seniority": expected_seniority,
            "resume_maturity": resume_maturity
        }

    @staticmethod
    def _calculate_skill_score(resume_skills: set, mandatory_jd_skills: set, preferred_jd_skills: set) -> Dict[str, Any]:
        matched_skills = []
        missing_mandatory = []
        missing_preferred = []
        alternative_matches = []

        for skill in mandatory_jd_skills:
            if skill in resume_skills:
                matched_skills.append(skill)
            else:
                equivalent_found = False
                for _, members in SKILL_GROUPS.items():
                    if skill in members:
                        found_equivs = [m for m in members if m in resume_skills]
                        if found_equivs:
                            matched_skills.append(skill)
                            alternative_matches.append({"required": skill, "found": found_equivs[0]})
                            equivalent_found = True
                            break
                if not equivalent_found:
                    missing_mandatory.append(skill)
        
        for skill in preferred_jd_skills:
            if skill in resume_skills:
                matched_skills.append(skill)
            else:
                missing_preferred.append(skill)

        total_mandatory = len(mandatory_jd_skills)
        if total_mandatory == 0:
            skill_score = 100.0
        else:
            skill_score = (len(matched_skills) / (total_mandatory + len(preferred_jd_skills) * 0.5 + 1)) * 100
            if missing_mandatory:
                skill_score *= 0.8 # Penalty
                
        return {
            "score": skill_score,
            "matched_skills": matched_skills,
            "missing_mandatory": missing_mandatory,
            "missing_preferred": missing_preferred,
            "alternative_matches": alternative_matches
        }

    @staticmethod
    def _calculate_maturity_score(resume_maturity: Dict[str, Any], jd_maturity: Dict[str, Any]) -> Dict[str, Any]:
        def calc_cluster_score(res_list, jd_list):
            if not jd_list: return 100.0
            matches = [item for item in jd_list if item in res_list]
            return (len(matches) / len(jd_list)) * 100

        arch_score = calc_cluster_score(resume_maturity.get("architecture_depth", []), jd_maturity.get("architecture_depth", []))
        prod_score = calc_cluster_score(resume_maturity.get("production_ready", []), jd_maturity.get("production_ready", []))
        soft_score = calc_cluster_score(resume_maturity.get("soft_skills", []), jd_maturity.get("soft_skills", []))
        fe_score = calc_cluster_score(resume_maturity.get("frontend_depth", []), jd_maturity.get("frontend_depth", []))
        
        scale_penalty = 0.7 if jd_maturity.get("scale_signals") and not resume_maturity.get("scale_signals") else 1.0
        ownership_bonus = 1.1 if resume_maturity.get("ownership_signals") else 1.0
            
        system_thinking_bonus = 1.0
        if resume_maturity.get("architectural_patterns"):
            pattern_count = len(resume_maturity["architectural_patterns"])
            system_thinking_bonus = 1.0 + (min(0.2, pattern_count * 0.05))

        maturity_score = ((arch_score * 0.4) + (prod_score * 0.3) + (soft_score * 0.15) + (fe_score * 0.15)) * \
                         scale_penalty * ownership_bonus * system_thinking_bonus
                         
        return {
            "score": min(100.0, maturity_score),
            "details": {
                "architecture": round(arch_score, 2),
                "production": round(prod_score, 2),
                "soft_skills": round(soft_score, 2),
                "frontend": round(fe_score, 2)
            }
        }

    @staticmethod
    def _calculate_experience_score(resume_exp: float, min_exp: float, max_exp: float) -> float:
        if resume_exp >= min_exp:
            if max_exp and resume_exp > max_exp + 2:
                return 85.0 # Overqualified
            return 100.0
        return (resume_exp / min_exp) ** 1.5 * 100 if min_exp > 0 else 100.0

    @staticmethod
    def _calculate_domain_seniority_score(resume_domain: str, jd_domain: str, resume_seniority: str, expected_seniority: str) -> float:
        domain_match = 100 if resume_domain == jd_domain else 50
        
        seniority_map = {"Junior": 1, "Senior": 2, "Lead": 3}
        res_val = seniority_map.get(resume_seniority, 1)
        exp_val = seniority_map.get(expected_seniority, 1)
        
        if res_val >= exp_val:
            seniority_score = 100 if res_val == exp_val else 90
        else:
            seniority_score = 50
            
        return (domain_match * 0.4) + (seniority_score * 0.6)

    @staticmethod
    def _calculate_confidence_score(resume_exp: float, skill_count: int, contacts_found: bool, resume_seniority: str, resume_maturity: Dict[str, Any], is_domain_match: bool) -> Dict[str, Any]:
        parsing_trust = 0
        if resume_exp > 0: parsing_trust += 30
        if skill_count > 5: parsing_trust += 40
        if contacts_found: parsing_trust += 30
        
        seniority_consistency = 70
        if resume_seniority in ["Senior", "Lead"] and resume_maturity.get("ownership_signals"):
            seniority_consistency = 100
        elif resume_seniority == "Junior" and not resume_maturity.get("architecture_depth"):
            seniority_consistency = 90
            
        domain_certainty = 100 if is_domain_match else 60
        confidence_val = (parsing_trust * 0.4) + (seniority_consistency * 0.3) + (domain_certainty * 0.3)
        
        if confidence_val > 85: confidence = "High"
        elif confidence_val > 60: confidence = "Medium"
        else: confidence = "Low"
        
        return {"level": confidence, "value": round(confidence_val, 2)}


class FeedbackService:
    @staticmethod
    def generate_feedback(match_results: Dict[str, Any]) -> Dict[str, Any]:
        missing_mandatory = match_results.get("missing_mandatory", [])
        alt_matches = match_results.get("alternative_matches", [])
        resume_exp = match_results.get("resume_exp", 0)
        min_exp = match_results.get("min_exp", 0)
        resume_dom = match_results.get("resume_domain")
        jd_dom = match_results.get("jd_domain")
        res_sen = match_results.get("resume_seniority")
        jd_sen = match_results.get("jd_seniority")
        det_mat = match_results.get("detailed_maturity", {})
        res_mat = match_results.get("resume_maturity", {})
        
        resume_updates = []
        missing_requirements = []
        misalignment = []
        
        if missing_mandatory:
            missing_requirements.append(f"Missing mandatory technical skills: {', '.join(missing_mandatory)}")
        
        if resume_exp < min_exp:
            missing_requirements.append(f"Experience Gap: Role requires {min_exp} years, you have {resume_exp} detected.")

        if det_mat.get("architecture", 100) < 50:
            resume_updates.append("Add Architecture Depth: Highlight experience with distributed systems or microservices clusters.")
        
        if not res_mat.get("scale_signals"):
            resume_updates.append("Include Scale Metrics: Add specific numbers (e.g., 'scaled to 1M users', '10k requests/sec') to demonstrate high-traffic handle.")

        if det_mat.get("production", 100) < 50:
            resume_updates.append("Enhance Production Readiness: Highlight observability (Grafana/ELK), CI/CD flow, and automated testing.")

        if not res_mat.get("ownership_signals"):
            resume_updates.append("Demonstrate Ownership: Mention end-to-end lifecycle management or driving technical roadmaps.")

        if det_mat.get("soft_skills", 100) < 40:
            resume_updates.append("Highlight Collaboration: Add instances of stakeholder management or bridging technical/business gaps.")

        for alt in alt_matches[:2]:
            resume_updates.append(f"Keyword Optimization: You have {alt['found']} which compensates for {alt['required']}. Consider adding {alt['required']} explicitly if applicable.")

        if res_sen != jd_sen:
            misalignment.append(f"Seniority Mismatch: Role targets {jd_sen} level; your profile aligns closer to {res_sen}.")

        if resume_dom != jd_dom and jd_dom != "General Tech":
            misalignment.append(f"Domain Focus: Role is in {jd_dom}, while your background is primarily in {resume_dom}.")

        return {
            "resume_updates": resume_updates,
            "missing_requirements": missing_requirements,
            "misalignment": misalignment,
            "strengths": match_results.get("matched_skills", [])[:5]
        }
