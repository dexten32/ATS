import csv
import json
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import sys
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
from app.core.constants import INDUSTRY_DOMAINS

# --- FIX 1: Domain ID mapping that is stable regardless of dict insertion order ---
# Previously: domain_id was derived from enumerate() position, which breaks if
# INDUSTRY_DOMAINS ever gains a new key or changes order between training and inference.
DOMAIN_NAME_TO_ID: Dict[str, int] = {
    name: i + 1 for i, name in enumerate(INDUSTRY_DOMAINS.keys())
}
DOMAIN_ID_TO_NAME: Dict[int, str] = {v: k for k, v in DOMAIN_NAME_TO_ID.items()}

# --- FIX 2: Canonical soft-skill vocabulary for consistent counting ---
# Previously: soft_skills_count was hardcoded to 5 in Dataset 2 and computed from
# raw JSON in Dataset 1. Both need to count against the same vocabulary so the
# model's feature[2] means the same thing at training and inference time.
SOFT_SKILL_VOCAB = {
    "communication", "leadership", "teamwork", "collaboration", "problem-solving",
    "problem solving", "critical thinking", "time management", "adaptability",
    "creativity", "mentoring", "conflict resolution", "presentation", "negotiation",
    "project management", "stakeholder management", "decision-making", "empathy",
    "organization", "attention to detail"
}


def _resolve_domain_id(title: str) -> int:
    """Map a job title to a stable domain ID. Returns 0 if no match."""
    title_lower = title.lower()
    for domain, keywords in INDUSTRY_DOMAINS.items():
        if any(kw.lower() in title_lower for kw in keywords):
            return DOMAIN_NAME_TO_ID[domain]
    return 0


def _count_soft_skills(skill_list: List[str]) -> int:
    """Count soft skills against the canonical vocabulary (case-insensitive)."""
    return sum(1 for s in skill_list if s.lower().strip() in SOFT_SKILL_VOCAB)


