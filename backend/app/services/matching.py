"""
matching.py — Semantic similarity between resume text and job description text.

Architecture (three-tier, degrades gracefully):

  Tier 1 — sentence-transformers (best accuracy)
    Uses 'all-MiniLM-L6-v2', a 22M-param model that produces 384-dim embeddings.
    Cosine similarity over these embeddings captures paraphrase-level meaning:
    "built REST APIs" ~ "designed HTTP services" in ways TF-IDF never can.
    The model is cached at class level after the first load (~20ms subsequent calls).

  Tier 2 — Pre-fitted TF-IDF corpus (medium accuracy)
    A TF-IDF vectorizer fitted on a large resume+JD corpus (offline, pickled).
    IDF weights are meaningful because they come from thousands of documents,
    not just the two documents being compared. Falls back to this if Tier 1
    is unavailable.

  Tier 3 — On-the-fly TF-IDF (low accuracy, always available)
    The original approach — kept as the final fallback. IDF is essentially 0.69
    for every word (log(2/1)), so this is really just TF cosine similarity.
    Results are reliable enough to avoid crashes but should not be trusted for
    final scoring. A warning is printed so operators know which tier fired.

Domain alignment is applied as a true weighted component (not an additive boost)
after the base similarity is computed. This prevents keyword presence from
independently inflating scores for unrelated resumes.
"""

from __future__ import annotations

import os
import pickle
import warnings
from functools import lru_cache
from typing import Dict, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.constants import DOMAIN_KEYWORDS

# --------------------------------------------------------------------------- #
# Tier 1: ONNX Runtime (Production-grade, lightweight)                         #
# --------------------------------------------------------------------------- #
try:
    import onnxruntime as ort
    from tokenizers import Tokenizer
    _ONNX_AVAILABLE = True
except ImportError:
    _ONNX_AVAILABLE = False

_ONNX_SESSION: Optional[ort.InferenceSession] = None
_TOKENIZER: Optional[Tokenizer] = None

def _load_onnx_resources():
    """Load and cache the ONNX session and Tokenizer. Returns (session, tokenizer) or (None, None)."""
    global _ONNX_SESSION, _TOKENIZER
    if _ONNX_SESSION is not None and _TOKENIZER is not None:
        return _ONNX_SESSION, _TOKENIZER
    
    if not _ONNX_AVAILABLE:
        return None, None

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "model.onnx")
        tokenizer_path = os.path.join(base_dir, "models", "tokenizer.json")
        
        if os.path.exists(model_path) and os.path.exists(tokenizer_path):
            _ONNX_SESSION = ort.InferenceSession(model_path)
            _TOKENIZER = Tokenizer.from_file(tokenizer_path)
            # Ensure padding and truncation are set correctly for this model
            _TOKENIZER.enable_padding(pad_id=0, pad_token="[PAD]")
            _TOKENIZER.enable_truncation(max_length=512)
            return _ONNX_SESSION, _TOKENIZER
    except Exception as e:
        warnings.warn(f"[matching] ONNX load failed: {e}. Falling back to TF-IDF.")
    
    return None, None

def _get_onnx_embeddings(texts: list[str], session, tokenizer) -> np.ndarray:
    """Computes Mean-Pooled embeddings for a list of texts using ONNX."""
    # Note: The current ONNX model has a fixed batch size of 1.
    # We must process texts individually to avoid dimension mismatch.
    all_embeddings = []
    
    for text in texts:
        encoded = tokenizer.encode(text)
        
        # Prepare inputs for ONNX (Batch Size 1)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        
        # Run Inference
        outputs = session.run(["last_hidden_state"], {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        })
        
        # Mean Pooling: Average the token embeddings while respecting the attention mask
        token_embeddings = outputs[0]  # Shape: [1, seq_len, 384]
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float) # [1, seq_len, 1]
        
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, 1) # [1, 384]
        sum_mask = np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None) # [1, 1]
        
        embedding = sum_embeddings / sum_mask
        all_embeddings.append(embedding[0])
        
    return np.array(all_embeddings)


