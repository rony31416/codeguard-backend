"""
Wrong Input Type Detector
==========================
Detects wrong input types passed to functions (e.g., string to math.sqrt()).

Upgraded to use astroid instead of stdlib ast for better type resolution.
Uses nodes.Const for literal detection instead of ast.Constant.

Pattern: Wrong Input Type
Severity: 6/10 (Medium-High)
Speed: ~10ms
"""

import astroid
from astroid import nodes, exceptions as astroid_exceptions
from typing import Dict, Any, List


class WrongInputTypeDetector:
    """Detects wrong input types in function calls using astroid."""

    # Functions that expect numeric input
    NUMERIC_FUNCTIONS = {
        'sqrt', 'pow', 'log', 'exp', 'sin', 'cos', 'tan',
        'ceil', 'floor', 'round', 'abs', 'int', 'float'
    }

    def __init__(self, code: str, tree=None):
        """
        Initialize detector.

        Args:
            code: Source code to analyze
            tree: Pre-parsed astroid Module (optional)
        """
        self.code = code
        self.tree = tree
        if not self.tree:
            try:
                self.tree = astroid.parse(code)
            except:
                pass

    def detect(self) -> Dict[str, Any]:
        """
        Detect wrong input types in function calls.

        Uses astroid nodes.Const (replaces ast.Constant) and nodes.Call
        (replaces ast.Call). In astroid, node.func is nodes.Name or
        nodes.Attribute (using .name and .attrname instead of .id and .attr).

        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict]
        """
        wrong_types = []

        if not self.tree:
            return {"found": False, "details": []}

        # Use nodes_of_class(nodes.Call) instead of ast.walk + isinstance(node, ast.Call)
        for node in self.tree.nodes_of_class(nodes.Call):
            func_name = None

            # In astroid: nodes.Name.name (not .id like stdlib ast)
            if isinstance(node.func, nodes.Name):
                func_name = node.func.name
            # In astroid: nodes.Attribute.attrname (not .attr like stdlib ast)
            elif isinstance(node.func, nodes.Attribute):
                func_name = node.func.attrname

            if func_name in self.NUMERIC_FUNCTIONS:
                for arg in node.args:
                    # In astroid: nodes.Const replaces ast.Constant
                    if isinstance(arg, nodes.Const) and isinstance(arg.value, str):
                        wrong_types.append({
                            "function": func_name,
                            "expected_type": "numeric",
                            "actual_type": "string",
                            "value": arg.value,
                            "line": node.lineno,
                            "description": (
                                f"Passing string '{arg.value}' to numeric function"
                                f" {func_name}()"
                            )
                        })

        return {
            "found": len(wrong_types) > 0,
            "details": wrong_types
        }
