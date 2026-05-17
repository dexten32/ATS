import re
from typing import List, Dict, Any

class PenaltyEngine:
    @staticmethod
    def calculate_penalties(text_lower: str, exp_years: float, tool_hits: int, word_count: int) -> Dict[str, Any]:
        inflation_penalty = 0
        if exp_years < 2 and re.search(r'millions of users|petabytes|large-scale distributed|architected|led a team', text_lower):
            inflation_penalty += 15
        if tool_hits > 18 and word_count < 250:
            inflation_penalty += 10
            
        return {
            "inflation": inflation_penalty
        }

    @staticmethod
    def apply_graduated_multipliers(raw_score: float, power_verbs: int) -> float:
        if power_verbs < 3: return raw_score * 0.75
        if power_verbs < 6: return raw_score * 0.9
        return raw_score

    @staticmethod
    def apply_junior_cap(score: float, exp_years: float, tool_hits: int) -> float:
        if exp_years < 2 and tool_hits < 5:
            max_allowed = 65 + (exp_years / 2) * 15
            return min(max_allowed, score)
        return score
