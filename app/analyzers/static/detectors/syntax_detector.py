"""
Syntax Error Detector
=====================
Detects Python syntax errors using AST parsing.

Pattern: Syntax Error
Severity: 9/10 (Critical)
Speed: <5ms
"""

import ast
from typing import Dict, Any


class SyntaxErrorDetector:
    """Detects syntax errors in Python code."""
    
    def __init__(self, code: str):
        """
        Initialize detector.
        
        Args:
            code: Source code to analyze
        """
        self.code = code
        self.tree = None
    
    def detect(self) -> Dict[str, Any]:
        """
        Check for syntax errors using AST parsing.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - error: str (if found)
                - line: int (if found)
                - offset: int (if found)
                - text: str (if found)
        """
        try:
            self.tree = ast.parse(self.code)
            return {
                "found": False,
                "error": None
            }
        except SyntaxError as e:
            return {
                "found": True,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            return {
                "found": True,
                "error": f"Parse error: {str(e)}",
                "line": None,
                "offset": None,
                "text": None
            }
    
    def get_partial_ast(self) -> ast.AST:
        """
        Try to get a partial AST even if there are syntax errors.
        
        Returns:
            AST node or None
        """
        if self.tree:
            return self.tree
        
        # Try to parse by removing problematic lines
        lines = self.code.split('\n')
        for i in range(len(lines)):
            try:
                temp_lines = lines[:i] + lines[i+1:]
                temp_code = '\n'.join(temp_lines)
                return ast.parse(temp_code)
            except:
                continue
        return None
