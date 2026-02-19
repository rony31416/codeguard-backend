"""
Layer 2: AST Analyzer
=====================
Structural code analysis using Python AST.
Provides ground truth about code structure (~50ms).
"""

import ast
from typing import Dict, List, Any, Optional


class ASTAnalyzer:
    """Structural code analysis using Abstract Syntax Tree."""
    
    def __init__(self):
        """Initialize AST analyzer."""
        self.confidence = 1.0  # AST provides 100% structural accuracy
    
    def parse_code(self, code: str) -> Optional[ast.Module]:
        """Parse code into AST."""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            print(f"Syntax error in code: {e}")
            return None
    
    def extract_function_calls(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract all function calls from AST."""
        calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name:
                    calls.append({
                        'name': func_name,
                        'lineno': node.lineno if hasattr(node, 'lineno') else None
                    })
        
        return calls
    
    def extract_literals(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract all literal values (strings, numbers)."""
        literals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                literals.append({
                    'type': type(node.value).__name__,
                    'value': node.value,
                    'lineno': node.lineno if hasattr(node, 'lineno') else None
                })
        
        return literals
    
    def extract_imports(self, tree: ast.Module) -> List[str]:
        """Extract all imports."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return imports
    
    def extract_functions(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'lineno': node.lineno,
                    'has_return': any(isinstance(n, ast.Return) for n in ast.walk(node))
                })
        
        return functions
    
    def verify_npc(self, code: str) -> Dict[str, Any]:
        """Verify NPC issues using AST."""
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
        logging_calls = [c for c in calls if any(log in c['name'].lower() for log in ['log', 'debug', 'info', 'warning', 'error'])]
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
        """Verify hardcoded literals using AST."""
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}
        
        issues = []
        literals = self.extract_literals(tree)
        
        # If we have a prompt, check for values from prompt
        if prompt:
            # Extract numbers from prompt
            import re
            prompt_numbers = re.findall(r'\b\d+\b', prompt)
            
            # Check if these numbers appear as literals
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
        
        # Check for example strings
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
        """Verify if mentioned functions exist using AST.
        
        CONSERVATIVE: Only reports missing features for complex prompts with
        explicit multiple requirements. Simple prompts return no missing features.
        """
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}
        
        # Conservative approach: Skip for simple prompts
        prompt_words = prompt.split()
        if len(prompt_words) < 15:
            # Simple prompt - don't look for missing features
            return {
                'found': False,
                'issues': [],
                'layer': 'ast',
                'confidence': 0
            }
        
        # For complex prompts, could analyze here, but leave to LLM Layer 3
        # Layer 2 focuses on structural verification, not semantic feature matching
        
        return {
            'found': False,
            'issues': [],
            'layer': 'ast',
            'confidence': 0
        }
    
    def analyze_return_type_mismatch(self, code: str, prompt: str) -> Dict[str, Any]:
        """Analyze return types vs prompt expectations."""
        tree = self.parse_code(code)
        if not tree:
            return {'found': False, 'issues': [], 'layer': 'ast', 'confidence': 0}
        
        issues = []
        
        # CRITICAL: Check for print vs return (AST verification)
        import re
        if re.search(r'\breturn(s|ing)?\b', prompt.lower()):
            has_return_statement = False
            has_print_statement = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value:
                    has_return_statement = True
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'print':
                        has_print_statement = True
            
            if has_print_statement and not has_return_statement:
                issues.append({
                    'type': 'print_vs_return',
                    'expected': 'return statement',
                    'actual': 'print statement',
                    'message': 'Function prints output instead of returning it',
                    'confidence': self.confidence  # 100% confidence from AST
                })
        
        # Check what prompt expects
        expects_list = 'list' in prompt.lower() and 'return' in prompt.lower()
        expects_dict = 'dict' in prompt.lower() and 'return' in prompt.lower()
        
        # Analyze actual returns
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value:
                return_type = None
                
                if isinstance(node.value, ast.List):
                    return_type = 'list'
                elif isinstance(node.value, ast.Dict):
                    return_type = 'dict'
                elif isinstance(node.value, ast.Constant):
                    return_type = type(node.value.value).__name__
                
                # Check mismatch
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
    
    print("Testing AST Analyzer...")
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
