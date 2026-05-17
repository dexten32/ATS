import json
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from app.core.constants import INDUSTRY_DOMAINS

class DomainTrainer:
    @staticmethod
    def train_from_jsonl(file_path: str, model_output_path: str):
        print(f"--- Starting Training from {file_path} ---")
        
        texts = []
        labels = []
        
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Extract full text for training
                    summary = data.get("personal_info", {}).get("summary", "")
                    skills_list = []
                    skills_obj = data.get("skills", {}).get("technical", {})
                    for category, items in skills_obj.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "name" in item:
                                    skills_list.append(item["name"])
                    
                    # Fix 1: Include job titles + responsibility descriptions for richer domain signal
                    experience = data.get("experience", [])
                    titles = " ".join(e.get("title", "") for e in experience if isinstance(e, dict))
                    responsibilities = " ".join(
                        " ".join(e.get("responsibilities", [])) if isinstance(e.get("responsibilities"), list)
                        else e.get("responsibilities", "")
                        for e in experience if isinstance(e, dict)
                    )
                    full_text = f"{summary} {titles} {responsibilities} {' '.join(skills_list)}"
                    
                    # Determine label using existing heuristics (Self-Supervision)
                    best_domain = "General"
                    max_matches = 0
                    text_lower = full_text.lower()
                    
                    for domain, keywords in INDUSTRY_DOMAINS.items():
                        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
                        if matches > max_matches:
                            max_matches = matches
                            best_domain = domain
                    
                    if max_matches > 0: # Only train on data we are somewhat sure about
                        texts.append(full_text)
                        labels.append(best_domain)
                        
                except Exception as e:
                    continue

        if len(texts) < 10:
            print("Not enough samples to train. Aborting.")
            return

        print(f"Extracted {len(texts)} samples for training across {len(set(labels))} domains.")

        # Fix 2: Add train/test split so model accuracy is measurable
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels if len(set(labels)) > 1 else None
        )

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))),
            ('clf', LinearSVC(C=1.0, max_iter=1000))
        ])

        pipeline.fit(X_train, y_train)
        accuracy = pipeline.score(X_test, y_test)
        print(f"Domain Classifier Accuracy (held-out 20%): {accuracy:.2%}")

        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        with open(model_output_path, 'wb') as f:
            pickle.dump(pipeline, f)
        print(f"Successfully trained and saved model to {model_output_path}")

if __name__ == "__main__":
    # For standalone testing
    import sys
    # Get to project root (g:\ATS)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # JSONL is now in root/training_data
    data_path = os.path.join(base_dir, "training_data", "master_resumes.jsonl")
    # Output model goes to backend/app/core
    model_path = os.path.join(base_dir, "backend", "app", "core", "domain_model.pkl")
    DomainTrainer.train_from_jsonl(data_path, model_path)