# --------------------------------------------------------------------------- #
# Tier 2: Pre-fitted TF-IDF vectorizer (optional, offline-trained)            #
# --------------------------------------------------------------------------- #
_CORPUS_VECTORIZER: Optional[TfidfVectorizer] = None
_CORPUS_VECTORIZER_LOADED = False  # flag so we only try to load once

def _load_corpus_vectorizer() -> Optional[TfidfVectorizer]:
    """
    Load a TF-IDF vectorizer pre-fitted on a large resume+JD corpus.
    Expected path: backend/app/core/tfidf_vectorizer.pkl

    To create this file, run offline:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import pickle, glob
        texts = [open(f).read() for f in glob.glob("training_data/*.txt")]
        vec = TfidfVectorizer(stop_words='english', max_features=50000, ngram_range=(1,2))
        vec.fit(texts)
        with open("backend/app/core/tfidf_vectorizer.pkl", "wb") as f:
            pickle.dump(vec, f)
    """
    global _CORPUS_VECTORIZER, _CORPUS_VECTORIZER_LOADED
    if _CORPUS_VECTORIZER_LOADED:
        return _CORPUS_VECTORIZER

    _CORPUS_VECTORIZER_LOADED = True
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "core", "tfidf_vectorizer.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                _CORPUS_VECTORIZER = pickle.load(f)
    except Exception as e:
        warnings.warn(f"[matching] corpus vectorizer load failed: {e}")
    return _CORPUS_VECTORIZER


# --------------------------------------------------------------------------- #
# Domain alignment component                                                   #
# --------------------------------------------------------------------------- #

def _domain_alignment_score(text1_lower: str, text2_lower: str) -> float:
    """
    Returns a 0–100 score reflecting how well the two texts share domain-specific
    vocabulary. Used as a weighted COMPONENT of the final score, not an additive
    boost on top of it.

    Key fixes vs original:
    - Keyword hits are deduplicated per domain (one keyword = one signal,
      regardless of how many times it appears in the text).
    - Score is normalised to 0–100 so it can be mixed with the base similarity
      using true percentage weights.
    - Unused variable 'domain_score' removed.
    """
    if not DOMAIN_KEYWORDS:
        return 0.0

    matched_domains = 0
    total_unique_keyword_matches = 0

    for domain, keywords in DOMAIN_KEYWORDS.items():
        # FIX: count each keyword only once (deduplicate hits)
        # Original counted raw occurrences, so "api" appearing 10× in both texts
        # contributed 10 to total_matches and dominated the boost.
        domain_hits = sum(
            1 for kw in set(keywords)     # set() deduplicates the keyword list itself
            if kw in text1_lower and kw in text2_lower
        )
        if domain_hits > 0:
            matched_domains += 1
            total_unique_keyword_matches += domain_hits

    if matched_domains == 0:
        return 0.0

    # Normalise: assume 5 matched domains and 20 keyword hits = perfect domain alignment.
    # These caps prevent one heavily-documented domain from swamping the score.
    domain_component = min(1.0, matched_domains / 5.0) * 50      # up to 50 points
    keyword_component = min(1.0, total_unique_keyword_matches / 20.0) * 50  # up to 50 points
    return round(domain_component + keyword_component, 2)


# --------------------------------------------------------------------------- #
# Tier 3: on-the-fly TF-IDF (always available, low accuracy)                  #
# --------------------------------------------------------------------------- #

# FIX: Cache the vectorizer instance (not fitted, just the object) to avoid
# recreating it on every call. The fit() is still per-call in this tier
# because the vocabulary depends on the two texts, but the object overhead
# is eliminated.
@lru_cache(maxsize=1)
def _get_fallback_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(stop_words="english", sublinear_tf=True)


