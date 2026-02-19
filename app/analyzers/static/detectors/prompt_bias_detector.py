"""
Prompt Bias Detector (Static)
==============================
Detects hardcoded values from prompt examples.

Pattern: Prompt-Biased Code
Severity: Variable (3-8/10)
Speed: ~5ms
"""

import re
from typing import Dict, Any, List


class PromptBiasDetector:
    """Detects hardcoded values from examples in prompts."""
    
    def __init__(self, code: str):
        """
        Initialize detector.
        
        Args:
            code: Source code to analyze
        """
        self.code = code
        self.lines = code.split('\n')
    
    def detect(self) -> Dict[str, Any]:
        """
        Detect hardcoded example values.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (line, description)
        """
        biased_code = []
        
        # Look for example-specific patterns
        for i, line in enumerate(self.lines):
            # Pattern 1: Hardcoded example filenames with keywords
            if re.search(r'(==|!=)\s*["\'][^"\']*(demo|example|sample|test)[^"\']*["\']', line, re.IGNORECASE):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded example filename in comparison"
                })
            
            # Pattern 2: Hardcoded "Example_" patterns
            elif re.search(r'==\s*["\']Example_', line):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded check for example-specific value"
                })
        
        return {
            "found": len(biased_code) > 0,
            "details": biased_code
        }
