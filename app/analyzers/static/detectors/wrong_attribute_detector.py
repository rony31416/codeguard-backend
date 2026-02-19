"""
Wrong Attribute Detector
=========================
Detects incorrect attribute access patterns (e.g., dict.key instead of dict['key']).

Pattern: Wrong Attribute
Severity: 7/10 (High)
Speed: ~5ms
"""

import re
from typing import Dict, Any, List


class WrongAttributeDetector:
    """Detects wrong attribute access patterns."""
    
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
        Detect wrong attribute access patterns.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (variable, attribute, line, description)
        """
        wrong_attrs = []
        
        # Pattern: dict.attribute instead of dict['key']
        # Common mistake: item.cost instead of item['cost']
        for i, line in enumerate(self.lines):
            dict_access = re.findall(r'(\w+)\.(\w+)', line)
            for var, attr in dict_access:
                # Common dict keys that are often accessed incorrectly
                if attr in ['cost', 'price', 'name', 'value', 'id', 'key', 'username', 'email']:
                    wrong_attrs.append({
                        "variable": var,
                        "attribute": attr,
                        "line": i + 1,
                        "description": f"Accessing '{attr}' as attribute instead of dictionary key"
                    })
        
        return {
            "found": len(wrong_attrs) > 0,
            "details": wrong_attrs
        }
