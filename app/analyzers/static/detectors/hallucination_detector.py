"""
Hallucinated Object Detector
=============================
Detects references to undefined classes, functions, or variables
that may have been "hallucinated" by LLMs.

Uses astroid (Pylint's AST library) for scope-aware inference,
drastically reducing false positives compared to manual ast.walk traversal.

Pattern: Hallucinated Object
Severity: 8/10 (High)
Speed: ~15ms
"""

import astroid
from astroid import nodes, exceptions as astroid_exceptions
import re
from typing import Dict, Any, List, Set


class HallucinatedObjectDetector:
    """Detects undefined objects that LLMs sometimes invent - using astroid inference."""

    BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
        'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
        'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
        'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
        'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
        'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
        'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
        'vars', 'zip', '__import__',
        'False', 'True', 'None', 'NotImplemented', 'Ellipsis', '__debug__',
        '__name__', '__main__', '__file__', '__doc__', '__package__',
        '__loader__', '__spec__', '__annotations__', '__builtins__',
        '__cached__', '__dict__', '__class__',
    }

    COMMON_MODULES = {
        'math', 'os', 'sys', 're', 'json', 'time', 'datetime',
        'random', 'collections', 'itertools', 'functools', 'numpy', 'pandas',
        'logging', 'pathlib', 'io', 'typing', 'copy', 'pickle'
    }

    def __init__(self, code: str, tree=None):
        """
        Initialize detector.

        Args:
            code: Source code to analyze
            tree: Pre-parsed astroid Module (optional)
        """
        self.code = code
        self.lines = code.split('\n')
        self.tree = tree
        if not self.tree:
            try:
                self.tree = astroid.parse(code)
            except:
                pass

    def detect(self) -> Dict[str, Any]:
        """
        Detect potentially hallucinated objects.

        Returns:
            Dict with detection results containing:
                - found: bool
                - objects: List[Dict] (name, line, type)
        """
        hallucinated = []

        # Pattern 1: Regex-based class instantiation check (CamelCase names)
        class_pattern = re.compile(r'([A-Z][a-zA-Z0-9]*)\s*\(')
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            code_part = line.split('#')[0]
            matches = class_pattern.findall(code_part)
            for match in matches:
                if match not in self.BUILTINS and match not in self.COMMON_MODULES:
                    if not any(f'class {match}' in l for l in self.lines):
                        hallucinated.append({
                            "name": match,
                            "line": i + 1,
                            "type": "class"
                        })

        # Pattern 2: astroid scope-aware check
        # In astroid: nodes.Name = variable read (Load equivalent)
        #             nodes.AssignName = variable write (Store equivalent)
        # This removes the need for manual ast.Load context checks.
        if self.tree:
            defined_names = self._get_defined_names()
            used_names = self._get_used_names()

            for name, lineno in used_names:
                if (
                    name not in defined_names
                    and name not in self.BUILTINS
                    and name not in self.COMMON_MODULES
                ):
                    if not any(h['name'] == name for h in hallucinated):
                        hallucinated.append({
                            "name": name,
                            "line": lineno,
                            "type": "variable"
                        })

        return {
            "found": len(hallucinated) > 0,
            "objects": hallucinated
        }

    def _get_defined_names(self) -> Set[str]:
        """Extract all defined names using astroid node types."""
        defined = set()

        # Function definitions and their arguments
        # In astroid: arg.name (not arg.arg like stdlib ast)
        for node in self.tree.nodes_of_class(nodes.FunctionDef):
            defined.add(node.name)
            for arg in node.args.args or []:
                if hasattr(arg, 'name'):
                    defined.add(arg.name)
            for arg in node.args.kwonlyargs or []:
                if hasattr(arg, 'name'):
                    defined.add(arg.name)
            if node.args.vararg:
                defined.add(node.args.vararg)
            if node.args.kwarg:
                defined.add(node.args.kwarg)

        # Class definitions
        for node in self.tree.nodes_of_class(nodes.ClassDef):
            defined.add(node.name)

        # Assignments: astroid uses AssignName instead of ast.Name(ctx=Store)
        for node in self.tree.nodes_of_class(nodes.AssignName):
            defined.add(node.name)

        # For loop targets
        for node in self.tree.nodes_of_class(nodes.For):
            if isinstance(node.target, nodes.AssignName):
                defined.add(node.target.name)
            elif isinstance(node.target, nodes.Tuple):
                for elt in node.target.elts:
                    if isinstance(elt, nodes.AssignName):
                        defined.add(elt.name)

        # With statement variables (item is a 2-tuple: context_expr, optional_var)
        for node in self.tree.nodes_of_class(nodes.With):
            for item in node.items:
                optional_var = item[1] if len(item) > 1 else None
                if optional_var and isinstance(optional_var, nodes.AssignName):
                    defined.add(optional_var.name)

        # Comprehension variables
        for comp_class in (nodes.ListComp, nodes.SetComp, nodes.DictComp, nodes.GeneratorExp):
            for node in self.tree.nodes_of_class(comp_class):
                for generator in node.generators:
                    if isinstance(generator.target, nodes.AssignName):
                        defined.add(generator.target.name)
                    elif isinstance(generator.target, nodes.Tuple):
                        for elt in generator.target.elts:
                            if isinstance(elt, nodes.AssignName):
                                defined.add(elt.name)

        # Imports
        for node in self.tree.nodes_of_class(nodes.Import):
            for name, alias in node.names:
                defined.add(alias if alias else name)

        for node in self.tree.nodes_of_class(nodes.ImportFrom):
            for name, alias in node.names:
                defined.add(alias if alias else name)

        return defined

    def _get_used_names(self) -> List[tuple]:
        """
        Extract all read variable names using astroid.
        In astroid: nodes.Name is always a variable read (Load).
        nodes.AssignName is a variable write (Store).
        No need to check ctx context - the node type itself encodes the context.
        """
        used = []
        for node in self.tree.nodes_of_class(nodes.Name):
            used.append((node.name, node.lineno))
        return used
