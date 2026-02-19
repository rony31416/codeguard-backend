"""
Corner Case Detector
====================
Detects missing critical edge case handling (very conservative).

Pattern: Missing Corner Case
Severity: 5/10 (Medium)
Speed: ~10ms
"""

import ast
from typing import Dict, Any, List


class CornerCaseDetector:
    """Detects missing critical edge case handling."""
    
    def __init__(self, code: str, tree: ast.AST = None):
        """
        Initialize detector.
        
        Args:
            code: Source code to analyze
            tree: Pre-parsed AST (optional)
        """
        self.code = code
        self.lines = code.split('\n')
        self.tree = tree
        if not self.tree:
            try:
                self.tree = ast.parse(code)
            except:
                pass
    
    def detect(self) -> Dict[str, Any]:
        """
        Detect missing critical corner case handling.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (line/function, description)
        """
        missing_cases = []
        
        # Only check for CRITICAL missing cases (division by zero)
        for i, line in enumerate(self.lines):
            # Skip comments and strings
            if line.strip().startswith('#'):
                continue
            
            # Check for division operations
            if '/' in line and '//' not in line and 'http://' not in line and 'https://' not in line:
                # Check wider context for protection
                context_start = max(0, i-5)
                context_end = min(len(self.lines), i+4)
                context_lines = '\n'.join(self.lines[context_start:context_end])
                
                # Look for protective checks in context
                has_protection = any([
                    '!= 0' in context_lines,
                    '== 0' in context_lines,
                    'if not numbers' in context_lines,
                    'if not items' in context_lines,
                    'if not data' in context_lines,
                    'if len(' in context_lines,
                    'ZeroDivisionError' in context_lines,
                    'try:' in context_lines and 'except' in context_lines,
                ])
                
                # Flag division by len() or count without protection
                if not has_protection:
                    if 'len(' in line or '.count(' in line:
                        missing_cases.append({
                            "line": i + 1,
                            "description": "Division operation without zero check"
                        })
        
        return {
            "found": len(missing_cases) > 0,
            "details": missing_cases
        }
