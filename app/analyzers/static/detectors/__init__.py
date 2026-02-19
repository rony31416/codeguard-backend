"""
Static Analysis Detectors
==========================
Individual detector modules for specific bug patterns.
"""

from .syntax_detector import SyntaxErrorDetector
from .hallucination_detector import HallucinatedObjectDetector
from .incomplete_detector import IncompleteGenerationDetector
from .silly_mistake_detector import SillyMistakeDetector
from .wrong_attribute_detector import WrongAttributeDetector
from .wrong_input_type_detector import WrongInputTypeDetector
from .prompt_bias_detector import PromptBiasDetector
from .npc_detector import NPCDetector
from .corner_case_detector import CornerCaseDetector

__all__ = [
    'SyntaxErrorDetector',
    'HallucinatedObjectDetector',
    'IncompleteGenerationDetector',
    'SillyMistakeDetector',
    'WrongAttributeDetector',
    'WrongInputTypeDetector',
    'PromptBiasDetector',
    'NPCDetector',
    'CornerCaseDetector'
]
