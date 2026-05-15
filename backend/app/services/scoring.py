from typing import List, Dict, Any, Tuple
from .matching import SemanticMatchingService
from app.core.constants import SKILL_GROUPS, POWER_VERBS, WEAK_VERBS, INDUSTRY_DOMAINS
from .parsing import ParsingService
import os
import pickle
import sys
import re
from collections import Counter

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

    @staticmethod
    def predict_success(resume_data: Dict[str, Any], text: str) -> Dict[str, Any]:
        try:
            # Get paths (Universal support for dev and PyInstaller)
            if getattr(sys, 'frozen', False):
                base_dir = os.path.join(getattr(sys, '_MEIPASS'), "backend", "app")
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            model_path = os.path.join(base_dir, "core", "success_model.pkl")
            bench_path = os.path.join(base_dir, "core", "market_intelligence.pkl")
            
            if not os.path.exists(model_path):
                return {"prediction": 50.0, "benchmarks": None}

            # 1. Prepare Features for Prediction
            # Features: [exp_years, hard_skills, soft_skills, salary, domain_id]
            exp_years = resume_data.get("experience_years", 0.0)
            skills = resume_data.get("skills", [])
            hard_skills_count = len(skills) # Approximation
            soft_skills_count = 5 # Default
            salary = 0.0 # Default if unknown
            
            # Domain ID mapping
            domain_name = resume_data.get("domain", "General")
            domain_id = 0
            for i, d in enumerate(INDUSTRY_DOMAINS.keys()):
                if d == domain_name:
                    domain_id = i + 1
                    break
            
            features = [[exp_years, hard_skills_count, soft_skills_count, salary, domain_id]]
            
            # 2. Predict
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
                # LinearSVC doesn't have predict_proba by default, but RandomForest does
                # Since I used RandomForest in big_data_trainer, we can get probability
                proba = model.predict_proba(features)[0][1] # Probability of "Invitation"
                prediction_score = round(proba * 100, 2)
            
            # 3. Get Benchmarks
            benchmarks = None
            if os.path.exists(bench_path):
                with open(bench_path, "rb") as f:
                    intel_data = pickle.load(f)
                    all_benchmarks = intel_data["benchmarks"]
                    benchmarks = all_benchmarks.get(domain_name, all_benchmarks.get("General"))

            return {
                "prediction": prediction_score,
                "benchmarks": benchmarks
            }
        except Exception as e:
            print(f"Success Prediction failed: {str(e)}")
            return {"prediction": 50.0, "benchmarks": None}


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


import re
from collections import Counter
from app.core.constants import POWER_VERBS, WEAK_VERBS, INDUSTRY_DOMAINS

