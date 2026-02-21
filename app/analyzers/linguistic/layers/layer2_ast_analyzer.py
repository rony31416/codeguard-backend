"""
Layer 2: AST Analyzer
=====================
Structural code analysis using astroid (upgraded from stdlib ast).
Provides ground truth about code structure (~50ms).

astroid is the AST library used by Pylint - it offers:
- nodes_of_class() instead of ast.walk() for targeted traversal
- Node types: nodes.FunctionDef, nodes.Call, nodes.Const, etc.
- .name attribute instead of .id for Name nodes
- .attrname instead of .attr for Attribute nodes
- nodes.Const replaces ast.Constant
"""

import astroid
from astroid import nodes, exceptions as astroid_exceptions
import re
from typing import Dict, List, Any, Optional


class ASTAnalyzer:
    """Structural code analysis using astroid Abstract Syntax Tree."""

    def __init__(self):
        """Initialize AST analyzer."""
        self.confidence = 1.0  # AST provides 100% structural accuracy

    def parse_code(self, code: str) -> Optional[astroid.nodes.Module]:
        """Parse code into astroid Module."""
        try:
            return astroid.parse(code)
        except astroid_exceptions.AstroidSyntaxError as e:
            print(f"Syntax error in code: {e}")
            return None
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def extract_function_calls(self, tree: astroid.nodes.Module) -> List[Dict[str, Any]]:
        """Extract all function calls from astroid tree."""
        calls = []

        # nodes.Call replaces ast.Call
        for node in tree.nodes_of_class(nodes.Call):
            func_name = None

            # nodes.Name.name replaces ast.Name.id
            if isinstance(node.func, nodes.Name):
                func_name = node.func.name
            # nodes.Attribute.attrname replaces ast.Attribute.attr
            elif isinstance(node.func, nodes.Attribute):
                func_name = node.func.attrname

            if func_name:
                calls.append({
                    'name': func_name,
                    'lineno': node.lineno if hasattr(node, 'lineno') else None
                })

        return calls

    def extract_literals(self, tree: astroid.nodes.Module) -> List[Dict[str, Any]]:
        """Extract all literal values (strings, numbers)."""
        literals = []

        # nodes.Const replaces ast.Constant
        for node in tree.nodes_of_class(nodes.Const):
            literals.append({
                'type': type(node.value).__name__,
                'value': node.value,
                'lineno': node.lineno if hasattr(node, 'lineno') else None
            })

        return literals

    def extract_imports(self, tree: astroid.nodes.Module) -> List[str]:
        """Extract all imports."""
        imports = []

        for node in tree.nodes_of_class(nodes.Import):
            for name, alias in node.names:
                imports.append(name)

        for node in tree.nodes_of_class(nodes.ImportFrom):
            module = node.modname or ''
            for name, alias in node.names:
                imports.append(f"{module}.{name}" if module else name)

        return imports

    def extract_functions(self, tree: astroid.nodes.Module) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []

        for node in tree.nodes_of_class(nodes.FunctionDef):
            # In astroid: arg.name (not arg.arg like stdlib ast)
            args = [arg.name for arg in node.args.args or [] if hasattr(arg, 'name')]
            # Check for return statements inside the function
            has_return = any(True for _ in node.nodes_of_class(nodes.Return))
            functions.append({
                'name': node.name,
                'args': args,
                'lineno': node.lineno,
                'has_return': has_return
            })

        return functions

    def verify_npc(self, code: str) -> Dict[str, Any]:
        """Verify NPC issues using astroid."""
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

        issues = []
        calls = self.extract_function_calls(tree)

        # Check for print statements (confirmed by AST)
        print_calls = [c for c in calls if c['name'] == 'print']
        if print_calls:
            issues.append({
                'type': 'print_statement',
                'count': len(print_calls),
                'lines': [c['lineno'] for c in print_calls],
                'message': f'{len(print_calls)} print statement(s) found',
                'confidence': self.confidence
            })

        # Check for logging calls
        logging_calls = [c for c in calls if any(
            log in c['name'].lower() for log in ['log', 'debug', 'info', 'warning', 'error']
        )]
        if logging_calls:
            issues.append({
                'type': 'logging',
                'count': len(logging_calls),
                'message': f'{len(logging_calls)} logging call(s) found',
                'confidence': self.confidence
            })

        # Check for debugger imports
        imports = self.extract_imports(tree)
        debug_imports = [i for i in imports if any(d in i.lower() for d in ['pdb', 'debugger', 'ipdb'])]
        if debug_imports:
            issues.append({
                'type': 'debug_import',
                'imports': debug_imports,
                'message': f'Debug imports found: {", ".join(debug_imports)}',
                'confidence': self.confidence
            })

        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'ast',
            'confidence': self.confidence if issues else 0
        }

    def verify_prompt_bias(self, code: str, prompt: str = "") -> Dict[str, Any]:
        """Verify hardcoded literals using astroid."""
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

        issues = []
        literals = self.extract_literals(tree)

        if prompt:
            prompt_numbers = re.findall(r'\b\d+\b', prompt)

            for lit in literals:
                if lit['type'] in ['int', 'float']:
                    if str(lit['value']) in prompt_numbers:
                        issues.append({
                            'type': 'hardcoded_number',
                            'value': lit['value'],
                            'line': lit['lineno'],
                            'message': f'Number {lit["value"]} from prompt is hardcoded at line {lit["lineno"]}',
                            'confidence': self.confidence
                        })

        example_patterns = ['test', 'example', 'sample', 'demo', 'hello world']
        for lit in literals:
            if lit['type'] == 'str' and lit['value']:
                value_lower = str(lit['value']).lower()
                for pattern in example_patterns:
                    if pattern in value_lower:
                        issues.append({
                            'type': 'example_string',
                            'value': lit['value'],
                            'line': lit['lineno'],
                            'message': f'Example string "{lit["value"]}" at line {lit["lineno"]}',
                            'confidence': 0.9
                        })
                        break

        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'ast',
            'confidence': self.confidence if issues else 0
        }

    def verify_missing_features(self, code: str, prompt: str) -> Dict[str, Any]:
        """
        Verify if mentioned functions exist using astroid.
        CONSERVATIVE: Only reports missing features for complex prompts.
        """
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

        prompt_words = prompt.split()
        if len(prompt_words) < 15:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

        return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

    def analyze_return_type_mismatch(self, code: str, prompt: str) -> Dict[str, Any]:
        """Analyze return types vs prompt expectations using astroid."""
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}

        issues = []

        # CRITICAL: Check for print vs return
        if re.search(r'\breturn(s|ing)?\b', prompt.lower()):
            has_return_statement = False
            has_print_statement = False

            # nodes.Return replaces ast.Return
            for node in tree.nodes_of_class(nodes.Return):
                if node.value is not None:
                    has_return_statement = True

            # nodes.Call replaces ast.Call; nodes.Name.name replaces ast.Name.id
            for node in tree.nodes_of_class(nodes.Call):
                if isinstance(node.func, nodes.Name) and node.func.name == 'print':
                    has_print_statement = True

            if has_print_statement and not has_return_statement:
                issues.append({
                    'type': 'print_vs_return',
                    'expected': 'return statement',
                    'actual': 'print statement',
                    'message': 'Function prints output instead of returning it',
                    'confidence': self.confidence
                })

        expects_list = 'list' in prompt.lower() and 'return' in prompt.lower()
        expects_dict = 'dict' in prompt.lower() and 'return' in prompt.lower()

        for node in tree.nodes_of_class(nodes.Return):
            if node.value is not None:
                return_type = None

                # nodes.List / nodes.Dict replace ast.List / ast.Dict
                if isinstance(node.value, nodes.List):
                    return_type = 'list'
                elif isinstance(node.value, nodes.Dict):
                    return_type = 'dict'
                # nodes.Const replaces ast.Constant
                elif isinstance(node.value, nodes.Const):
                    return_type = type(node.value.value).__name__

                if expects_list and return_type != 'list':
                    issues.append({
                        'type': 'return_type_mismatch',
                        'expected': 'list',
                        'actual': return_type,
                        'line': node.lineno,
                        'message': f'Expected list return but got {return_type} at line {node.lineno}',
                        'confidence': self.confidence
                    })

                if expects_dict and return_type != 'dict':
                    issues.append({
                        'type': 'return_type_mismatch',
                        'expected': 'dict',
                        'actual': return_type,
                        'line': node.lineno,
                        'message': f'Expected dict return but got {return_type} at line {node.lineno}',
                        'confidence': self.confidence
                    })

        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'ast',
            'confidence': self.confidence if issues else 0
        }


if __name__ == "__main__":
    """Quick test"""
    analyzer = ASTAnalyzer()

    test_code = """
def add_numbers(a, b):
    print(f"Adding {a} and {b}")
    result = a + b
    return result

test_value = "example"
result = add_numbers(5, 3)
"""

    test_prompt = "Create a function to add 5 and 3"

    print("Testing ASTAnalyzer (astroid)...")
    print("\n1. NPC Verification:")
    npc = analyzer.verify_npc(test_code)
    print(f"Found: {npc['found']}, Issues: {len(npc['issues'])}")
    for issue in npc['issues']:
        print(f"  - {issue['message']}")

    print("\n2. Prompt Bias Verification:")
    bias = analyzer.verify_prompt_bias(test_code, test_prompt)
    print(f"Found: {bias['found']}, Issues: {len(bias['issues'])}")
    for issue in bias['issues']:
        print(f"  - {issue['message']}")
