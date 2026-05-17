import re
from app.core.constants import INDUSTRY_DOMAINS

class DomainClassifier:
    @staticmethod
    def classify_domain(text: str) -> str:
        text_lower = text.lower()
        header = text_lower[:500]
        counts = {}
        
        for domain, keywords in INDUSTRY_DOMAINS.items():
            full_count = sum(4 for kw in keywords if kw in text_lower)
            header_count = sum(3 for kw in keywords if kw in header)
            
            # Contextual Evidence Boost
            if domain == "Database & Infrastructure":
                narrative_patterns = [r"migrat", r"tun", r"upgrad", r"manag", r"configur", r"backup", r"failover"]
                dba_tools = ["oracle", "rman", "asm", "rac", "dataguard", "goldengate", "oem"]
                for tool in dba_tools:
                    for pattern in narrative_patterns:
                        if re.search(rf"{pattern}.*?{tool}|{tool}.*?{pattern}", text_lower, re.DOTALL):
                            full_count += 12 
            
            first_line = text_lower.split('\n')[0]
            title_boost = 15 if any(kw in first_line for kw in keywords) else 0
            
            total = full_count + header_count + title_boost
            if total > 0:
                counts[domain] = total
        
        if not counts:
            return "Software Engineering"
        return max(counts, key=counts.get)
