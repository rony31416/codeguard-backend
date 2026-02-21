"""
Syntax Error Detector
=====================
Detects Python syntax errors using astroid parsing.
Uses astroid (Pylint's AST library) for more accurate parsing.

Pattern: Syntax Error
Severity: 9/10 (Critical)
Speed: <5ms
"""

import astroid
from astroid import exceptions as astroid_exceptions
from typing import Dict, Any, Optional


class SyntaxErrorDetector:
    """Detects syntax errors in Python code using astroid."""
    
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
        Check for syntax errors using astroid parsing.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - error: str (if found)
                - line: int (if found)
                - offset: int (if found)
                - text: str (if found)
        """
        try:
            self.tree = astroid.parse(self.code)
            return {
                "found": False,
                "error": None
            }
        except astroid_exceptions.AstroidSyntaxError as e:
            # Extract error details from the underlying SyntaxError
            original = e.error if hasattr(e, 'error') else e
            lineno = getattr(original, 'lineno', None)
            offset = getattr(original, 'offset', None)
            text = getattr(original, 'text', None)
            return {
                "found": True,
                "error": str(original),
                "line": lineno,
                "offset": offset,
                "text": text
            }
        except Exception as e:
            return {
                "found": True,
                "error": f"Parse error: {str(e)}",
                "line": None,
                "offset": None,
                "text": None
            }
    
    def get_partial_ast(self) -> Optional[astroid.nodes.Module]:
        """
        Try to get a partial AST even if there are syntax errors.
        
        Returns:
            astroid Module node or None
        """
        if self.tree:
            return self.tree
        
        # Try to parse by removing problematic lines
        lines = self.code.split('\n')
        for i in range(len(lines)):
            try:
                temp_lines = lines[:i] + lines[i+1:]
                temp_code = '\n'.join(temp_lines)
                return astroid.parse(temp_code)
            except:
                continue
        return None
