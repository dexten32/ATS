import re
from typing import List
from app.core.constants import _SKILL_MAP_NORMALIZED

class SkillExtractor:
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        found_skills = set()
        normalized_text = text.lower()
        
        # Sort variations by length descending
        sorted_variations = sorted(_SKILL_MAP_NORMALIZED.keys(), key=len, reverse=True)
        
        for variation in sorted_variations:
            normalized = _SKILL_MAP_NORMALIZED[variation]
            # Fuzzy match: allow optional spaces/hyphens
            fuzzy_variation = variation.replace(" ", r"[\s\-]*")
            pattern = rf'\b{fuzzy_variation}\b'
            
            if re.search(pattern, normalized_text):
                found_skills.add(normalized)
                normalized_text = re.sub(pattern, " " * len(variation), normalized_text)
                
        return list(found_skills)
