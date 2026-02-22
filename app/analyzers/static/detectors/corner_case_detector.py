"""
Corner Case Detector
====================
Detects missing critical edge case handling.

Pattern: Missing Corner Case
Severity: 5/10 (Medium)
Speed: ~10ms
"""

import astroid
from astroid import nodes, exceptions as astroid_exceptions
from typing import Dict, Any, List, Optional


class CornerCaseDetector:
    """Detects missing critical edge case handling using astroid."""

    def __init__(self, code: str, tree=None):
        self.code = code
        self.lines = code.split('\n')
        self.tree = tree
        if not self.tree:
            try:
                self.tree = astroid.parse(code)
            except Exception:
                pass

    def detect(self) -> Dict[str, Any]:
        """
        Detect missing critical corner case handling.

        Checks:
          - Division by any non-literal variable without a zero-guard or
            try/except ZeroDivisionError in the enclosing scope.

        Returns:
            Dict with detection results:
                - found: bool
                - details: List[Dict] (line, description)
        """
        if not self.tree:
            return {"found": False, "details": []}

        missing_cases = []

        for node in self.tree.nodes_of_class(nodes.BinOp):
            # Only care about true division '/'
            if node.op != '/':
                continue

            right = node.right

            # Division by a non-zero literal is safe — skip it
            if isinstance(right, nodes.Const):
                # e.g. x / 2  — safe
                # Note: x / 0 would be caught by silly_mistake_detector
                continue

            # Right side is a variable / expression — potentially zero
            scope = node.scope()
            if not self._has_zero_protection(scope, right):
                missing_cases.append({
                    "line": node.lineno,
                    "description": (
                        f"Division by variable '{self._name(right)}' without "
                        f"zero check — may raise ZeroDivisionError"
                    ),
                })

        return {
            "found": len(missing_cases) > 0,
            "details": missing_cases,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _name(node) -> str:
        """Return a readable name for the divisor node."""
        if isinstance(node, nodes.Name):
            return node.name
        if isinstance(node, nodes.Call):
            if isinstance(node.func, nodes.Name):
                return node.func.name + "()"
            if isinstance(node.func, nodes.Attribute):
                return node.func.attrname + "()"
        return "<expr>"

    def _has_zero_protection(self, scope, divisor_node) -> bool:
        """Return True if the scope contains a zero-guard for the divisor."""
        divisor_name: Optional[str] = None
        if isinstance(divisor_node, nodes.Name):
            divisor_name = divisor_node.name

        # 1. try/except ZeroDivisionError  OR  bare except
        for handler in scope.nodes_of_class(nodes.ExceptHandler):
            if handler.type is None:
                # bare except — conservative: counts as protection
                return True
            exc_names = []
            if isinstance(handler.type, nodes.Name):
                exc_names = [handler.type.name]
            elif isinstance(handler.type, nodes.Tuple):
                exc_names = [
                    e.name for e in handler.type.elts
                    if isinstance(e, nodes.Name)
                ]
            if "ZeroDivisionError" in exc_names or "Exception" in exc_names:
                return True

        # 2. Zero comparison: if b == 0 / if b != 0 / if 0 == b / if b
        if divisor_name:
            for if_node in scope.nodes_of_class(nodes.If):
                if self._test_guards_zero(if_node.test, divisor_name):
                    return True

        return False

    @staticmethod
    def _test_guards_zero(test_node, name: str) -> bool:
        """Return True if the test node checks `name` against zero."""
        # if name  (truthy — guards falsy/zero)
        if isinstance(test_node, nodes.Name) and test_node.name == name:
            return True

        # if not name
        if (
            isinstance(test_node, nodes.UnaryOp)
            and test_node.op == "not"
            and isinstance(test_node.operand, nodes.Name)
            and test_node.operand.name == name
        ):
            return True

        # if name == 0  /  if name != 0  /  if 0 == name  /  if 0 != name
        if isinstance(test_node, nodes.Compare):
            left = test_node.left
            for op, comparator in test_node.ops:
                # name compared to 0
                if (
                    isinstance(left, nodes.Name)
                    and left.name == name
                    and isinstance(comparator, nodes.Const)
                    and comparator.value == 0
                ):
                    return True
                # 0 compared to name
                if (
                    isinstance(left, nodes.Const)
                    and left.value == 0
                    and isinstance(comparator, nodes.Name)
                    and comparator.name == name
                ):
                    return True

        return False
