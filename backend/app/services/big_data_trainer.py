import csv
import json
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import sys
import re
from typing import Dict, List

# Add backend to path for imports
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
from app.core.constants import INDUSTRY_DOMAINS

class BigDataTrainer:
    @staticmethod
    def extract_features_v1(row):
        """Dataset 1: 1GB Hiring Outcomes"""
        try:
            exp_years = float(row.get('experience', 0) or 0)
            hs = json.loads(row.get('hardSkills_cv', '[]'))
            ss = json.loads(row.get('softSkills_cv', '[]'))
            status = 1 if "Приглашение" in row.get('cv_status', '') else 0
            title = row.get('positionName', '').lower()
            domain_id = 0
            for i, (domain, keywords) in enumerate(INDUSTRY_DOMAINS.items()):
                if any(kw.lower() in title for kw in keywords):
                    domain_id = i + 1
                    break
            return [exp_years, len(hs), len(ss), 0.0, domain_id], status
        except: return None, None

    @staticmethod
    def extract_features_v2(row):
        """Dataset 2: Resume-JD Matches"""
        try:
            exp_text = row.get('experiencere_requirement', '0')
            exp_years = float(re.findall(r'\d+', str(exp_text))[0]) if re.findall(r'\d+', str(exp_text)) else 0.0
            skills_text = row.get('skills', '[]')
            skill_count = str(skills_text).count(',') + 1 if '[' in str(skills_text) else 0
            title = row.get('job_position_name', '').lower()
            domain_id = 0
            for i, (domain, keywords) in enumerate(INDUSTRY_DOMAINS.items()):
                if any(kw.lower() in title for kw in keywords):
                    domain_id = i + 1
                    break
            score = float(row.get('matched_score', 0) or 0)
            status = 1 if score > 0.7 else 0
            return [exp_years, skill_count, 5, 0.0, domain_id], status
        except: return None, None

    @staticmethod
    def train_master_intelligence(base_path: str, output_dir: str):
        print(f"--- Building Unified Market Intelligence ---")
        
        # 1. Success Model Data (Merge v1 and v2)
        X, y = [], []
        benchmarks = {}
        
        # Dataset 1
        path1 = os.path.join(base_path, "train.csv")
        if os.path.exists(path1):
            print(f"Ingesting Hiring Outcomes...")
            with open(path1, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    feat, target = BigDataTrainer.extract_features_v1(row)
                    if feat:
                        X.append(feat); y.append(target)
                        if target == 1:
                            d_id = feat[4]
                            if d_id not in benchmarks: benchmarks[d_id] = []
                            benchmarks[d_id].append(feat[:4])

        # Dataset 2
        path2 = os.path.join(base_path, "resume_data.csv")
        if os.path.exists(path2):
            print(f"Ingesting Match Data...")
            with open(path2, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    feat, target = BigDataTrainer.extract_features_v2(row)
                    if feat:
                        X.append(feat); y.append(target)
                        if target == 1:
                            d_id = feat[4]
                            if d_id not in benchmarks: benchmarks[d_id] = []
                            benchmarks[d_id].append(feat[:4])

        # 2. Market Intelligence (New Files)
        market_intel = {
            "top_skills": {},     # domain -> [skills]
            "salary_map": {},     # role -> {exp: salary}
            "demand_trends": {}   # skill -> growth_rate
        }

        # Ingest Job Postings & Skill Demand
        path3 = os.path.join(base_path, "job_postings.csv")
        if os.path.exists(path3):
            print(f"Analyzing Market Demands...")
            with open(path3, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get('job_title', 'General')
                    skills = row.get('skills_required', '').split('|')
                    salary = float(row.get('salary_midpoint', 0) or 0)
                    
                    if title not in market_intel["salary_map"]: market_intel["salary_map"][title] = []
                    market_intel["salary_map"][title].append(salary)
                    
                    # Map title to industry domains
                    for domain in INDUSTRY_DOMAINS:
                        if any(kw.lower() in title.lower() for kw in INDUSTRY_DOMAINS[domain]):
                            if domain not in market_intel["top_skills"]: market_intel["top_skills"][domain] = {}
                            for s in skills:
                                market_intel["top_skills"][domain][s] = market_intel["top_skills"][domain].get(s, 0) + 1

        # Process top skills
        for domain in market_intel["top_skills"]:
            sorted_skills = sorted(market_intel["top_skills"][domain].items(), key=lambda x: x[1], reverse=True)
            market_intel["top_skills"][domain] = [s[0] for s in sorted_skills[:15]]

        # Train & Save
        print("Finalizing Brain...")
        model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
        model.fit(np.array(X), np.array(y))
        
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "success_model.pkl"), 'wb') as f: pickle.dump(model, f)
        
        # Merge benchmarks with market intel
        final_bench = {}
        for d_id, stats in benchmarks.items():
            domain_name = list(INDUSTRY_DOMAINS.keys())[d_id-1] if d_id > 0 else "General"
            avg = np.mean(stats, axis=0).tolist()
            final_bench[domain_name] = {
                "avg_experience": round(avg[0], 1),
                "avg_hard_skills": round(avg[1], 1),
                "market_skills": market_intel["top_skills"].get(domain_name, [])
            }
        
        with open(os.path.join(output_dir, "market_intelligence.pkl"), 'wb') as f:
            pickle.dump({"benchmarks": final_bench, "market_intel": market_intel}, f)

        print(f"--- Deployment Ready: Market Brain Synced ---")

if __name__ == "__main__":
    # Get to project root (g:\ATS)
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # CSVs are now in root/training_data
    data_path = os.path.join(base, "training_data")
    # Output models go to backend/app/core
    backend_path = os.path.join(base, "backend")
    core_path = os.path.join(backend_path, "app", "core")
    
    BigDataTrainer.train_master_intelligence(data_path, core_path)
