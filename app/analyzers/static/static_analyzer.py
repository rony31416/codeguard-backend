"""
Static Analyzer - Orchestrator
===============================
Coordinates all static analysis detectors.

This is the main entry point for static analysis.
It orchestrates individual detectors and aggregates results.
"""

import astroid
from typing import Dict, Any

from .detectors.syntax_detector import SyntaxErrorDetector
from .detectors.hallucination_detector import HallucinatedObjectDetector
from .detectors.incomplete_detector import IncompleteGenerationDetector
from .detectors.silly_mistake_detector import SillyMistakeDetector
from .detectors.wrong_attribute_detector import WrongAttributeDetector
from .detectors.wrong_input_type_detector import WrongInputTypeDetector
from .detectors.prompt_bias_detector import PromptBiasDetector
from .detectors.npc_detector import NPCDetector
from .detectors.corner_case_detector import CornerCaseDetector


class StaticAnalyzer:
    """
    Orchestrates all static analysis detectors.
    
    Detectors run in parallel and results are aggregated.
    Fault-tolerant: individual detector failures don't crash the analysis.
    """
    
    def __init__(self, code: str):
        """
        Initialize static analyzer.
        
        Args:
            code: Source code to analyze
        """
        self.code = code
        self.lines = code.split('\n')
        self.tree = None
        
        # Try to parse once for all detectors
        syntax_detector = SyntaxErrorDetector(code)
        syntax_result = syntax_detector.detect()
        
        if not syntax_result.get('found'):
            self.tree = syntax_detector.tree
        else:
            # Get partial AST for use by other detectors
            self.tree = syntax_detector.get_partial_ast()
    
    def analyze(self) -> Dict[str, Any]:
        """
        Run all static analysis checks.
        
        Returns:
            Dict containing results from all detectors:
                - syntax_error: {...}
                - hallucinated_objects: {...}
                - incomplete_generation: {...}
                - silly_mistakes: {...}
                - wrong_attribute: {...}
                - wrong_input_type: {...}
                - prompt_biased: {...}
                - npc: {...}
                - missing_corner_case: {...}
        """
        results = {
            "syntax_error": self._run_detector(SyntaxErrorDetector, self.code),
            "hallucinated_objects": self._run_detector(HallucinatedObjectDetector, self.code, self.tree),
            "incomplete_generation": self._run_detector(IncompleteGenerationDetector, self.code, self.tree),
            "silly_mistakes": self._run_detector(SillyMistakeDetector, self.code, self.tree),
            "wrong_attribute": self._run_detector(WrongAttributeDetector, self.code),
            "wrong_input_type": self._run_detector(WrongInputTypeDetector, self.code, self.tree),
            "prompt_biased": self._run_detector(PromptBiasDetector, self.code),
            "npc": self._run_detector(NPCDetector, self.code),
            "missing_corner_case": self._run_detector(CornerCaseDetector, self.code, self.tree),
        }
        
        return results
    
    def _run_detector(self, detector_class, *args):
        """
        Run a detector with fault tolerance.
        
        Args:
            detector_class: Detector class to instantiate
            *args: Arguments to pass to detector
        
        Returns:
            Detection results or error dict
        """
        try:
            detector = detector_class(*args)
            return detector.detect()
        except Exception as e:
            return {
                "found": False,
                "error": f"{detector_class.__name__} failed: {str(e)}"
            }


if __name__ == "__main__":
    """Quick test"""
    test_code = """
def calculate_total(items)  # missing colon
    total = 0
    for item in items:
        total += item
    return total
"""
    
    analyzer = StaticAnalyzer(test_code)
    results = analyzer.analyze()
    
    print("Static Analysis Results:")
    print("=" * 60)
    
    for pattern, result in results.items():
        if result.get('found'):
            print(f"\n✗ {pattern.upper().replace('_', ' ')}")
            if 'details' in result:
                print(f"  Issues: {len(result['details'])}")
            elif 'objects' in result:
                print(f"  Objects: {len(result['objects'])}")
            elif 'error' in result:
                print(f"  Error: {result['error']}")
    
    print("\n" + "=" * 60)
