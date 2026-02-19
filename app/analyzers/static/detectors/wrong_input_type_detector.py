"""
Wrong Input Type Detector
==========================
Detects wrong input types passed to functions (e.g., string to math.sqrt()).

Pattern: Wrong Input Type
Severity: 6/10 (Medium-High)
Speed: ~10ms
"""

import ast
from typing import Dict, Any, List


class WrongInputTypeDetector:
    """Detects wrong input types in function calls."""
    
    # Functions that expect numeric input
    NUMERIC_FUNCTIONS = {
        'sqrt', 'pow', 'log', 'exp', 'sin', 'cos', 'tan',
        'ceil', 'floor', 'round', 'abs', 'int', 'float'
    }
    
    def __init__(self, code: str, tree: ast.AST = None):
        """
        Initialize detector.
        
        Args:
            code: Source code to analyze
            tree: Pre-parsed AST (optional)
        """
        self.code = code
        self.tree = tree
        if not self.tree:
            try:
                self.tree = ast.parse(code)
            except:
                pass
    
    def detect(self) -> Dict[str, Any]:
        """
        Detect wrong input types in function calls.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (function, expected_type, actual_type, value, line, description)
        """
        wrong_types = []
        
        if not self.tree:
            return {"found": False, "details": []}
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name in self.NUMERIC_FUNCTIONS:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            wrong_types.append({
                                "function": func_name,
                                "expected_type": "numeric",
                                "actual_type": "string",
                                "value": arg.value,
                                "line": node.lineno,
                                "description": f"Passing string '{arg.value}' to numeric function {func_name}()"
                            })
        
        return {
            "found": len(wrong_types) > 0,
            "details": wrong_types
        }
