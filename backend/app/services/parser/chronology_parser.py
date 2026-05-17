import re
from datetime import datetime
from app.core.constants import MONTH_MAP
from app.services.parser.section_extractor import SectionExtractor

class ChronologyParser:
    @staticmethod
    def extract_experience_years(text: str) -> float:
        """Improved experience extraction using date ranges inside work sections."""
        text_norm = text.replace('\u2013', '-').replace('\u2014', '-')
        
        # Only parse inside work sections
        work_text = SectionExtractor.extract_work_sections(text_norm)
        if not work_text:
            return 0.0
            
        text = work_text
        month_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})'
        year_pattern = r'(?:\d{4}|(?:\'|’)?\d{2})' 
        # Support MM/YY, MM-YYYY, YYYY, and Jan YY (Remove \b for squashed text)
        date_pattern = rf'(?:{month_pattern}[./\s,\-]*{year_pattern}|\d{{4}})'
        present_pattern = r'(?:Present|Current|Now|Onward[s]?|Till Date|To Date|Active|Currently|Continuous)'
        
        range_pattern = rf'({date_pattern})\s*(?:-|to|until|–|—)\s*({date_pattern}|{present_pattern})'
        open_ended_pattern = rf'(?:Since\s+({date_pattern})(?:\s*{present_pattern})?)|(?:({date_pattern})\s*(?:-|to|until|–|—)?\s*{present_pattern})'
        
        date_ranges = []
        # Standard ranges
        for match in re.finditer(range_pattern, text, re.IGNORECASE):
            start_date = ChronologyParser._parse_date_string(match.group(1))
            end_date = ChronologyParser._parse_date_string(match.group(2))
            if start_date and end_date:
                date_ranges.append((start_date, end_date))
        
        # Open-ended
        for match in re.finditer(open_ended_pattern, text, re.IGNORECASE):
            # Check either group 1 or group 2 depending on which branch matched
            date_str = match.group(1) or match.group(2)
            start_date = ChronologyParser._parse_date_string(date_str)
            if start_date:
                date_ranges.append((start_date, datetime.now()))

        if not date_ranges:
            return {"total_years": 0.0, "intervals": []}

        # Sort and merge overlapping ranges
        date_ranges.sort(key=lambda x: x[0])
        merged = []
        if date_ranges:
            curr_start, curr_end = date_ranges[0]
            for next_start, next_end in date_ranges[1:]:
                if next_start <= curr_end:
                    curr_end = max(curr_end, next_end)
                else:
                    merged.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged.append((curr_start, curr_end))

        total_days = sum((end - start).days for start, end in merged)
        return {
            "total_years": round(total_days / 365.25, 1),
            "intervals": [f"{s.strftime('%b %Y')} - {e.strftime('%b %Y')}" for s, e in merged]
        }

    @staticmethod
    def _parse_date_string(date_str: str) -> datetime:
        if not date_str: return None
        if any(p in date_str.lower() for p in ['present', 'current', 'now', 'date', 'active']):
            return datetime.now()
            
        clean_str = re.sub(r'[./\s,\-]+', ' ', date_str).strip().lower()
        # Split using regex to handle squashed text like 'Apr2025' (Issue 20)
        parts = re.findall(r'[a-z]+|\d+', clean_str)
        
        year = None
        month = 1
        
        for part in parts:
            if part.isdigit():
                if len(part) == 4: year = int(part)
                elif len(part) == 2: 
                    val = int(part)
                    if val > 50: year = 1900 + val
                    else: year = 2000 + val
            elif part[:3] in MONTH_MAP:
                month = MONTH_MAP[part[:3]]
        
        if year:
            return datetime(year, month, 1)
        return None