def _tfidf_similarity(text1: str, text2: str, vectorizer: Optional[TfidfVectorizer] = None) -> float:
    """
    Compute cosine similarity using TF-IDF. If a pre-fitted vectorizer is
    provided (Tier 2), uses transform(); otherwise fits on the two texts (Tier 3).

    sublinear_tf=True applies log(1+tf) instead of raw tf, which reduces the
    dominance of repeated terms — the one improvement available within the
    two-document constraint.
    """
    try:
        if vectorizer is not None:
            # Tier 2: use corpus IDF weights
            matrix = vectorizer.transform([text1, text2])
        else:
            # Tier 3: fit on just these two texts
            v = _get_fallback_vectorizer()
            # lru_cache returns the same object, so we must not call fit on it
            # in a concurrent context — create a fresh one for the actual fit.
            v = TfidfVectorizer(stop_words="english", sublinear_tf=True)
            matrix = v.fit_transform([text1, text2])

        sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        return round(sim * 100, 4)
    except Exception as e:
        warnings.warn(f"[matching] TF-IDF similarity failed: {e}")
        return 0.0


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

class SemanticMatchingService:

    @staticmethod
    def get_contextual_similarity(text1: str, text2: str) -> float:
        """
        Returns a 0–100 similarity score between resume text and JD text.

        Scoring formula (all three tiers use the same blending):
            final = (base_similarity * 0.75) + (domain_alignment * 0.25)

        'base_similarity' comes from whichever tier is available.
        'domain_alignment' is always computed the same way regardless of tier.

        FIX — original formula was:
            final = (cosine_sim * 0.7) + (boost * 1.0)
        The boost was added at full weight (not 30%), so a resume with
        zero textual similarity but shared keywords could score 30+ points.
        Now domain alignment is a true 25% weighted component: a perfect
        domain match can contribute at most 25 points to the final score.
        """
        if not text1 or not text2 or not text1.strip() or not text2.strip():
            return 0.0

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # --- Domain alignment (computed once, used in all tiers) -----------
        domain_score = _domain_alignment_score(text1_lower, text2_lower)

        # --- Base similarity (tier waterfall) --------------------------------
        tier_used = "unknown"
        base_sim = 0.0

        # Tier 1: ONNX Semantic Matching
        session, tokenizer = _load_onnx_resources()
        if session is not None and tokenizer is not None:
            try:
                embeddings = _get_onnx_embeddings([text1, text2], session, tokenizer)
                # Cosine similarity via dot product of L2-normalised vectors
                norm1 = embeddings[0] / (np.linalg.norm(embeddings[0]) + 1e-10)
                norm2 = embeddings[1] / (np.linalg.norm(embeddings[1]) + 1e-10)
                base_sim = float(np.dot(norm1, norm2)) * 100
                base_sim = max(0.0, round(base_sim, 4))
                tier_used = "onnx-transformers"
            except Exception as e:
                warnings.warn(f"[matching] Tier 1 (ONNX) failed: {e}. Trying Tier 2.")
                base_sim = 0.0

        # Tier 2: corpus TF-IDF
        if tier_used == "unknown":
            corpus_vec = _load_corpus_vectorizer()
            if corpus_vec is not None:
                try:
                    base_sim = _tfidf_similarity(text1, text2, vectorizer=corpus_vec)
                    tier_used = "corpus-tfidf"
                except Exception as e:
                    warnings.warn(f"[matching] Tier 2 (corpus TF-IDF) failed: {e}. Trying Tier 3.")

        # Tier 3: on-the-fly TF-IDF (always available)
        if tier_used == "unknown":
            warnings.warn(
                "[matching] Using Tier 3 (on-the-fly TF-IDF). Similarity scores will be "
                "less accurate. Install sentence-transformers or provide a corpus vectorizer "
                "for production-quality results."
            )
            base_sim = _tfidf_similarity(text1, text2, vectorizer=None)
            tier_used = "fallback-tfidf"

        # --- Blend base similarity + domain alignment -----------------------
        # Weights: 75% semantic base + 25% domain alignment
        # Both components are 0–100, so the result is also 0–100.
        final = (base_sim * 0.75) + (domain_score * 0.25)
        return min(100.0, round(final, 2))

    @staticmethod
    def get_tier_status() -> Dict[str, bool]:
        """Utility method — call this at startup to log which tier will be used."""
        session, tokenizer = _load_onnx_resources()
        return {
            "onnx_transformers": session is not None,
            "corpus_tfidf": _load_corpus_vectorizer() is not None,
            "fallback_tfidf": True,
        }