class AuditorService:
    @staticmethod
    def audit(text: str, resume_data: Dict[str, Any] = None, constraints: Dict[str, bool] = None) -> Dict[str, Any]:
        if constraints is None:
            constraints = {"can_learn_skills": True, "can_add_projects": True}
            
        text_lower = text.lower()
        
        # 1. Impact Score (Metrics/Numbers)
        all_nums = re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?(?:[kmbt])?\b|\b\d{2,}\b', text)
        
        metrics = []
        for n in all_nums:
            clean_n = n.replace('%', '').replace('$', '').replace(',', '')
            try:
                val = float(clean_n)
                if 1990 <= val <= 2030: continue
                if val > 10000000 and '.' not in clean_n: continue
                metrics.append(n)
            except:
                continue

        # 1. Impact Score (Calibrated: 8 metrics is now the strong threshold)
        metric_count = len(set(metrics))
        impact_score = min(100, (metric_count / 8) * 100) 
        
        # 2. Verb Strength (Calibrated: 10 power verbs is now the strong threshold)
        power_found = [v for v in POWER_VERBS if re.search(rf'\b{v}\b', text_lower)]
        weak_found = [v for v in WEAK_VERBS if re.search(rf'\b{v}\b', text_lower)]
        
        power_count = len(power_found)
        weak_count = len(weak_found)
        
        if power_count == 0:
            verb_score = 0
        else:
            base_score = (power_count / (power_count + weak_count)) * 100 if (power_count + weak_count) > 0 else 0
            quantity_multiplier = min(1.0, power_count / 10)
            verb_score = base_score * quantity_multiplier
            
        # 3. Keyword Identity (Cloud)
        all_keywords = []
        for domain, kws in INDUSTRY_DOMAINS.items():
            for kw in kws:
                if rf"\b{kw.lower()}\b" in text_lower:
                    all_keywords.append(kw)
        
        top_keywords = [kw for kw, _ in Counter(all_keywords).most_common(15)]
        
        # 4. Section Health
        sections = {
            "Contact Info": bool(re.search(r'email|phone|@|\d{10}|linkedin|github', text_lower)),
            "Experience": bool(re.search(r'experience|work|employment|history|professional', text_lower)),
            "Skills": bool(re.search(r'skills|technologies|tools|expertise|stack', text_lower)),
            "Education": bool(re.search(r'education|university|college|degree|bachelor|master', text_lower))
        }
        
        section_score = (sum(sections.values()) / len(sections)) * 100
        
        # 5. Success Prediction (Data-Driven)
        prediction_res = {"prediction": 50.0, "benchmarks": None}
        if resume_data:
            prediction_res = ScoringService.predict_success(resume_data, text)
            
        # 6. Overall Audit Score (Highly reactive to improvements)
        # Impact (40%) + Verbs (25%) + Sections (25%) + ML Market Probability (10%)
        base_audit = (impact_score * 0.4) + (verb_score * 0.25) + (section_score * 0.25) + (prediction_res["prediction"] * 0.1)
        
        # Seniority Bonus (Up to 5 points for experience maturity)
        exp_years = resume_data.get("experience_years", 0) if resume_data else 0
        seniority_bonus = min(5, (exp_years / 10) * 5) if exp_years >= 3 else 0
        
        overall_audit = min(100, base_audit + seniority_bonus)

        # 7. Generate Elaborate AI Suggestions to hit 80%+
        # 7. Generate Elaborate AI Suggestions to hit 80%+
        remedies = []
        
        DOMAIN_SPECIFIC_ADVICE = {
            "Healthcare": "Focus on HIPAA compliance, HL7/FHIR protocols, and data privacy in patient-facing systems.",
            "Fintech": "Highlight transaction security, PCI-DSS compliance, and high-concurrency ledger management.",
            "E-commerce": "Emphasize conversion optimization, inventory scaling, and global payment gateway integration.",
            "Cybersecurity": "Document threat modeling, zero-trust architectures, and incident response lifecycle ownership.",
            "Web Development": "Showcase core web vitals, state-management depth, and micro-frontend orchestration.",
            "Data & AI": "Detail model interpretability, feature engineering pipelines, and MLOps at scale.",
            "Cloud & DevOps": "Highlight IaC maturity (Terraform/CDK), disaster recovery testing, and cost-optimization metrics.",
            "Product Management": "Focus on product-market fit metrics, stakeholder negotiation, and data-driven roadmap prioritization.",
            "Management/Leadership": "Emphasize team scaling (0 to 1), P&L ownership, and strategic organizational transformation."
        }

        if overall_audit < 98:
            domain_name = prediction_res.get("domain_prediction", "General Tech")
            market_data = prediction_res.get("benchmarks") or {}
            
            # 1. Skill Density (Using Market Intelligence)
            if market_data:
                top_skills = market_data.get("market_skills", [])
                user_skills = [s.lower() for s in (resume_data.get("skills", []) if resume_data else [])]
                missing_critical = [s for s in top_skills[:10] if s.lower() not in user_skills]
                
                if missing_critical:
                    skill_list = ', '.join(missing_critical[:3])
                    remedies.append({
                        "type": "Strategic Skill Gap",
                        "text": f"Your profile is missing '{skill_list}', which are currently top-tier requirements for {domain_name} roles. Integrating these specific triggers will increase your visibility in semantic search algorithms by approximately 30%.",
                        "impact_on_score": f"+{len(missing_critical)*1.5}%"
                    })

            # 2. Impact Optimization (Quantitative)
            if impact_score < 90:
                needed = 10 - metric_count
                remedies.append({
                    "type": "Quantitative Proof",
                    "text": f"Recruiters in the {domain_name} sector prioritize outcome-based resumes. Your metric density is low. Aim to quantify {max(2, needed)} more achievements—focusing on cost reduction, speed increases, or user growth.",
                    "impact_on_score": "+12%"
                })
            
            # 3. Linguistic Strength (Verb Power)
            if verb_score < 80:
                remedies.append({
                    "type": "Senior Authority Tone",
                    "text": f"To align with {domain_name} leadership standards, replace passive verbs with decisive ones. Use terms like 'Orchestrated' or 'Spearheaded' to signal that you didn't just 'assist' but actually 'owned' the technical outcomes.",
                    "impact_on_score": "+8%"
                })
                
            # 4. Domain Specialization (Actionable Industry Insight)
            specialized_tip = DOMAIN_SPECIFIC_ADVICE.get(domain_name)
            if specialized_tip and constraints.get("can_add_projects"):
                remedies.append({
                    "type": "Industry Edge",
                    "text": f"Quick Win: {specialized_tip} Adding just one project reflecting these keywords can boost your industry relevance by 15% immediately.",
                    "impact_on_score": "+10%"
                })
            elif specialized_tip:
                # If they can't add projects, suggest re-wording an existing project to include these keywords
                remedies.append({
                    "type": "Contextual Pivot",
                    "text": f"Strategic Insight: Re-word your existing project descriptions to include keywords like {specialized_tip.split(':')[0]}. This signals domain expertise without requiring new project work.",
                    "impact_on_score": "+7%"
                })
            
            # 5. Fast-Track Upskilling (Pathway to 100% - only if allowed)
            if constraints.get("can_learn_skills") and market_data:
                top_skills = market_data.get("market_skills", [])
                user_skills = [s.lower() for s in (resume_data.get("skills", []) if resume_data else [])]
                upskill_targets = [s for s in top_skills[:12] if s.lower() not in user_skills]
                
                if upskill_targets:
                    quick_learn = upskill_targets[:2]
                    remedies.append({
                        "type": "Skill Fast-Track",
                        "text": f"To hit 100%, consider adding or learning {', '.join(quick_learn)}. These are 'High-Velocity' skills that can be picked up in a few weeks and are currently in high demand for {domain_name} roles.",
                        "impact_on_score": "+10%"
                    })
            elif market_data:
                # If they can't learn skills, focus on "Linguistic Skill Mining"
                remedies.append({
                    "type": "Hidden Skill Mining",
                    "text": f"Since you are focusing on your current stack, ensure you haven't missed mentioning specialized sub-tools or versions related to {domain_name}. Deepening the description of your existing skills can increase semantic match by 10%.",
                    "impact_on_score": "+8%"
                })
            
            # 6. Strategic Formatting (Actionable seniority signaling)
            remedies.append({
                "type": "Authority Signaling",
                "text": "Strategy: Use 'Senior-level' language for your current projects. Emphasize 'end-to-end ownership' and 'cross-team collaboration' to bridge any seniority gap without needing more years of experience.",
                "impact_on_score": "+12%"
            })
            
            # 5. Section Health
            for section, exists in sections.items():
                if not exists:
                    remedies.append({
                        "type": "Structural Integrity",
                        "text": f"CRITICAL: The '{section}' section was not detected. This is a primary rejection trigger for automated parsers. Ensure the header is standard and the content is plain text.",
                        "impact_on_score": "+20%"
                    })

        return {
            "mode": "audit",
            "overall_score": round(overall_audit, 2),
            "success_prediction": prediction_res["prediction"],
            "remedies": remedies[:4],
            "keyword_cloud": resume_data.get("skills", [])[:12] if resume_data else [],
            "impact_metrics": {
                "score": round(impact_score, 2),
                "count": metric_count,
            },
            "verb_strength": {
                "score": round(verb_score, 2),
                "power_verbs_count": power_count,
                "weak_verbs_count": weak_count,
                "found_power": list(set(power_found))[:8],
                "found_weak": list(set(weak_found))[:8]
            },
            "section_health": sections,
            "domain_prediction": ParsingService.classify_domain(text)
        }
