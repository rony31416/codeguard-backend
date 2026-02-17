"""
Stage 3: Linguistic Analysis - Compares prompt intent with code implementation

Main orchestrator for all linguistic detectors:
1. NPC (Non-Prompted Consideration) - unrequested features
2. Prompt-Biased Code - hardcoded example values
3. Missing Features - features requested but not implemented
4. Misinterpretation - fundamental intent mismatch
"""

import ast
from typing import Dict, Any

# Import specialized detectors
from .linguistic.npc_detector import NPCDetector
from .linguistic.prompt_bias_detector import PromptBiasDetector
from .linguistic.missing_feature_detector import MissingFeatureDetector
from .linguistic.misinterpretation_detector import MisinterpretationDetector
from .linguistic.utils.similarity_calculator import SimilarityCalculator


class LinguisticAnalyzer:
    """
    Stage 3: Linguistic Analysis Orchestrator
    Coordinates all specialized detectors with NLP support
    """
    
    def __init__(self, prompt: str, code: str):
        self.prompt = prompt
        self.code = code
        self.code_ast = self._safe_parse_ast()
        
        # Initialize similarity calculator
        self.similarity_calculator = SimilarityCalculator()
        
        # Initialize all detectors
        self.npc_detector = NPCDetector(prompt, code, self.code_ast)
        self.prompt_bias_detector = PromptBiasDetector(prompt, code, self.code_ast)
        self.missing_feature_detector = MissingFeatureDetector(prompt, code, self.code_ast)
        self.misinterpretation_detector = MisinterpretationDetector(prompt, code, self.code_ast)
    
    def analyze(self) -> Dict[str, Any]:
        """Run all linguistic analyses"""
        results = {
            "npc": self.npc_detector.detect(),
            "prompt_biased": self.prompt_bias_detector.detect(),
            "missing_features": self.missing_feature_detector.detect(),
            "misinterpretation": self.misinterpretation_detector.detect(),
            "intent_match_score": self.similarity_calculator.calculate_similarity(
                self.prompt, self.code
            )
        }
        return results
    
    def _safe_parse_ast(self) -> ast.AST:
        """Safely parse AST"""
        try:
            return ast.parse(self.code)
        except SyntaxError:
            return None
