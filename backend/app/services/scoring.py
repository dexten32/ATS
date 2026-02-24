from typing import List, Dict, Any
from .matching import SemanticMatchingService
from .parsing import SKILL_GROUPS

class ScoringService:
    @staticmethod
    def calculate_score(resume_data: Dict[str, Any], jd_data: Dict[str, Any], resume_text: str = "", jd_text: str = "") -> Dict[str, Any]:
        # Weights (Maturity-Core Pillar)
        SKILL_WEIGHT = 0.3
        MATURITY_WEIGHT = 0.35 # Core pillar
        SEMANTIC_WEIGHT = 0.2
        EXP_WEIGHT = 0.1
        DS_WEIGHT = 0.05
        
        from .parsing import ParsingService
        
        resume_skills = set(resume_data.get("skills", []))
        mandatory_jd_skills = set(jd_data.get("required_skills", []))
        preferred_jd_skills = set(jd_data.get("preferred_skills", []))
        
        # Extract Maturity Signals from Resume
        resume_maturity = ParsingService.extract_maturity_signals(resume_text)
        jd_maturity = jd_data.get("maturity_requirements", {})
        
        # 1. Skill Match with Depth Multipliers
        matched_skills = []
        missing_mandatory = []
        missing_preferred = []
        alternative_matches = []
        
        # Scale/Optimization signals provide a multiplier
        depth_multiplier = 1.0
        if resume_maturity["scale_signals"]: depth_multiplier += 0.1
        if resume_maturity["optimization_signals"]: depth_multiplier += 0.1
        if resume_maturity["ownership_signals"]: depth_multiplier += 0.05

        for skill in mandatory_jd_skills:
            if skill in resume_skills:
                matched_skills.append(skill)
            else:
                equivalent_found = False
                for group_name, members in SKILL_GROUPS.items():
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

        # Skill Score (Base Presence)
        total_mandatory = len(mandatory_jd_skills)
        if total_mandatory == 0:
            skill_score = 100.0
        else:
            base_skill_score = (len(matched_skills) / (total_mandatory + len(preferred_jd_skills) * 0.5 + 1)) * 100
            skill_score = base_skill_score
            
            if missing_mandatory:
                skill_score *= 0.8 # Penalty

        # 2. Maturity & Depth Analysis (Detail)
        def calc_cluster_score(res_list, jd_list):
            if not jd_list: return 100.0
            matches = [item for item in jd_list if item in res_list]
            return (len(matches) / len(jd_list)) * 100

        arch_score = calc_cluster_score(resume_maturity["architecture_depth"], jd_maturity.get("architecture_depth", []))
        prod_score = calc_cluster_score(resume_maturity["production_ready"], jd_maturity.get("production_ready", []))
        soft_score = calc_cluster_score(resume_maturity["soft_skills"], jd_maturity.get("soft_skills", []))
        fe_score = calc_cluster_score(resume_maturity["frontend_depth"], jd_maturity.get("frontend_depth", []))
        
        # Scale Penalty: If JD has scale signals and resume has ZERO
        scale_penalty = 1.0
        if jd_maturity.get("scale_signals") and not resume_maturity.get("scale_signals"):
            scale_penalty = 0.7 # 30% penalty for missing essential scale
        
        # Ownership Bonus
        ownership_bonus = 1.0
        if resume_maturity.get("ownership_signals"):
            ownership_bonus = 1.1 # 10% boost for ownership signals
            
        # System Thinking Bonus (Architectural Patterns)
        system_thinking_bonus = 1.0
        if resume_maturity.get("architectural_patterns"):
            # Reward diversity of patterns found
            pattern_count = len(resume_maturity["architectural_patterns"])
            system_thinking_bonus = 1.0 + (min(0.2, pattern_count * 0.05)) # Up to 20% boost

        maturity_score = ((arch_score * 0.4) + (prod_score * 0.3) + (soft_score * 0.15) + (fe_score * 0.15)) * \
                         scale_penalty * ownership_bonus * system_thinking_bonus
        maturity_score = min(100, maturity_score)
        resume_exp = resume_data.get("experience_years", 0.0)
        min_exp = jd_data.get("min_experience", 0.0)
        max_exp = jd_data.get("max_experience")
        
        if resume_exp >= min_exp:
            if max_exp and resume_exp > max_exp + 2:
                exp_score = 85.0 # Overqualified
            else:
                exp_score = 100.0
        else:
            # Underqualified is a curve, not linear
            exp_score = (resume_exp / min_exp) ** 1.5 * 100 if min_exp > 0 else 100.0
            
        # 3. Domain & Seniority Alignment
        resume_domain = resume_data.get("domain", "General Tech")
        jd_domain = jd_data.get("domain", "General Tech")
        resume_seniority = resume_data.get("seniority", "Junior")
        expected_seniority = jd_data.get("expected_seniority", "Junior")
        
        domain_match = 100 if resume_domain == jd_domain else 50
        
        seniority_map = {"Junior": 1, "Senior": 2, "Lead": 3}
        res_val = seniority_map.get(resume_seniority, 1)
        exp_val = seniority_map.get(expected_seniority, 1)
        
        if res_val >= exp_val:
            seniority_score = 100 if res_val == exp_val else 90 # Slight penalty for being over-senior
        else:
            seniority_score = 50 # Under-senior
            
        ds_score = (domain_match * 0.4) + (seniority_score * 0.6)

        # 4. Semantic Match (Contextual)
        semantic_score = SemanticMatchingService.get_contextual_similarity(resume_text, jd_text)
        
        # 5. Overall Score (Strategic Weighting)
        overall_score = (skill_score * SKILL_WEIGHT) + (maturity_score * MATURITY_WEIGHT) + \
                        (semantic_score * SEMANTIC_WEIGHT) + (exp_score * EXP_WEIGHT) + (ds_score * DS_WEIGHT)
        
        # 6. Confidence 2.0 (Strategic Trust Factor)
        parsing_trust = 0
        if resume_exp > 0: parsing_trust += 30
        if len(resume_skills) > 5: parsing_trust += 40
        if resume_data.get("contacts_found"): parsing_trust += 30
        
        # Factor 2: Seniority Consistency (Signals vs Level)
        seniority_consistency = 70
        if resume_seniority in ["Senior", "Lead"] and resume_maturity["ownership_signals"]:
            seniority_consistency = 100
        elif resume_seniority == "Junior" and not resume_maturity["architecture_depth"]:
            seniority_consistency = 90
            
        # Factor 3: Domain Density
        domain_certainty = 100 if domain_match == 100 else 60
        
        confidence_val = (parsing_trust * 0.4) + (seniority_consistency * 0.3) + (domain_certainty * 0.3)
        
        if confidence_val > 85: confidence = "High"
        elif confidence_val > 60: confidence = "Medium"
        else: confidence = "Low"
            
        return {
            "overall_score": round(overall_score, 2),
            "skill_score": round(skill_score, 2),
            "experience_score": round(exp_score, 2),
            "semantic_score": round(semantic_score, 2),
            "maturity_score": round(maturity_score, 2),
            "detailed_maturity": {
                "architecture": round(arch_score, 2),
                "production": round(prod_score, 2),
                "soft_skills": round(soft_score, 2),
                "frontend": round(fe_score, 2)
            },
            "domain_seniority_score": round(ds_score, 2),
            "confidence_level": confidence,
            "confidence_value": round(confidence_val, 2),
            "matched_skills": matched_skills,
            "missing_mandatory": missing_mandatory,
            "missing_preferred": missing_preferred,
            "alternative_matches": alternative_matches,
            "resume_exp": resume_exp,
            "min_exp": min_exp,
            "max_exp": max_exp,
            "resume_domain": resume_domain,
            "jd_domain": jd_domain,
            "resume_seniority": resume_seniority,
            "jd_seniority": expected_seniority,
            "resume_maturity": resume_maturity
        }

