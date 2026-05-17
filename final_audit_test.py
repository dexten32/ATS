import sys
import os
import json
import re

# Ensure we can import from 'backend/app'
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.ingestion import IngestionService
from app.services.parsing import ParsingService
from app.services.scoring import AuditorService

def run_elite_audit():
    print("\n" + "="*60)
    print(" ATS ELITE INTELLIGENCE ENGINE - FINAL AUDIT TERMINAL ")
    print("="*60)
    
    path = input("\nEnter the full path to a resume (PDF/DOCX/TXT): ").strip().replace('"', '')
    
    if not os.path.exists(path):
        print(f"ERROR: File not found at {path}")
        return

    try:
        # 1. Extraction & Parsing
        print("\n[1/3] Extracting and Parsing Engineering Context...")
        text = IngestionService.extract_text(path)
        text = IngestionService.sanitize_text(text)
        
        skills = ParsingService.extract_skills(text)
        domain = ParsingService.classify_domain(text)
        exp_data = ParsingService.extract_experience_years(text)
        exp_years = exp_data["total_years"]
        
        # 2. Structural Evidence Peek
        struct = ParsingService.check_employment_structure(text)
        
        resume_data = {
            "skills": skills,
            "experience_years": exp_years,
            "domain": domain,
            "contacts_found": bool(re.search(r'@', text))
        }

        # 3. Final Hardened Audit
        print("[2/3] Analyzing Technical Depth & Professional Narrative...")
        results = AuditorService.audit(text, resume_data)

        # 4. Results Display
        print("\n" + "="*60)
        print(f" FINAL HIREABILITY SCORE: {results['overall_score']}%")
        print("="*60)
        
        # DEBUG: Print Extracted Blocks (Issue 18)
        print("\n[DEBUG] RAW TEXT PREVIEW (FIRST 500 CHARS):")
        print(f"{text[:500]}...")
        
        work_text = ParsingService.extract_work_sections(text)
        print("\n[DEBUG] EXTRACTED WORK BLOCKS:")
        if work_text:
            for i, block in enumerate(work_text.split('\n\n')):
                print(f" --- Block {i+1} ---\n{block.strip()[:300]}...")
        else:
            print(" !!! NO WORK BLOCKS DETECTED !!!")
        print("\n" + "-"*60)
        
        print(f"Detected Experience: {exp_years} years")
        if results.get("experience_intervals"):
            print(f"  > Chronology: {', '.join(results['experience_intervals'])}")
        print(f"Detected Domain:     {domain}")
        print(f"Structural Hits:    {struct.get('structural_hits', 0)} ({struct.get('confidence')})")
        print("-"*60)
        print("SCORING BREAKDOWN:")
        print(f" - Career Evidence:      {results['career_evidence']}/100")
        print(f" - Foundation Strength: {results['foundation_strength']}/100")
        print(f" - Technical Depth:      {results['technical_depth']}/100")
        print(f" - Credibility Level:    {results['credibility_level']:.2f}")
        print("-"*60)
        print("CRITICAL REMEDIES:")
        for remedy in results['remedies']:
            print(f" [!] {remedy['type']}: {remedy['text']} (Impact: {remedy['impact']})")
        print("="*60 + "\n")

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_elite_audit()
