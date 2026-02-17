"""
Enhanced keyword extraction using multiple NLP techniques with lazy loading
"""
import re
import os
from typing import Set, List
from collections import Counter

# Force lightweight mode on low-memory environments (Render free tier)
DISABLE_HEAVY_NLP = os.getenv("DISABLE_HEAVY_NLP", "false").lower() == "true"

# Lazy loading for heavy models
SPACY_AVAILABLE = False
KEYBERT_AVAILABLE = False
NLTK_AVAILABLE = False

# Global references (loaded on first use)
nlp = None
keybert_model = None

# Check if libraries are installed (but don't load yet)
if not DISABLE_HEAVY_NLP:
    try:
        import spacy
        SPACY_AVAILABLE = True
    except ImportError:
        pass

    try:
        from keybert import KeyBERT
        KEYBERT_AVAILABLE = True
    except ImportError:
        pass

    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        from nltk.stem import WordNetLemmatizer
        NLTK_AVAILABLE = True
    except ImportError:
        pass
else:
    print("⚠️  Heavy NLP disabled (DISABLE_HEAVY_NLP=true) - using regex fallback")


class KeywordExtractor:
    """Multi-strategy keyword extraction - with lazy loading to avoid slowdown"""
    
    def __init__(self):
        self.stop_words = self._get_stop_words()
        self.lemmatizer = None  # Lazy load when needed
        self._spacy_loaded = False
        self._keybert_loaded = False
    
    def _get_stop_words(self) -> Set[str]:
        """Get stop words from NLTK or fallback"""
        if NLTK_AVAILABLE:
            try:
                from nltk.corpus import stopwords
                return set(stopwords.words('english'))
            except:
                pass
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are'
        }
    
    def extract_from_prompt(self, prompt: str, top_n: int = 20) -> Set[str]:
        """
        Extract keywords from prompt using best available method
        Priority: KeyBERT > spaCy > NLTK > Regex
        """
        # Try KeyBERT first (best for keyword extraction)
        if KEYBERT_AVAILABLE:
            return self._extract_with_keybert(prompt, top_n)
        
        # Fall back to spaCy
        elif SPACY_AVAILABLE:
            return self._extract_with_spacy(prompt)
        
        # Fall back to NLTK
        elif NLTK_AVAILABLE:
            return self._extract_with_nltk(prompt)
        
        # Last resort: regex
        else:
            return self._extract_with_regex(prompt)
    
    def _load_keybert(self):
        """Lazy load KeyBERT model (only on first use)"""
        global keybert_model
        if not self._keybert_loaded and keybert_model is None:
            try:
                from keybert import KeyBERT
                keybert_model = KeyBERT('all-MiniLM-L6-v2')
                self._keybert_loaded = True
            except Exception as e:
                print(f"Failed to load KeyBERT: {e}")
                self._keybert_loaded = False
    
    def _extract_with_keybert(self, text: str, top_n: int = 20) -> Set[str]:
        """
        Use KeyBERT for state-of-the-art keyword extraction
        Best for: Finding most relevant keywords automatically
        """
        try:
            self._load_keybert()
            if keybert_model:
                # Simple extraction (fast, no maxsum algorithm)
                keywords = keybert_model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 2),
                    stop_words='english',
                    top_n=top_n
                )
                return {kw[0].lower() for kw in keywords}
        except Exception as e:
            print(f"KeyBERT extraction failed: {e}")
        return self._extract_with_spacy(text)
    
    def _load_spacy(self):
        """Lazy load spaCy model (only on first use)"""
        global nlp
        if not self._spacy_loaded and nlp is None:
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                self._spacy_loaded = True
            except Exception as e:
                print(f"Failed to load spaCy: {e}")
                self._spacy_loaded = False
    
    def _extract_with_spacy(self, text: str) -> Set[str]:
        """
        Use spaCy for linguistic analysis
        Best for: Part-of-speech tagging, named entities
        """
        try:
            self._load_spacy()
            if nlp:
                doc = nlp(text.lower())
                keywords = set()
                
                for token in doc:
                    if token.pos_ == "VERB" and not token.is_stop:
                        keywords.add(token.lemma_)
                
                for token in doc:
                    if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 3:
                        keywords.add(token.lemma_)
                
                for ent in doc.ents:
                    keywords.add(ent.text.lower())
                
                for token in doc:
                    if token.pos_ == "ADJ" and len(token.text) > 4:
                        keywords.add(token.lemma_)
                
                return keywords
        except Exception as e:
            print(f"spaCy extraction failed: {e}")
        return self._extract_with_nltk(text)
    
    def _extract_with_nltk(self, text: str) -> Set[str]:
        """
        Use NLTK for traditional NLP
        Best for: Research, custom algorithms
        """
        if not NLTK_AVAILABLE:
            return self._extract_with_regex(text)
        
        try:
            if self.lemmatizer is None:
                from nltk.stem import WordNetLemmatizer
                self.lemmatizer = WordNetLemmatizer()
                try:
                    import nltk
                    nltk.data.find('corpora/stopwords')
                    nltk.data.find('tokenizers/punkt_tab')
                    nltk.data.find('corpora/wordnet')
                except LookupError:
                    nltk.download('stopwords', quiet=True)
                    nltk.download('punkt_tab', quiet=True)
                    nltk.download('punkt', quiet=True)
                    nltk.download('wordnet', quiet=True)
            
            from nltk.tokenize import word_tokenize
            tokens = word_tokenize(text.lower())
            
            keywords = {
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if token.isalpha() and len(token) > 3 and token not in self.stop_words
            }
            
            try:
                import nltk
                pos_tags = nltk.pos_tag(tokens)
                filtered_keywords = {
                    self.lemmatizer.lemmatize(word)
                    for word, pos in pos_tags
                    if pos.startswith(('NN', 'VB', 'JJ')) and word in keywords
                }
                return filtered_keywords if filtered_keywords else keywords
            except:
                return keywords
        except Exception as e:
            print(f"NLTK extraction failed: {e}, falling back to regex")
            return self._extract_with_regex(text)
    
    def _extract_with_regex(self, text: str) -> Set[str]:
        """
        Fallback: Simple regex extraction (fast, no dependencies)
        Best for: When no NLP library available
        """
        words = re.findall(r'\b[a-z]+\b', text.lower())
        keywords = {
            w for w in words 
            if len(w) > 3 and w not in self.stop_words
        }
        return keywords
    
    def extract_action_verbs(self, text: str) -> Set[str]:
        """Extract programming action verbs specifically"""
        action_verbs = {
            'create', 'write', 'implement', 'calculate', 'compute', 'return',
            'get', 'fetch', 'retrieve', 'find', 'search', 'check', 'validate',
            'sort', 'filter', 'parse', 'process', 'handle', 'convert', 'format'
        }
        
        if SPACY_AVAILABLE:
            self._load_spacy()
            if nlp:
                doc = nlp(text.lower())
                found_verbs = {token.lemma_ for token in doc if token.pos_ == "VERB"}
                return found_verbs & action_verbs
        
        return {verb for verb in action_verbs if verb in text.lower()}
    
    def extract_data_types(self, text: str) -> Set[str]:
        """Extract mentioned data types"""
        data_types = {
            'list', 'dict', 'dictionary', 'string', 'str', 'int', 'integer',
            'float', 'number', 'tuple', 'array', 'set', 'bool', 'boolean'
        }
        return {dt for dt in data_types if dt in text.lower()}
