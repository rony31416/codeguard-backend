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
        self.in_main_block = False
        self._identify_main_block()
    
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
            # Skip lines inside if __name__ == "__main__": block (demo/sample data is expected there)
            if self._is_in_main_block(i):
                continue
            
            # Pattern 1: Hardcoded example filenames with keywords IN LOGIC (not demo data)
            if re.search(r"(==|!=)\s*[\"'][^\"']*(demo|example|sample|test)[^\"']*[\"']", line, re.IGNORECASE):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded example filename in comparison"
                })
            
            # Pattern 2: Hardcoded "Example_" patterns
            elif re.search(r"==\s*[\"']Example_", line):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded check for example-specific value"
                })
        
        return {
            "found": len(biased_code) > 0,
            "details": biased_code
        }
    
    def _identify_main_block(self):
        """Identify the range of if __name__ == '__main__': block."""
        self.main_block_start = None
        self.main_block_end = None
        
        for i, line in enumerate(self.lines):
            if '__name__' in line and '__main__' in line:
                self.main_block_start = i
            elif self.main_block_start is not None and self.main_block_end is None:
                # Find the end of the main block (dedented or end of file)
                if line and not line[0].isspace() and line.strip() != '':
                    self.main_block_end = i
                    break
        
        if self.main_block_start is not None and self.main_block_end is None:
            self.main_block_end = len(self.lines)
    
    def _is_in_main_block(self, line_index: int) -> bool:
        """Check if line is inside if __name__ == '__main__': block."""
        if self.main_block_start is None:
            return False
        return self.main_block_start <= line_index < self.main_block_end
