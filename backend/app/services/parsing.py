import re
from typing import List, Dict, Any

from app.core.constants import (
    SKILL_MAP, SKILL_KEYWORDS, SKILL_GROUPS, MONTH_MAP,
    INDUSTRY_DOMAINS, SENIORITY_SIGNALS, MATURITY_SIGNALS,
    ARCHITECTURE_KEYWORDS, PRODUCTION_KEYWORDS, ARCHITECTURAL_PATTERNS,
    SOFT_SKILLS_KEYWORDS, FRONTEND_DEPTH_KEYWORDS
)
from datetime import datetime

class ParsingService:
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        found_skills = set()
        normalized_text = text.lower()
        
        for variation, normalized in SKILL_MAP.items():
            pattern = r'\b' + re.escape(variation) + r'\b'
            if re.search(pattern, normalized_text):
                found_skills.add(normalized)
        
        return list(found_skills)

    @staticmethod
    def extract_experience_years(text: str) -> float:
        """Improved experience extraction using date ranges"""
        month_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        year_pattern = r'(?:\d{4})'
        date_pattern = rf'({month_pattern}\s+{year_pattern})'
        present_pattern = r'(?:Present|Current|Now|Onward[s]?|Till Date|To Date|Active)'
        
        # 1. Handle Standard Ranges: Date to (Date or Present)
        range_pattern = rf'{date_pattern}\s*(?:-|to|until)\s*({date_pattern}|{present_pattern})'
        
        # 2. Handle Open-ended Ranges: Date (Present Keyword)
        # Examples: "Jan 2020 onward", "Since Jan 2020", "Jan 2020 - "
        # Modified to ensure date_pattern is always in a capturing group
        open_ended_pattern = rf'(?:Since\s+{date_pattern}(?:\s*{present_pattern})?)|(?:{date_pattern}\s*(?:-|to|until)?\s*{present_pattern})|(?:{date_pattern}\s*-\s*(?!\d))'
        
        total_months = 0
        found_ranges = False
        track_indices = []

        # Process standard ranges first
        matches = list(re.finditer(range_pattern, text, re.IGNORECASE))
        for match in matches:
            found_ranges = True
            track_indices.append(match.span())
            
            start_str = match.group(1).lower()
            end_str = match.group(2).lower()
            
            start_date = ParsingService._parse_date(start_str)
            if re.search(present_pattern, end_str, re.IGNORECASE):
                end_date = datetime.now()
            else:
                end_date = ParsingService._parse_date(end_str)
            
            if start_date and end_date:
                diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                if diff > 0:
                    total_months += diff

        # Process open-ended ranges, but avoid those already covered by standard ranges
        matches = list(re.finditer(open_ended_pattern, text, re.IGNORECASE))
        for match in matches:
            span = match.span()
            # Check if this match overlaps significantly with any already processed range
            is_overlap = any(max(span[0], s[0]) < min(span[1], s[1]) for s in track_indices)
            if is_overlap:
                continue
                
            found_ranges = True
            track_indices.append(span)
            
            # Find the first non-None group which should be our date
            date_str = next((g for g in match.groups() if g is not None), None)
            if not date_str: continue
            
            start_date = ParsingService._parse_date(date_str.lower())
            end_date = datetime.now()
            
            if start_date:
                diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                if diff > 0:
                    total_months += diff

        if found_ranges:
            return round(total_months / 12.0, 1)
        
        patterns = [
            r'(\d+(?:\.\d+)?)\+?\s*years?\s*of\s*experience',
            r'experience:\s*(\d+(?:\.\d+)?)\+?\s*years?',
            r'(\d+(?:\.\d+)?)\s*years?\s*in'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return 0.0

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            parts = date_str.split()
            if len(parts) == 2:
                month = MONTH_MAP.get(parts[0].lower(), 1)
                year = int(parts[1])
                return datetime(year, month, 1)
        except:
            pass
        return None

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\b\d{10}\b'
        ]
        
        email = re.search(email_pattern, text)
        phone = None
        for p in phone_patterns:
            m = re.search(p, text)
            if m:
                phone = m.group()
                break
                
        return {
            "email": email.group() if email else None,
            "phone": phone
        }

    @staticmethod
    def classify_domain(text: str) -> str:
        text_lower = text.lower()
        counts = {}
        for domain, keywords in INDUSTRY_DOMAINS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > 0:
                counts[domain] = count
        
        if not counts:
            return "General Tech"
        return max(counts, key=counts.get)

    @staticmethod
    def detect_seniority(text: str) -> str:
        text_lower = text.lower()
        for level, signals in SENIORITY_SIGNALS.items():
            for signal in signals:
                if re.search(rf"\b{re.escape(signal)}\b", text_lower):
                    return level
        # Check for years as proxy
        exp = ParsingService.extract_experience_years(text)
        if exp >= 8: return "Lead"
        if exp >= 5: return "Senior"
        return "Junior"

    @staticmethod
    def extract_maturity_signals(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        signals = {
            "scale_signals": [],
            "ownership_signals": [],
            "optimization_signals": [],
            "architecture_depth": [],
            "production_ready": [],
            "soft_skills": [],
            "frontend_depth": [],
            "architectural_patterns": {}
        }
        
        for category, patterns in MATURITY_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    signals[f"{category.lower()}_signals"].append(pattern)
        
        for cluster, keywords in ARCHITECTURAL_PATTERNS.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                signals["architectural_patterns"][cluster] = found
        
        signals["architecture_depth"] = [kw for kw in ARCHITECTURE_KEYWORDS if kw in text_lower]
        signals["production_ready"] = [kw for kw in PRODUCTION_KEYWORDS if kw in text_lower]
        signals["soft_skills"] = [kw for kw in SOFT_SKILLS_KEYWORDS if kw in text_lower]
        signals["frontend_depth"] = [kw for kw in FRONTEND_DEPTH_KEYWORDS if kw in text_lower]
        
        return signals

    @staticmethod
    def parse_job_description(text: str) -> Dict[str, Any]:
        """Deep JD parsing with mandatory/preferred split, domain, and maturity requirements"""
        all_found_skills = ParsingService.extract_skills(text)
        domain = ParsingService.classify_domain(text)
        maturity_reqs = ParsingService.extract_maturity_signals(text)
        
        # Split text into sentences to check context
        sentences = re.split(r'[.!?\n]', text)
        mandatory_skills = []
        preferred_skills = []
        
        mandatory_indicators = ["mandatory", "required", "must have", "essential", "minimum", "should have"]
        preferred_indicators = ["preferred", "plus", "bonus", "optional", "nice to have", "exposure to"]
        
        for skill in all_found_skills:
            is_mandatory = False
            is_preferred = False
            
            for sentence in sentences:
                if skill.lower() in sentence.lower():
                    if any(ind in sentence.lower() for ind in mandatory_indicators):
                        is_mandatory = True
                    if any(ind in sentence.lower() for ind in preferred_indicators):
                        is_preferred = True
            
            if is_mandatory:
                mandatory_skills.append(skill)
            elif is_preferred:
                preferred_skills.append(skill)
            else:
                mandatory_skills.append(skill) # Default to mandatory for safety

        # Extract Experience Range
        range_pattern = r'(\d+)\s*(?:-|to)\s*(\d+)\s*years?'
        min_only_pattern = r'(?:min(?:imum)?|at\s+least|more\s+than|(\d+)\+)\s*(\d+)\s*years?'
        
        range_match = re.search(range_pattern, text, re.IGNORECASE)
        min_exp = 0.0
        max_exp = None
        
        if range_match:
            min_exp = float(range_match.group(1))
            max_exp = float(range_match.group(2))
        else:
            min_match = re.search(min_only_pattern, text, re.IGNORECASE)
            if min_match:
                val = min_match.group(1) or min_match.group(2)
                min_exp = float(val)
        
        return {
            "required_skills": mandatory_skills,
            "preferred_skills": preferred_skills,
            "min_experience": min_exp,
            "max_experience": max_exp,
            "domain": domain,
            "expected_seniority": ParsingService.detect_seniority(text),
            "maturity_requirements": maturity_reqs
        }