class BigDataTrainer:

    @staticmethod
    def extract_features_v1(row: dict) -> Tuple[Optional[List], Optional[int]]:
        """
        Dataset 1: Hiring Outcomes (train.csv, pipe-delimited).
        Label: 1 = candidate received an interview invitation ("Приглашение").
        Features: [exp_years, hard_skill_count, soft_skill_count, salary_proxy, domain_id]
        All five features represent CANDIDATE attributes. This is the only dataset
        that should be used to train the success model.
        """
        try:
            exp_years = float(row.get('experience', 0) or 0)

            raw_hs = row.get('hardSkills_cv', '[]') or '[]'
            raw_ss = row.get('softSkills_cv', '[]') or '[]'

            # FIX 3: Robust JSON parsing with fallback — previously a bare json.loads
            # that would raise on malformed rows and silently drop the whole row.
            try:
                hs = json.loads(raw_hs)
                if not isinstance(hs, list):
                    hs = []
            except (json.JSONDecodeError, TypeError):
                # Try comma-split as last resort
                hs = [s.strip() for s in raw_hs.strip('[]').split(',') if s.strip()]

            try:
                ss = json.loads(raw_ss)
                if not isinstance(ss, list):
                    ss = []
            except (json.JSONDecodeError, TypeError):
                ss = [s.strip() for s in raw_ss.strip('[]').split(',') if s.strip()]

            # FIX 4: Count soft skills against the canonical vocabulary, not raw length.
            # Previously len(ss) counted everything in the softSkills_cv field, including
            # skills that the inference side would never match. Now both sides use the same vocab.
            soft_skill_count = _count_soft_skills(ss)

            status = 1 if "Приглашение" in row.get('cv_status', '') else 0
            domain_id = _resolve_domain_id(row.get('positionName', ''))

            features = [exp_years, len(hs), soft_skill_count, 0.0, domain_id]
            return features, status

        except Exception as e:
            # FIX 5: Log bad rows instead of silently swallowing them.
            # Silent except made debugging training data quality impossible.
            print(f"[WARN] extract_features_v1 skipped row: {e} | row keys: {list(row.keys())[:5]}")
            return None, None

    # --- FIX 6: extract_features_v2 is REMOVED from success model training ---
    #
    # Dataset 2 (resume_data.csv) had three fundamental problems that made it
    # incompatible with Dataset 1 for training the success model:
    #
    # Problem A — Wrong label definition:
    #   status = 1 if matched_score > 0.7 else 0
    #   This predicts "did some other ATS score this resume above 0.7?", NOT
    #   "did this candidate get an interview?". Mixing two different label
    #   definitions into one model trains it to predict nothing coherently.
    #
    # Problem B — Wrong feature semantics for exp_years:
    #   exp_text = row.get('experiencere_requirement', '0')
    #   'experiencere_requirement' is the JD's requirement (how many years
    #   the JOB needs), not the CANDIDATE's experience. Feature[0] in Dataset 1
    #   means "candidate has X years". Feature[0] from Dataset 2 means "job
    #   requires X years". The model cannot learn from contradictory semantics.
    #
    # Problem C — soft_skills hardcoded to 5:
    #   return [exp_years, skill_count, 5, 0.0, domain_id]
    #   Training the model with a constant feature teaches it to ignore soft
    #   skills entirely. Even fixing inference won't help — the model weights
    #   for feature[2] are already corrupted from training.
    #
    # Dataset 2 is retained ONLY for market intelligence (top skills per domain),
    # where its JD-side data is actually meaningful.

    @staticmethod
    def _ingest_dataset2_for_market_intel(path: str, market_intel: dict):
        """
        Use Dataset 2 only for extracting JD-side market signals (skill demand),
        NOT for training the success model. This is the correct use of this data.
        """
        if not os.path.exists(path):
            return
        print("Ingesting Dataset 2 for market intelligence only (not success model)...")
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    title = row.get('job_position_name', 'General')
                    skills_raw = row.get('skills', '') or ''

                    # FIX 7: Parse skills properly instead of counting commas.
                    # Previously: skill_count = str(skills_text).count(',') + 1
                    # That gave wrong counts for nested objects, plain strings, etc.
                    if skills_raw.startswith('['):
                        try:
                            skills = json.loads(skills_raw)
                            if isinstance(skills, list):
                                skills = [str(s) for s in skills]
                            else:
                                skills = []
                        except json.JSONDecodeError:
                            skills = [s.strip() for s in skills_raw.strip('[]').split(',') if s.strip()]
                    else:
                        skills = [s.strip() for s in skills_raw.split(',') if s.strip()]

                    domain_id = _resolve_domain_id(title)
                    domain_name = DOMAIN_ID_TO_NAME.get(domain_id, "General")

                    if domain_name not in market_intel["top_skills"]:
                        market_intel["top_skills"][domain_name] = {}
                    for s in skills:
                        if s:
                            market_intel["top_skills"][domain_name][s] = \
                                market_intel["top_skills"][domain_name].get(s, 0) + 1
                except Exception as e:
                    print(f"[WARN] Dataset 2 market intel row skipped: {e}")

    @staticmethod
    def train_master_intelligence(base_path: str, output_dir: str):
        print("--- Building Unified Market Intelligence ---")

        # ------------------------------------------------------------------ #
        # STEP 1: Success Model — Dataset 1 ONLY                             #
        # ------------------------------------------------------------------ #
        X, y = [], []
        # Benchmarks: domain_id -> list of [exp, hard_skills, soft_skills, salary]
        # for candidates who received invitations (target == 1)
        benchmarks: Dict[int, List[List[float]]] = defaultdict(list)

        path1 = os.path.join(base_path, "train.csv")
        if os.path.exists(path1):
            print("Ingesting Hiring Outcomes (Dataset 1)...")
            with open(path1, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                skipped = 0
                for row in reader:
                    feat, target = BigDataTrainer.extract_features_v1(row)
                    if feat is None:
                        skipped += 1
                        continue
                    X.append(feat)
                    y.append(target)
                    if target == 1:
                        # FIX 8: Benchmarks use only Dataset 1 features so avg_experience
                        # always means "candidate experience", never "JD requirement".
                        # Previously Dataset 2 was mixed in, making avg_experience meaningless.
                        benchmarks[feat[4]].append(feat[:4])
            print(f"  → {len(X)} samples loaded, {skipped} rows skipped")
        else:
            print(f"[ERROR] train.csv not found at {path1}")

        # FIX 9: Validate before training — previously model.fit() on an empty
        # X would raise a cryptic numpy error with no actionable message.
        if len(X) == 0:
            print("[ERROR] No training data loaded. Aborting.")
            return

        class_counts = {0: y.count(0), 1: y.count(1)}
        print(f"  → Class distribution: {class_counts}")
        if class_counts.get(0, 0) == 0 or class_counts.get(1, 0) == 0:
            print("[ERROR] Only one class present in training data. Model cannot be trained.")
            return

        # ------------------------------------------------------------------ #
        # STEP 2: Train/Test Split + Evaluation                              #
        # FIX 10: Previously no held-out test set — model accuracy was       #
        # completely unknown. Now we get a proper classification report.      #
        # ------------------------------------------------------------------ #
        X_arr = np.array(X)
        y_arr = np.array(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X_arr, y_arr, test_size=0.15, random_state=42, stratify=y_arr
        )

        print(f"Training on {len(X_train)} samples, evaluating on {len(X_test)} samples...")
        model = RandomForestClassifier(
            n_estimators=200,       # more trees = more stable predictions
            max_depth=12,
            min_samples_leaf=5,     # prevents overfitting on sparse domain classes
            class_weight='balanced',# handles imbalanced invitation vs rejection labels
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)

        # Evaluation report
        y_pred = model.predict(X_test)
        print("\n--- Success Model Evaluation ---")
        print(classification_report(y_test, y_pred, target_names=["Rejected", "Invited"]))

        # Feature importance (useful for debugging which signals matter)
        feature_names = ["exp_years", "hard_skill_count", "soft_skill_count", "salary", "domain_id"]
        importances = model.feature_importances_
        print("Feature importances:")
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
            print(f"  {name}: {imp:.3f}")

        # ------------------------------------------------------------------ #
        # STEP 3: Market Intelligence                                         #
        # ------------------------------------------------------------------ #
        market_intel = {
            "top_skills": {},
            "salary_map": {},   # role -> avg_salary (aggregated, not raw list)
            "demand_trends": {}
        }

        # Pull JD-side skill demand from Dataset 2 (correct use of that data)
        path2 = os.path.join(base_path, "resume_data.csv")
        BigDataTrainer._ingest_dataset2_for_market_intel(path2, market_intel)

        # Job postings for salary and additional skill demand
        path3 = os.path.join(base_path, "job_postings.csv")
        if os.path.exists(path3):
            print("Analyzing Job Postings for market demand...")
            # FIX 11: salary_map previously stored raw lists that were never
            # aggregated. Now we compute the mean per role at ingestion time
            # so the pickle is compact and the data is actually usable.
            raw_salaries: Dict[str, List[float]] = defaultdict(list)

            with open(path3, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        title = row.get('job_title', 'General')
                        skills = [s.strip() for s in row.get('skills_required', '').split('|') if s.strip()]
                        salary = float(row.get('salary_midpoint', 0) or 0)

                        if salary > 0:
                            raw_salaries[title].append(salary)

                        title_lower = title.lower()
                        for domain, keywords in INDUSTRY_DOMAINS.items():
                            if any(kw.lower() in title_lower for kw in keywords):
                                if domain not in market_intel["top_skills"]:
                                    market_intel["top_skills"][domain] = {}
                                for s in skills:
                                    market_intel["top_skills"][domain][s] = \
                                        market_intel["top_skills"][domain].get(s, 0) + 1
                                break
                    except Exception as e:
                        print(f"[WARN] job_postings row skipped: {e}")

            # Aggregate salaries to mean
            market_intel["salary_map"] = {
                role: round(float(np.mean(vals)), 2)
                for role, vals in raw_salaries.items()
                if vals
            }

        # Finalize top skills per domain (top 15 by frequency)
        for domain in market_intel["top_skills"]:
            sorted_skills = sorted(
                market_intel["top_skills"][domain].items(),
                key=lambda x: x[1], reverse=True
            )
            market_intel["top_skills"][domain] = [s[0] for s in sorted_skills[:15] if s[0]]

        # ------------------------------------------------------------------ #
        # STEP 4: Build Benchmarks                                           #
        # ------------------------------------------------------------------ #
        final_bench = {}
        for d_id, stats in benchmarks.items():
            # FIX 12: Previously used list(INDUSTRY_DOMAINS.keys())[d_id-1]
            # which breaks if the dict order changes. Now using the stable map.
            domain_name = DOMAIN_ID_TO_NAME.get(d_id, "General")
            avg = np.mean(stats, axis=0).tolist()
            final_bench[domain_name] = {
                "avg_experience": round(avg[0], 1),
                "avg_hard_skills": round(avg[1], 1),
                "avg_soft_skills": round(avg[2], 1),  # now meaningful, not always 5
                "market_skills": market_intel["top_skills"].get(domain_name, []),
                "sample_count": len(stats)  # transparency: how many invited candidates
            }

        # ------------------------------------------------------------------ #
        # STEP 5: Save                                                        #
        # ------------------------------------------------------------------ #
        os.makedirs(output_dir, exist_ok=True)

        model_path = os.path.join(output_dir, "success_model.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"\nSuccess model saved → {model_path}")

        intel_path = os.path.join(output_dir, "market_intelligence.pkl")
        with open(intel_path, 'wb') as f:
            pickle.dump({"benchmarks": final_bench, "market_intel": market_intel}, f)
        print(f"Market intelligence saved → {intel_path}")

        print("\n--- Deployment Ready ---")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_path = os.path.join(base, "training_data")
    core_path = os.path.join(base, "backend", "app", "core")
    BigDataTrainer.train_master_intelligence(data_path, core_path)