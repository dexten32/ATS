import re
from typing import Dict, Any

class FoundationScorer:
    @staticmethod
    def calculate_foundation(text_lower: str, has_edu: bool, has_cert: bool) -> float:
        foundation_score = 0
        if has_edu: foundation_score += 30
        if re.search(r'computer science|software engineering|information technology|b\.tech|m\.tech|bca|mca', text_lower): foundation_score += 30
        if has_cert: foundation_score += 10
        
        systems_keywords = ["memory management", "pointers", "threading", "locks", "deadlock", "raft", "paxos", "sharding", "consensus", "atomic", "mutex", "distributed consensus"]
        found_systems = [kw for kw in systems_keywords if kw in text_lower]
        
        return min(100, foundation_score + len(found_systems) * 8)
