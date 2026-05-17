from typing import Dict, List, Any
from app.services.parser.section_extractor import SectionExtractor
from app.services.parser.skill_extractor import SkillExtractor
from app.services.parser.chronology_parser import ChronologyParser
from app.services.parser.domain_classifier import DomainClassifier

class ParsingService:
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        return SkillExtractor.extract_skills(text)

    @staticmethod
    def extract_work_sections(text: str) -> str:
        return SectionExtractor.extract_work_sections(text)

    @staticmethod
    def check_employment_structure(text: str) -> Dict[str, Any]:
        return SectionExtractor.check_employment_structure(text)

    @staticmethod
    def extract_experience_years(text: str) -> float:
        res = ChronologyParser.extract_experience_years(text)
        return res if isinstance(res, dict) else {"total_years": res, "intervals": []}

    @staticmethod
    def classify_domain(text: str) -> str:
        return DomainClassifier.classify_domain(text)

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Any]:
        import re
        email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text)
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None
        }

    @staticmethod
    def extract_maturity_signals(text: str) -> Dict[str, Any]:
        # Minimal wrapper for now, can be modularized further if needed
        return {"architecture_depth": [], "operational_maturity": []}
