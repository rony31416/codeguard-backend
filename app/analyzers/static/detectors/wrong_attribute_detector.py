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
            # Skip if line contains class definition or self (class attributes are valid)
            if 'class ' in line or 'self.' in line or 'def ' in line:
                continue
            
            dict_access = re.findall(r'(\w+)\.(\w+)', line)
            for var, attr in dict_access:
                # Skip 'self' and common class-related patterns
                if var in ['self', 'cls', 'super']:
                    continue
                
                # Skip common module/library attributes
                if var in ['os', 'sys', 'json', 'math', 'datetime', 'time', 're', 'collections']:
                    continue
                
                # Only flag if it looks like a dict operation context
                if attr in ['cost', 'price', 'value', 'key'] and ('[' in line or 'dict' in line.lower()):
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
