from typing import Dict, Any

class CareerScorer:
    @staticmethod
    def calculate_career_score(exp_years: float, text_lower: str, confidence: str, power_verbs: int) -> Dict[str, Any]:
        has_exp = exp_years > 0
        has_proj = any(kw in text_lower for kw in ["projects", "github.com", "portfolio", "personal project"])
        has_cert = any(kw in text_lower for kw in ["certified", "certification", "aws certified", "ocp", "oca"])
        
        ownership_signals = ["lead", "architect", "driven", "managed", "owned", "shipped", "deployed", "scaled", "stakeholder", "end-to-end"]
        ownership_count = sum(1 for kw in ownership_signals if kw in text_lower)
        ownership_boost = min(15, ownership_count * 4)

        has_high_tech = len(["found" for s in ["oracle", "java", "python", "k8s", "docker", "aws", "sql", "dba"] if s in text_lower]) > 5

        if exp_years == 0 and (power_verbs > 3 or has_high_tech):
            exp_points = 45 
            career_points = exp_points + (ownership_boost * 0.5)
        elif exp_years > 0:
            duration_points = min(60, (exp_years / 5) * 60)
            exp_points = duration_points
            if confidence == "LOW" and exp_years > 2:
                exp_points *= 0.7
            career_points = min(100, max(exp_points, 45 if (has_proj and exp_points < 45) else exp_points) + ownership_boost)
        elif has_proj:
            proj_floor = 45 if power_verbs >= 3 else 25
            career_points = proj_floor + (ownership_boost * 0.5)
        elif has_cert:
            career_points = 20
        else:
            career_points = 0
            
        return {
            "score": career_points,
            "exp_years": exp_years,
            "has_proj": has_proj,
            "has_edu": bool("education" in text_lower or "university" in text_lower),
            "has_cert": has_cert
        }
