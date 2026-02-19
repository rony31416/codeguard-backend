"""
Hallucinated Object Detector
=============================
Detects references to undefined classes, functions, or variables
that may have been "hallucinated" by LLMs.

Pattern: Hallucinated Object
Severity: 8/10 (High)
Speed: ~10ms
"""

import ast
import re
from typing import Dict, Any, List, Set


class HallucinatedObjectDetector:
    """Detects undefined objects that LLMs sometimes invent."""
    
    # Hardcoded Python built-ins (reliable across platforms)
    BUILTINS = {
        # Built-in functions
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
        # Built-in constants
        'False', 'True', 'None', 'NotImplemented', 'Ellipsis', '__debug__',
        # Dunder variables (always available in Python)
        '__name__', '__main__', '__file__', '__doc__', '__package__',
        '__loader__', '__spec__', '__annotations__', '__builtins__',
        '__cached__', '__dict__', '__class__',
    }
    
    COMMON_MODULES = {
        'math', 'os', 'sys', 're', 'json', 'time', 'datetime',
        'random', 'collections', 'itertools', 'functools', 'numpy', 'pandas',
        'logging', 'pathlib', 'io', 'typing', 'copy', 'pickle'
    }
    
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
        Detect potentially hallucinated objects.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - objects: List[Dict] (name, line, type)
        """
        hallucinated = []
        
        # Pattern 1: Class instantiations (CamelCase names)
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
        
        # Pattern 2: AST-based analysis
        if self.tree:
            defined_names = self._get_defined_names()
            used_names = self._get_used_names()
            
            for name in used_names:
                if name not in defined_names and name not in self.BUILTINS and name not in self.COMMON_MODULES:
                    if not any(h['name'] == name for h in hallucinated):
                        hallucinated.append({
                            "name": name,
                            "line": None,
                            "type": "variable"
                        })
        
        return {
            "found": len(hallucinated) > 0,
            "objects": hallucinated
        }
    
    def _get_defined_names(self) -> Set[str]:
        """Extract all defined names from AST."""
        defined = set()
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
                # Add parameters
                for arg in node.args.args:
                    defined.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    defined.add(arg.arg)
                if node.args.vararg:
                    defined.add(node.args.vararg.arg)
                if node.args.kwarg:
                    defined.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
            # Loop variables
            elif isinstance(node, ast.For):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            defined.add(elt.id)
            # With statement variables
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        defined.add(item.optional_vars.id)
            # Comprehension variables
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for generator in node.generators:
                    if isinstance(generator.target, ast.Name):
                        defined.add(generator.target.id)
                    elif isinstance(generator.target, ast.Tuple):
                        for elt in generator.target.elts:
                            if isinstance(elt, ast.Name):
                                defined.add(elt.id)
            # Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    defined.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    defined.add(name)
        
        return defined
    
    def _get_used_names(self) -> Set[str]:
        """Extract all used names from AST."""
        used = set()
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        
        return used
