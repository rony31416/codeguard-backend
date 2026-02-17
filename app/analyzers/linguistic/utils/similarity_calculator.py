"""
Calculate semantic similarity between prompt and code with lazy loading
"""
from typing import Tuple
import re
import os

# Force lightweight mode on low-memory environments (Render free tier)
DISABLE_HEAVY_NLP = os.getenv("DISABLE_HEAVY_NLP", "false").lower() == "true"

# Lazy loading for heavy models
SBERT_AVAILABLE = False
SKLEARN_AVAILABLE = False

# Global model reference (loaded on first use)
sbert_model = None

# Check if libraries are installed (but don't load yet)
if not DISABLE_HEAVY_NLP:
    try:
        from sentence_transformers import SentenceTransformer, util
        SBERT_AVAILABLE = True
    except ImportError:
        pass

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        SKLEARN_AVAILABLE = True
    except ImportError:
        pass
else:
    print("⚠️  Heavy NLP disabled (DISABLE_HEAVY_NLP=true) - using keyword overlap")


class SimilarityCalculator:
    """Calculate semantic similarity using multiple methods - with lazy loading"""
    
    def __init__(self):
        self._sbert_loaded = False
    
    def _load_sbert(self):
        """Lazy load Sentence-BERT model (only on first use)"""
        global sbert_model
        if not self._sbert_loaded and sbert_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
                self._sbert_loaded = True
            except Exception as e:
                print(f"Failed to load SBERT: {e}")
                self._sbert_loaded = False
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity using best available method
        Priority: Sentence-BERT > TF-IDF > Keyword Overlap
        """
        if SBERT_AVAILABLE:
            return self._sbert_similarity(text1, text2)
        elif SKLEARN_AVAILABLE:
            return self._tfidf_similarity(text1, text2)
        else:
            return self._keyword_overlap(text1, text2)
    
    def _sbert_similarity(self, text1: str, text2: str) -> float:
        """
        Use Sentence-BERT for semantic similarity
        Best method: Understands context and meaning
        """
        try:
            self._load_sbert()
            if sbert_model:
                from sentence_transformers import util
                embedding1 = sbert_model.encode(text1, convert_to_tensor=True)
                embedding2 = sbert_model.encode(text2, convert_to_tensor=True)
                similarity = util.cos_sim(embedding1, embedding2).item()
                return round(similarity, 3)
        except Exception as e:
            print(f"SBERT failed: {e}, falling back to TF-IDF")
        return self._tfidf_similarity(text1, text2)
    
    def _tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Use TF-IDF with cosine similarity
        Good for: Keyword-based matching
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            tfidf_matrix = vectorizer.fit_transform([text1.lower(), text2.lower()])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(similarity), 3)
        except:
            return self._keyword_overlap(text1, text2)
    
    def _keyword_overlap(self, text1: str, text2: str) -> float:
        """
        Fallback: Simple keyword overlap (Jaccard similarity)
        Fast, no dependencies
        """
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        words1 = {w for w in words1 if len(w) > 3}
        words2 = {w for w in words2 if len(w) > 3}
        
        if not words1:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return round(intersection / union if union > 0 else 0.0, 3)
