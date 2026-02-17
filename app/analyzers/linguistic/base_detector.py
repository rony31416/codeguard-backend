"""
Base detector class with shared utilities
"""
import ast
from typing import Set, Dict, Any, List
from abc import ABC, abstractmethod


class BaseDetector(ABC):
    """Abstract base class for all linguistic detectors"""
    
    # Common stop words
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that'
    }
    
    # Programming verbs
    ACTION_VERBS = {
        'create', 'write', 'implement', 'calculate', 'compute', 'return',
        'get', 'fetch', 'find', 'check', 'validate', 'sort', 'filter',
        'parse', 'process', 'handle', 'update', 'delete', 'add', 'remove'
    }
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        self.prompt = prompt
        self.prompt_lower = prompt.lower()
        self.code = code
        self.code_lower = code.lower()
        self.code_ast = code_ast if code_ast else self._safe_parse_ast()
    
    @abstractmethod
    def detect(self) -> Dict[str, Any]:
        """Each detector must implement this method"""
        pass
    
    def _safe_parse_ast(self) -> ast.AST:
        """Safely parse AST"""
        try:
            return ast.parse(self.code)
        except SyntaxError:
            return None
    
    def _filter_stop_words(self, words: Set[str]) -> Set[str]:
        """Remove common stop words"""
        return {w for w in words if w.lower() not in self.STOP_WORDS}
