import re
from typing import Dict, Any, List

class SectionExtractor:
    @staticmethod
    def normalize_layout(text: str) -> str:
        """Repair PDF extraction artifacts: broken lines, column bleed, and duplicate whitespace."""
        # 1. Standardize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 2. Repair broken date lines (e.g., "Jan\n2022")
        # Matches Month name followed by a newline then a year
        months = r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
        text = re.sub(rf'({months})\n\s*(\d{{4}})', r'\1 \2', text, flags=re.IGNORECASE)
        
        # 3. Collapse multiple spaces (keep newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 4. Repair bullet bleed (Bullet at end of line)
        text = re.sub(r'([•●\-\*])\n\s*', r'\1 ', text)
        
        # 5. De-Squash text (e.g., "BackendDeveloper" -> "Backend Developer")
        # Handle CamelCase squashing
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        # Handle Letter-Number squashing (e.g., "Apr2025" -> "Apr 2025")
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        
        return text

    @staticmethod
    def extract_work_sections(text: str) -> str:
        """Extract only employment/experience sections for date parsing."""
        text = SectionExtractor.normalize_layout(text)
        
        # Flexible headers (Issue 18: Handle varied terminators and prefixes)
        terminator = r'[:|\-\u2013\u2014•\|●\.\s]*'
        work_keywords = rf'(?:experience|employment|work|career\s+history|professional\s+experience){terminator}'
        other_sections = rf'(?:education|skills|technical|certification|projects|summary|honors|publications|profile|academic){terminator}'
        
        # Normalize text to isolate headers
        pattern = rf'\b({work_keywords}|{other_sections})\b'
        headers = list(re.finditer(pattern, text, re.IGNORECASE))
        
        work_blocks = []
        if headers:
            for i, match in enumerate(headers):
                header_type = match.group(1).lower()
                # Check if it's a work header (excluding summary/profile keywords manually)
                if re.match(work_keywords, header_type, re.IGNORECASE) and not re.search(r'summary|profile', header_type):
                    start = match.end()
                    end = headers[i+1].start() if i+1 < len(headers) else len(text)
                    section_content = text[start:end]
                    
                    # Surgical Exclusion: Filter education blocks WITHIN the section rather than rejecting all (Issue 19)
                    edu_red_flags = r'\b(?:b\.tech|m\.tech|bca|mca|semester|cgpa|gpa|graduation|undergraduate|postgraduate|schooling|academic|curriculum|student|internship\s+training|coursework|10th|12th)\b'
                    
                    # Process section content in blocks
                    section_lines = section_content.split('\n')
                    for i in range(0, len(section_lines), 3):
                        block = "\n".join(section_lines[i : i+5])
                        if not re.search(edu_red_flags, block, re.IGNORECASE):
                            work_blocks.append(block)
        
        # FALLBACK: Sliding Window Block Scoring (Issue 18)
        if not work_blocks:
            lines = text.split('\n')
            titles_pattern = r'\b(?:engineer|administrator|manager|developer|architect|analyst|lead|dba|senior|specialist|consultant)\b'
            org_suffixes = r'\b(?:pvt\.?\s*ltd|ltd|inc|corp|co|systems|solutions|technologies|services|consulting|group|industries|@| at )\b'
            entity_pattern = r'(?:^|,)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            date_indicators = r'\b(?:\d{4}|present|current)\b'
            edu_red_flags = r'\b(?:b\.tech|m\.tech|bca|mca|semester|cgpa|gpa|graduation|undergraduate|postgraduate|schooling|academic|curriculum|student|internship\s+training|coursework|10th|12th|secondary|university|college|degree|bachelor|master)\b'

            for i in range(len(lines)):
                window_lines = lines[i : i+5]
                block_clean = "\n".join(window_lines).strip()
                if len(block_clean) < 15: continue
                
                has_title = bool(re.search(titles_pattern, block_clean, re.IGNORECASE))
                has_org = bool(re.search(org_suffixes, block_clean, re.IGNORECASE)) or bool(re.search(entity_pattern, block_clean))
                has_date = bool(re.search(date_indicators, block_clean, re.IGNORECASE))
                is_edu = bool(re.search(edu_red_flags, block_clean, re.IGNORECASE))
                
                if has_title and (has_org or has_date) and not is_edu:
                    work_blocks.append(block_clean)
                
        return "\n".join(work_blocks).strip()

    @staticmethod
    def check_employment_structure(text: str) -> Dict[str, Any]:
        """Verify structural evidence with sliding-window block scoring."""
        text = SectionExtractor.normalize_layout(text)
        text_lower = text.lower()
        
        titles_pattern = r'\b(?:engineer|administrator|manager|developer|architect|analyst|lead|dba|senior|specialist|consultant)\b'
        org_suffixes = r'\b(?:pvt\.?\s*ltd|ltd|inc|corp|co|systems|solutions|technologies|services|consulting|group|industries|@| at )\b'
        date_pattern = r'\b(?:\d{4}|present|current)\b'
        edu_red_flags = r'\b(?:b\.tech|m\.tech|bca|mca|semester|cgpa|gpa|graduation|undergraduate|postgraduate|schooling|academic|curriculum|student|internship\s+training|coursework|10th|12th|secondary|university|college|degree|bachelor|master)\b'
        
        lines = text.split('\n')
        total_weight = 0
        seen_ranges = set()
        
        for i in range(len(lines)):
            window = "\n".join(lines[i : i+4]).lower()
            if len(window.strip()) < 15: continue
            
            has_title = bool(re.search(titles_pattern, window))
            has_org = bool(re.search(org_suffixes, window)) or bool(re.search(r'(?:^|,)\s*([A-Z][a-z]+)', window))
            has_date = bool(re.search(date_pattern, window))
            is_edu = bool(re.search(edu_red_flags, window))
            
            if not is_edu:
                if has_title and has_org and has_date:
                    if window not in seen_ranges:
                        total_weight += 4
                        seen_ranges.add(window)
                elif has_title and (has_org or has_date):
                    if window not in seen_ranges:
                        total_weight += 1
                        seen_ranges.add(window)
        
        conf = "LOW"
        if total_weight >= 6: conf = "HIGH"
        elif total_weight >= 3: conf = "MEDIUM"
        
        return {"structural_hits": total_weight, "confidence": conf}
