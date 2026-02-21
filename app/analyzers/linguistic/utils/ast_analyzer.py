"""
Deep AST analysis utilities - upgraded to use astroid.

astroid differences from stdlib ast:
- nodes_of_class(NodeType) instead of ast.walk(tree)
- nodes.Name.name instead of ast.Name.id
- nodes.Attribute.attrname instead of ast.Attribute.attr
- nodes.Const instead of ast.Constant
- nodes.AssignName for variable assignments (ast used Name with Store ctx)
"""
import astroid
from astroid import nodes, exceptions as astroid_exceptions
from typing import List, Set, Dict, Any


class ASTAnalyzer:
    """Advanced AST analysis for code features using astroid"""

    def __init__(self, code_ast):
        """Accept an astroid Module or None."""
        self.ast = code_ast

    def get_function_names(self) -> Set[str]:
        """Extract all function definitions"""
        if not self.ast:
            return set()

        functions = set()
        # nodes.FunctionDef replaces ast.FunctionDef
        for node in self.ast.nodes_of_class(nodes.FunctionDef):
            functions.add(node.name)
        return functions

    def get_function_calls(self) -> Set[str]:
        """Extract all function calls"""
        if not self.ast:
            return set()

        calls = set()
        # nodes.Call replaces ast.Call
        for node in self.ast.nodes_of_class(nodes.Call):
            # nodes.Name.name replaces ast.Name.id
            if isinstance(node.func, nodes.Name):
                calls.add(node.func.name)
            # nodes.Attribute.attrname replaces ast.Attribute.attr
            elif isinstance(node.func, nodes.Attribute):
                calls.add(node.func.attrname)
        return calls

    def get_imports(self) -> Set[str]:
        """Extract all imported modules"""
        if not self.ast:
            return set()

        imports = set()
        for node in self.ast.nodes_of_class(nodes.Import):
            for name, alias in node.names:
                imports.add(name)
        for node in self.ast.nodes_of_class(nodes.ImportFrom):
            if node.modname:
                imports.add(node.modname)
            for name, alias in node.names:
                imports.add(name)
        return imports

    def has_try_except(self) -> bool:
        """Check if code has try-except blocks"""
        if not self.ast:
            return False

        # nodes.Try replaces ast.Try
        for _ in self.ast.nodes_of_class(nodes.Try):
            return True
        return False

    def get_decorators(self) -> List[str]:
        """Extract all decorators used"""
        if not self.ast:
            return []

        decorators = []
        for node in self.ast.nodes_of_class(nodes.FunctionDef):
            for decorator in node.decorators.nodes if node.decorators else []:
                if isinstance(decorator, nodes.Name):
                    decorators.append(decorator.name)
                elif isinstance(decorator, nodes.Attribute):
                    decorators.append(decorator.attrname)
        return decorators

    def get_comparisons(self) -> List[Dict[str, Any]]:
        """Extract all comparison operations"""
        if not self.ast:
            return []

        comparisons = []
        # nodes.Compare replaces ast.Compare
        for node in self.ast.nodes_of_class(nodes.Compare):
            try:
                ops = [op.__class__.__name__ for op in node.ops]

                values = []
                for comparator in node.comparators:
                    # nodes.Const replaces ast.Constant
                    if isinstance(comparator, nodes.Const):
                        values.append(comparator.value)

                if values:
                    comparisons.append({
                        'operators': ops,
                        'values': values
                    })
            except Exception:
                pass

        return comparisons

    def get_return_type_hints(self) -> Set[str]:
        """Extract return type annotations"""
        if not self.ast:
            return set()

        types = set()
        for node in self.ast.nodes_of_class(nodes.FunctionDef):
            if node.returns:
                if isinstance(node.returns, nodes.Name):
                    types.add(node.returns.name)
                elif isinstance(node.returns, nodes.Subscript):
                    if isinstance(node.returns.value, nodes.Name):
                        types.add(node.returns.value.name)
        return types

    def count_loops(self) -> Dict[str, int]:
        """Count different types of loops"""
        if not self.ast:
            return {'for': 0, 'while': 0}

        counts = {'for': 0, 'while': 0}
        # nodes.For / nodes.While replace ast.For / ast.While
        for _ in self.ast.nodes_of_class(nodes.For):
            counts['for'] += 1
        for _ in self.ast.nodes_of_class(nodes.While):
            counts['while'] += 1
        return counts

    def has_recursion(self) -> bool:
        """Check if any function calls itself"""
        if not self.ast:
            return False

        for func_node in self.ast.nodes_of_class(nodes.FunctionDef):
            func_name = func_node.name
            for call_node in func_node.nodes_of_class(nodes.Call):
                if isinstance(call_node.func, nodes.Name):
                    if call_node.func.name == func_name:
                        return True
        return False
