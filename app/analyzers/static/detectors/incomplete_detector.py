"""
Incomplete Generation Detector
===============================
Detects code that appears to be incompletely generated
(LLM was cut off or reached token limits).

Pattern: Incomplete Generation
Severity: 7/10 (High)
Speed: ~10ms
"""

import ast
import re
from typing import Dict, Any, List


class IncompleteGenerationDetector:
    """Detects incomplete code generation patterns."""
    
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
        Detect incomplete code patterns.
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (type, line, description)
        """
        incomplete = []
        
        # Pattern 1: Empty assignments
        for i, line in enumerate(self.lines):
            if re.search(r'\w+\s*=\s*$', line.strip()):
                incomplete.append({
                    "type": "incomplete_assignment",
                    "line": i + 1,
                    "description": "Assignment with no value"
                })
        
        # Pattern 2: Functions with only pass or empty bodies
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) == 0:
                        incomplete.append({
                            "type": "empty_function",
                            "line": node.lineno,
                            "description": f"Function '{node.name}' has no body"
                        })
                    elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        incomplete.append({
                            "type": "pass_only",
                            "line": node.lineno,
                            "description": f"Function '{node.name}' contains only 'pass'"
                        })
        
        # Pattern 3: Incomplete markers in comments
        for i, line in enumerate(self.lines):
            if '...' in line or 'TODO' in line or 'FIXME' in line:
                incomplete.append({
                    "type": "incomplete_marker",
                    "line": i + 1,
                    "description": "Code contains incomplete markers"
                })
            if '# missing' in line.lower() or '# stopped' in line.lower() or '# incomplete' in line.lower():
                incomplete.append({
                    "type": "incomplete_comment",
                    "line": i + 1,
                    "description": "Comment indicates incomplete code"
                })
        
        # Pattern 4: Incomplete loop logic
        if self.tree:
            incomplete.extend(self._detect_incomplete_loops())
        
        return {
            "found": len(incomplete) > 0,
            "details": incomplete
        }
    
    def _detect_incomplete_loops(self) -> List[Dict]:
        """Detect loops that appear incomplete (e.g., only one counter modified)."""
        issues = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.While):
                loop_vars = set()
                if isinstance(node.test, ast.Compare):
                    if isinstance(node.test.left, ast.Name):
                        loop_vars.add(node.test.left.id)
                    for comp in node.test.comparators:
                        if isinstance(comp, ast.Name):
                            loop_vars.add(comp.id)
                
                modified_vars = set()
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                        modified_vars.add(stmt.target.id)
                    elif isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                modified_vars.add(target.id)
                
                if len(loop_vars) >= 2 and len(modified_vars) == 1 and modified_vars.issubset(loop_vars):
                    issues.append({
                        "type": "incomplete_loop",
                        "line": node.lineno,
                        "description": f"While loop modifies only {modified_vars.pop()} but compares multiple variables"
                    })
        
        return issues
