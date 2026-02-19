"""
Silly Mistake Detector
======================
Detects non-human coding patterns like identical if/else branches,
reversed operands, or illogical operations.

Pattern: Silly Mistake
Severity: 6/10 (Medium-High)
Speed: ~10ms
"""

import ast
import re
from typing import Dict, Any, List


class SillyMistakeDetector:
    """Detects non-human coding patterns and silly mistakes."""
    
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
        Detect silly mistakes and non-human patterns.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (type, line, description)
        """
        mistakes = []
        
        # Pattern 1: Reversed operands in calculations
        for i, line in enumerate(self.lines):
            if re.search(r'(discount|rate|percent)\s*-\s*(\w+)', line):
                mistakes.append({
                    "type": "reversed_operands",
                    "line": i + 1,
                    "description": "Suspicious operation: possible reversed operands"
                })
        
        # Pattern 2: String concatenation with non-string
        for i, line in enumerate(self.lines):
            if re.search(r'["\'].*["\']\s*\+\s*\w+(?!\()', line):
                if re.search(r'(rate|price|count|value|num)', line):
                    mistakes.append({
                        "type": "type_concatenation",
                        "line": i + 1,
                        "description": "Attempting string concatenation with likely numeric value"
                    })
        
        # Pattern 3: Identical if/else branches (AST-based)
        if self.tree:
            mistakes.extend(self._detect_identical_branches())
        
        return {
            "found": len(mistakes) > 0,
            "details": mistakes
        }
    
    def _detect_identical_branches(self) -> List[Dict]:
        """Detect if/else statements with identical code in both branches."""
        issues = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.If):
                if node.orelse and len(node.orelse) > 0:
                    try:
                        if_body_dump = [ast.dump(stmt) for stmt in node.body]
                        
                        # Skip elif chains
                        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                            continue
                        
                        else_body_dump = [ast.dump(stmt) for stmt in node.orelse]
                        
                        if if_body_dump == else_body_dump and len(if_body_dump) > 0:
                            issues.append({
                                "type": "identical_branches",
                                "line": node.lineno,
                                "description": "If and else branches contain identical code"
                            })
                    except:
                        continue
        
        return issues
