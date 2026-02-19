import ast
import re
import sys
from io import StringIO
from typing import List, Dict, Any, Set
from pyflakes import api as pyflakes_api
from pyflakes import reporter as pyflakes_reporter

class StaticAnalyzer:
    def __init__(self, code: str):
        self.code = code
        self.lines = code.split('\n')
        self.tree = None
        self.issues = []
    
    def analyze(self) -> Dict[str, Any]:
        """Run all static analysis checks - fault tolerant"""
        results = {
            "syntax_error": self._check_syntax(),
            "hallucinated_objects": self._check_hallucinated_objects(),
            "incomplete_generation": self._check_incomplete_generation(),
            "silly_mistakes": self._check_silly_mistakes(),
            "undefined_names": self._check_undefined_names(),
            "wrong_attribute": self._check_wrong_attribute_static(),
            "wrong_input_type": self._check_wrong_input_type_static(),
            "prompt_biased": self._check_prompt_biased_code(),
            "npc": self._check_non_prompted_consideration(),
            "missing_corner_case": self._check_missing_corner_cases()
        }
        return results
    
    def _check_syntax(self) -> Dict[str, Any]:
        """Check for syntax errors using AST parsing"""
        try:
            self.tree = ast.parse(self.code)
            return {"found": False, "error": None}
        except SyntaxError as e:
            # Still try to get partial AST for further analysis
            return {
                "found": True,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        except Exception as e:
            return {
                "found": True,
                "error": f"Parse error: {str(e)}",
                "line": None,
                "offset": None,
                "text": None
            }
    
    def _try_parse_partial(self) -> ast.AST:
        """Try to parse code with syntax errors removed"""
        if self.tree:
            return self.tree
        
        # Try to parse by removing problematic lines
        for i in range(len(self.lines)):
            try:
                # Remove lines one by one to get partial AST
                temp_lines = self.lines[:i] + self.lines[i+1:]
                temp_code = '\n'.join(temp_lines)
                return ast.parse(temp_code)
            except:
                continue
        return None
    
    def _check_hallucinated_objects(self) -> Dict[str, Any]:
        """Detect potentially undefined variables/functions via pattern matching"""
        hallucinated = []
        
        # Pattern matching approach (works even with syntax errors)
        patterns = [
            (r'(\w+)\s*=\s*(\w+)\(\)', 'function_call'),  # x = SomeClass()
            (r'from\s+(\w+)\s+import', 'import_statement'),
            (r'import\s+(\w+)', 'import_statement'),
        ]
        
        # Hardcoded Python built-ins (more reliable than dir(__builtins__) on cloud platforms)
        builtins = {
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
            # Built-in exceptions
            'BaseException', 'Exception', 'ArithmeticError', 'AssertionError',
            'AttributeError', 'BlockingIOError', 'BrokenPipeError', 'BufferError',
            'BytesWarning', 'ChildProcessError', 'ConnectionError', 'ConnectionAbortedError',
            'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
            'EOFError', 'EnvironmentError', 'FileExistsError', 'FileNotFoundError',
            'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
            'ImportError', 'ImportWarning', 'IndentationError', 'IndexError',
            'InterruptedError', 'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
            'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError',
            'NotADirectoryError', 'NotImplementedError', 'OSError', 'OverflowError',
            'PendingDeprecationWarning', 'PermissionError', 'ProcessLookupError',
            'RecursionError', 'ReferenceError', 'ResourceWarning', 'RuntimeError',
            'RuntimeWarning', 'StopAsyncIteration', 'StopIteration', 'SyntaxError',
            'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TimeoutError',
            'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError',
            'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning',
            'ValueError', 'Warning', 'ZeroDivisionError',
            # Built-in constants
            'False', 'True', 'None', 'NotImplemented', 'Ellipsis', '__debug__',
        }
        
        common_modules = {'math', 'os', 'sys', 're', 'json', 'time', 'datetime', 
                         'random', 'collections', 'itertools', 'functools', 'numpy', 'pandas',
                         'logging', 'pathlib', 'io', 'typing', 'copy', 'pickle'}
        
        # Look for suspicious class instantiations (skip comments)
        class_pattern = re.compile(r'([A-Z][a-zA-Z0-9]*)\s*\(')
        for i, line in enumerate(self.lines):
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Remove inline comments before matching
            code_part = line.split('#')[0]
            matches = class_pattern.findall(code_part)
            for match in matches:
                if match not in builtins and match not in common_modules:
                    # Check if it's defined in the code
                    if not any(f'class {match}' in l for l in self.lines):
                        hallucinated.append({
                            "name": match,
                            "line": i + 1,
                            "type": "class"
                        })
        
        # Also check with AST if available
        tree = self._try_parse_partial()
        if tree:
            defined_names = set()
            used_names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    defined_names.add(node.name)
                    # Add function parameters to defined names
                    for arg in node.args.args:
                        defined_names.add(arg.arg)
                    # Add keyword-only args
                    for arg in node.args.kwonlyargs:
                        defined_names.add(arg.arg)
                    # Add *args and **kwargs
                    if node.args.vararg:
                        defined_names.add(node.args.vararg.arg)
                    if node.args.kwarg:
                        defined_names.add(node.args.kwarg.arg)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_names.add(target.id)
                # FIX: Add loop variables as defined
                elif isinstance(node, ast.For):
                    if isinstance(node.target, ast.Name):
                        defined_names.add(node.target.id)
                    elif isinstance(node.target, ast.Tuple):
                        for elt in node.target.elts:
                            if isinstance(elt, ast.Name):
                                defined_names.add(elt.id)
                # FIX: Add with statement variables as defined
                elif isinstance(node, ast.With):
                    for item in node.items:
                        if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                            defined_names.add(item.optional_vars.id)
                # FIX: Add comprehension variables as defined
                elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    for generator in node.generators:
                        if isinstance(generator.target, ast.Name):
                            defined_names.add(generator.target.id)
                        elif isinstance(generator.target, ast.Tuple):
                            for elt in generator.target.elts:
                                if isinstance(elt, ast.Name):
                                    defined_names.add(elt.id)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        defined_names.add(name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        defined_names.add(name)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            
            for name in used_names:
                if name not in defined_names and name not in builtins and name not in common_modules:
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
    
    def _check_incomplete_generation(self) -> Dict[str, Any]:
        """Check for incomplete code generation patterns"""
        incomplete = []
        
        # Pattern 1: Variables assigned to nothing
        for i, line in enumerate(self.lines):
            # Check for incomplete assignments like "final_val ="
            if re.search(r'\w+\s*=\s*$', line.strip()):
                incomplete.append({
                    "type": "incomplete_assignment",
                    "line": i + 1,
                    "description": "Assignment with no value"
                })
        
        # Pattern 2: Functions with only pass or docstring
        tree = self._try_parse_partial()
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) == 0:
                        incomplete.append({
                            "type": "empty_function",
                            "line": node.lineno,
                            "description": f"Function '{node.name}' has no body"
                        })
                    elif len(node.body) == 1:
                        first_stmt = node.body[0]
                        if isinstance(first_stmt, ast.Pass):
                            incomplete.append({
                                "type": "pass_only",
                                "line": node.lineno,
                                "description": f"Function '{node.name}' contains only 'pass'"
                            })
        
        # Pattern 3: Incomplete strings or comments suggesting cutoff
        for i, line in enumerate(self.lines):
            if '...' in line or 'TODO' in line or 'FIXME' in line:
                incomplete.append({
                    "type": "incomplete_marker",
                    "line": i + 1,
                    "description": "Code contains incomplete markers"
                })
            # Comments suggesting incomplete code
            if '# missing' in line.lower() or '# stopped' in line.lower() or '# incomplete' in line.lower():
                incomplete.append({
                    "type": "incomplete_comment",
                    "line": i + 1,
                    "description": "Comment indicates incomplete code"
                })
        
        # Pattern 4: Incomplete loop logic (e.g., while loop with only one counter modified)
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.While):
                    # Check if there are comparison variables in the test
                    loop_vars = set()
                    if isinstance(node.test, ast.Compare):
                        if isinstance(node.test.left, ast.Name):
                            loop_vars.add(node.test.left.id)
                        for comp in node.test.comparators:
                            if isinstance(comp, ast.Name):
                                loop_vars.add(comp.id)
                    
                    # Check which variables are modified in the loop body
                    modified_vars = set()
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                            modified_vars.add(stmt.target.id)
                        elif isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    modified_vars.add(target.id)
                    
                    # If loop has 2+ comparison variables but only 1 is modified, it's likely incomplete
                    if len(loop_vars) >= 2 and len(modified_vars) == 1 and modified_vars.issubset(loop_vars):
                        incomplete.append({
                            "type": "incomplete_loop",
                            "line": node.lineno,
                            "description": f"While loop modifies only {modified_vars.pop()} but compares multiple variables"
                        })
        
        return {
            "found": len(incomplete) > 0,
            "details": incomplete
        }
    
    def _check_silly_mistakes(self) -> Dict[str, Any]:
        """Detect non-human coding patterns"""
        silly_mistakes = []
        
        # Pattern 1: Reversed operands in calculations
        # Look for patterns like "rate - price" instead of "price - rate"
        for i, line in enumerate(self.lines):
            # Detect suspicious subtractions with small values
            if re.search(r'(discount|rate|percent)\s*-\s*(\w+)', line):
                silly_mistakes.append({
                    "type": "reversed_operands",
                    "line": i + 1,
                    "description": "Suspicious operation: subtracting larger value from smaller (possible reversed operands)"
                })
        
        # Pattern 2: String concatenation with non-string
        for i, line in enumerate(self.lines):
            if re.search(r'["\'].*["\']\s*\+\s*\w+(?!\()', line):
                # Check if the variable looks numeric
                if re.search(r'(rate|price|count|value|num)', line):
                    silly_mistakes.append({
                        "type": "type_concatenation",
                        "line": i + 1,
                        "description": "Attempting string concatenation with likely numeric value"
                    })
        
        # Pattern 3: Identical if/else branches (AST)
        tree = self._try_parse_partial()
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    if node.orelse and len(node.orelse) > 0:
                        try:
                            if_body_dump = [ast.dump(stmt) for stmt in node.body]
                            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                                continue
                            else:
                                else_body_dump = [ast.dump(stmt) for stmt in node.orelse]
                            
                            if if_body_dump == else_body_dump and len(if_body_dump) > 0:
                                silly_mistakes.append({
                                    "type": "identical_branches",
                                    "line": node.lineno,
                                    "description": "If and else branches contain identical code"
                                })
                        except:
                            continue
        
        return {
            "found": len(silly_mistakes) > 0,
            "details": silly_mistakes
        }
    
    def _check_undefined_names(self) -> Dict[str, Any]:
        """Use pyflakes to detect undefined names"""
        warnings = StringIO()
        reporter = pyflakes_reporter.Reporter(warnings, sys.stderr)
        
        try:
            pyflakes_api.check(self.code, '<string>', reporter)
            warning_text = warnings.getvalue()
            
            undefined = []
            for line in warning_text.split('\n'):
                if 'undefined name' in line:
                    undefined.append(line.strip())
            
            return {
                "found": len(undefined) > 0,
                "warnings": undefined
            }
        except Exception as e:
            return {"found": False, "warnings": [], "error": str(e)}
    
    def _check_wrong_attribute_static(self) -> Dict[str, Any]:
        """Detect wrong attribute access patterns (static analysis)"""
        wrong_attrs = []
        
        # Pattern: dict.attribute instead of dict['key']
        # Common mistake: item.cost instead of item['cost']
        for i, line in enumerate(self.lines):
            # Look for variable.attribute where variable looks like a dict
            dict_access = re.findall(r'(\w+)\.(\w+)', line)
            for var, attr in dict_access:
                # If accessing common dict keys as attributes
                if attr in ['cost', 'price', 'name', 'value', 'id', 'key']:
                    wrong_attrs.append({
                        "variable": var,
                        "attribute": attr,
                        "line": i + 1,
                        "description": f"Accessing '{attr}' as attribute instead of dictionary key"
                    })
        
        return {
            "found": len(wrong_attrs) > 0,
            "details": wrong_attrs
        }
    
    def _check_wrong_input_type_static(self) -> Dict[str, Any]:
        """Detect wrong input types in function calls (static analysis)"""
        wrong_types = []
        
        # Pattern: String literal passed to numeric functions
        numeric_functions = {
            'sqrt', 'pow', 'log', 'exp', 'sin', 'cos', 'tan',
            'ceil', 'floor', 'round', 'abs', 'int', 'float'
        }
        
        tree = self._try_parse_partial()
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if calling a numeric function
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    
                    if func_name in numeric_functions:
                        # Check if passing string arguments
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                wrong_types.append({
                                    "function": func_name,
                                    "expected_type": "numeric",
                                    "actual_type": "string",
                                    "value": arg.value,
                                    "line": node.lineno,
                                    "description": f"Passing string '{arg.value}' to numeric function {func_name}()"
                                })
        
        return {
            "found": len(wrong_types) > 0,
            "details": wrong_types
        }
    
    def _check_prompt_biased_code(self) -> Dict[str, Any]:
        """Detect hardcoded values from examples"""
        biased_code = []
        
        # Look for hardcoded specific values
        for i, line in enumerate(self.lines):
            # Check for hardcoded strings in comparisons (but skip common patterns)
            if re.search(r'==\s*["\']Example_', line):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded check for example-specific value"
                })
            
            # Check for hardcoded file names from examples (e.g., "orders_demo.csv")
            if re.search(r'==\s*["\'][^"\']*(demo|example|sample|test)[^"\']*(\.(csv|txt|json))?["\']', line, re.IGNORECASE):
                biased_code.append({
                    "line": i + 1,
                    "description": "Hardcoded example filename in comparison"
                })
        
        return {
            "found": len(biased_code) > 0,
            "details": biased_code
        }
    
    def _check_non_prompted_consideration(self) -> Dict[str, Any]:
        """Detect features not requested in prompt"""
        npc_issues = []
        
        # Pattern 1: Security checks that weren't asked for
        for i, line in enumerate(self.lines):
            if 'raise' in line and any(word in line.lower() for word in ['admin', 'security', 'permission', 'auth']):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added security/authentication logic not requested"
                })
        
        # Pattern 2: Validation checks beyond requirements
        for i, line in enumerate(self.lines):
            if re.search(r'if.*>\s*\d{3,}.*raise', line):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added arbitrary threshold validation not requested"
                })
        
        return {
            "found": len(npc_issues) > 0,
            "details": npc_issues
        }
    
    def _check_missing_corner_cases(self) -> Dict[str, Any]:
        """Detect missing critical edge case handling (very conservative)"""
        missing_cases = []
        
        # Only check for CRITICAL missing corner cases, not defensive programming
        tree = self._try_parse_partial()
        
        # Check for division operations without ANY zero/empty checking
        if tree:
            for i, line in enumerate(self.lines):
                if '/' in line and 'if' not in line:
                    # Check if there's ANY protection against division by zero
                    # Look for checks in surrounding context (wider range)
                    context_start = max(0, i-5)
                    context_end = min(len(self.lines), i+3)
                    context_lines = '\n'.join(self.lines[context_start:context_end])
                    
                    # Check for various forms of protection
                    has_protection = any([
                        '!= 0' in context_lines,
                        '== 0' in context_lines,
                        'if not' in context_lines,  # Empty check
                        'len(' in context_lines and ('if' in context_lines or 'return' in context_lines),  # Length check
                        'ZeroDivisionError' in context_lines,  # Exception handling
                    ])
                    
                    if not has_protection:
                        # Only report if it's clearly risky (dividing by len() without checks)
                        if 'len(' in line or 'count' in line.lower():
                            missing_cases.append({
                                "line": i + 1,
                                "description": "Division operation without zero check"
                            })
        
        return {
            "found": len(missing_cases) > 0,
            "details": missing_cases
        }
