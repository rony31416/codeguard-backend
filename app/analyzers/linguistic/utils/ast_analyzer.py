"""
Deep AST analysis utilities
"""
import ast
from typing import List, Set, Dict, Any


class ASTAnalyzer:
    """Advanced AST analysis for code features"""
    
    def __init__(self, code_ast: ast.AST):
        self.ast = code_ast
    
    def get_function_names(self) -> Set[str]:
        """Extract all function definitions"""
        if not self.ast:
            return set()
        
        functions = set()
        for node in ast.walk(self.ast):
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
        return functions
    
    def get_function_calls(self) -> Set[str]:
        """Extract all function calls"""
        if not self.ast:
            return set()
        
        calls = set()
        for node in ast.walk(self.ast):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        return calls
    
    def get_imports(self) -> Set[str]:
        """Extract all imported modules"""
        if not self.ast:
            return set()
        
        imports = set()
        for node in ast.walk(self.ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                for alias in node.names:
                    imports.add(alias.name)
        return imports
    
    def has_try_except(self) -> bool:
        """Check if code has try-except blocks"""
        if not self.ast:
            return False
        
        for node in ast.walk(self.ast):
            if isinstance(node, ast.Try):
                return True
        return False
    
    def get_decorators(self) -> List[str]:
        """Extract all decorators used"""
        if not self.ast:
            return []
        
        decorators = []
        for node in ast.walk(self.ast):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(decorator.attr)
        return decorators
    
    def get_comparisons(self) -> List[Dict[str, Any]]:
        """Extract all comparison operations"""
        if not self.ast:
            return []
        
        comparisons = []
        for node in ast.walk(self.ast):
            if isinstance(node, ast.Compare):
                try:
                    # Get the comparison operators
                    ops = [op.__class__.__name__ for op in node.ops]
                    
                    # Get comparators if they're constants
                    values = []
                    for comparator in node.comparators:
                        if isinstance(comparator, ast.Constant):
                            values.append(comparator.value)
                    
                    if values:
                        comparisons.append({
                            'operators': ops,
                            'values': values
                        })
                except:
                    pass
        
        return comparisons
    
    def get_return_type_hints(self) -> Set[str]:
        """Extract return type annotations"""
        if not self.ast:
            return set()
        
        types = set()
        for node in ast.walk(self.ast):
            if isinstance(node, ast.FunctionDef):
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        types.add(node.returns.id)
                    elif isinstance(node.returns, ast.Subscript):
                        if isinstance(node.returns.value, ast.Name):
                            types.add(node.returns.value.id)
        return types
    
    def count_loops(self) -> Dict[str, int]:
        """Count different types of loops"""
        if not self.ast:
            return {'for': 0, 'while': 0}
        
        counts = {'for': 0, 'while': 0}
        for node in ast.walk(self.ast):
            if isinstance(node, ast.For):
                counts['for'] += 1
            elif isinstance(node, ast.While):
                counts['while'] += 1
        
        return counts
    
    def has_recursion(self) -> bool:
        """Check if any function calls itself"""
        if not self.ast:
            return False
        
        for node in ast.walk(self.ast):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id == func_name:
                                return True
        return False
