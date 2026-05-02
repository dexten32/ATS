from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.constants import DOMAIN_KEYWORDS

class SemanticMatchingService:
    @staticmethod
    def get_contextual_similarity(text1: str, text2: str) -> float:
        if not text1.strip() or not text2.strip():
            return 0.0
            
        try:
            # 1. Base TF-IDF Similarity
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            cosine_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]) * 100
            
            # 2. Domain-Specific Alignment Boost
            # Check for shared high-impact concepts
            domain_score = 0
            text1_lower = text1.lower()
            text2_lower = text2.lower()
            
            matched_domains = 0
            total_matches = 0
            
            for domain, keywords in DOMAIN_KEYWORDS.items():
                domain_matches = 0
                for kw in keywords:
                    if kw in text1_lower and kw in text2_lower:
                        domain_matches += 1
                
                if domain_matches > 0:
                    matched_domains += 1
                    total_matches += domain_matches
            
            # Boost logic: If they share architectural/security themes, increase similarity
            boost = min(30.0, (matched_domains * 5) + (total_matches * 1.5))
            
            # Combine scores (70% Cosine, 30% Domain Alignment)
            final_similarity = (cosine_sim * 0.7) + (boost * 1.0) # Boost can push it higher but we'll cap it
            
            return min(100.0, round(final_similarity, 2))
        except Exception as e:
            print(f"Semantic matching error: {e}")
            return 0.0
