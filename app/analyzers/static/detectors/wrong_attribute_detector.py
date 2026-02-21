"""
Wrong Attribute Detector
=========================
Detects incorrect attribute access patterns (e.g., dict.key instead of dict['key']).

Upgraded to use astroid inference instead of regex, giving semantic understanding
of whether the object being accessed is actually a dictionary.

Pattern: Wrong Attribute
Severity: 7/10 (High)
Speed: ~10ms
"""

import astroid
from astroid import nodes, exceptions as astroid_exceptions
from typing import Dict, Any, List


class WrongAttributeDetector:
    """Detects wrong attribute access patterns using astroid inference."""

    def __init__(self, code: str):
        """
        Initialize detector.

        Args:
            code: Source code to analyze
        """
        self.code = code
        self.lines = code.split('\n')
        self.tree = None
        try:
            self.tree = astroid.parse(code)
        except:
            pass

    def detect(self) -> Dict[str, Any]:
        """
        Detect wrong attribute access patterns.

        Uses astroid's type inference engine to determine whether the object
        being accessed via dot notation is actually a dictionary, which would
        require bracket notation instead.

        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (variable, attribute, line, description)
        """
        wrong_attrs = []

        if not self.tree:
            return {"found": False, "details": []}

        # Use astroid's nodes_of_class to find all attribute access nodes
        # This replaces the fragile regex approach
        for node in self.tree.nodes_of_class(nodes.Attribute):
            try:
                # Skip self/cls attribute access (class attributes are valid)
                if isinstance(node.expr, nodes.Name) and node.expr.name in ('self', 'cls', 'super'):
                    continue

                # Ask astroid to infer the actual type of the object being accessed
                inferred_types = list(node.expr.infer())
                for inferred in inferred_types:
                    # astroid can determine if this resolves to a Dict literal
                    if isinstance(inferred, nodes.Dict):
                        wrong_attrs.append({
                            "variable": node.expr.as_string(),
                            "attribute": node.attrname,
                            "line": node.lineno,
                            "description": (
                                f"Attempted to access dictionary key using dot notation"
                                f" (.{node.attrname}). Use bracket notation: "
                                f"['{node.attrname}'] instead."
                            )
                        })
                        break  # Report once per node
            except astroid_exceptions.InferenceError:
                # Inference failed - cannot determine type, skip to avoid false positives
                continue
            except Exception:
                continue

        return {
            "found": len(wrong_attrs) > 0,
            "details": wrong_attrs
        }