class FeedbackService:
    @staticmethod
    def generate_feedback(match_results: Dict[str, Any]) -> Dict[str, Any]:
        missing_mandatory = match_results.get("missing_mandatory", [])
        alt_matches = match_results.get("alternative_matches", [])
        resume_exp = match_results.get("resume_exp", 0)
        min_exp = match_results.get("min_exp", 0)
        max_exp = match_results.get("max_exp")
        resume_dom = match_results.get("resume_domain")
        jd_dom = match_results.get("jd_domain")
        res_sen = match_results.get("resume_seniority")
        jd_sen = match_results.get("jd_seniority")
        det_mat = match_results.get("detailed_maturity", {})
        res_mat = match_results.get("resume_maturity", {})
        
        suggestions = []
        
        # 1. Critical Skill Gaps
        if missing_mandatory:
            suggestions.append(f"CRITICAL GAP: Missing mandatory skills: {', '.join(missing_mandatory[:3])}")
        
        # 2. Maturity & Scale Gaps (Growth Path)
        if det_mat.get("architecture", 100) < 50:
            suggestions.append("GROWTH PATH: Add Architecture Depth. The role emphasizes distributed systems/microservices clusters.")
        
        if not res_mat.get("scale_signals"):
            suggestions.append("GROWTH PATH: Add Measurable Scale. No explicit signals for high-traffic or TPS found. Add metrics (e.g., 'scaled to 1M users').")

        if det_mat.get("production", 100) < 50:
            suggestions.append("GROWTH PATH: Add Distributed System Exposure. Highlighting observability (Grafana/ELK) and CI/CD lifecycle is key.")

        if not res_mat.get("ownership_signals"):
            suggestions.append("GROWTH PATH: Show Ownership. Signals for end-to-end lifecycle or stakeholder management are missing.")

        # 4. System Thinking Strengths
        patterns_found = res_mat.get("architectural_patterns", {})
        if patterns_found:
            pattern_list = list(patterns_found.keys())
            suggestions.append(f"SYSTEM THINKING: Strong signals for architectural patterns: {', '.join(pattern_list)}. This demonstrates high-level system design maturity.")

        if det_mat.get("soft_skills", 100) < 40:
            suggestions.append("Communication Gap: JD values client interaction. Highlight your experience bridging technical and business needs.")

        # 3. Experience & alignment
        if resume_exp < min_exp:
            suggestions.append(f"Experience Gap: Role requires {min_exp} years, you have {resume_exp}.")
        
        if res_sen != jd_sen:
            suggestions.append(f"Seniority Mismatch: Role is targeted at {jd_sen} level; you are detected as {res_sen}.")

        for alt in alt_matches[:2]:
            suggestions.append(f"Note: Compensating for missing {alt['required']} with {alt['found']}.")

        return {
            "missing_mandatory": missing_mandatory,
            "suggestions": suggestions,
            "strengths": match_results.get("matched_skills", [])[:5]
        }
