"""
Layer 1: Rule Engine
====================
Fast pattern matching using regex.
Returns preliminary findings in <10ms.
"""

import re
from typing import Dict, List, Any


class RuleEngine:
    """Fast regex-based pattern matching."""
    
    # NPC Patterns - Non-Prompted Considerations
    NPC_PATTERNS = {
        'debug_prints': [
            r'print\s*\(',
            r'console\.log\s*\(',
            r'debugger',
            r'import pdb',
            r'breakpoint\(\)',
        ],
        'logging': [
            r'logger\.',
            r'logging\.',
            r'\.debug\(',
            r'\.info\(',
            r'\.warning\(',
        ],
        'validation': [
            r'if\s+.*\s+is\s+None',
            r'if\s+not\s+',
            r'assert\s+',
            r'raise\s+',
        ],
        'error_handling': [
            r'try:',
            r'except\s+',
            r'finally:',
        ],
    }
    
    # Prompt Bias Patterns - Hardcoded examples
    EXAMPLE_PATTERNS = {
        'hardcoded_names': [
            r'\b(john|jane|alice|bob|test|example|sample|demo)\b',
            r'user123',
            r'test@',
        ],
        'hardcoded_numbers': [
            r'\b(123|456|789|42|100)\b(?!\s*(px|em|%|\))',  # Common example numbers
        ],
        'hardcoded_strings': [
            r'"hello\s*world"',
            r'"test"',
            r'"example"',
            r'"sample"',
        ],
    }
    
    # Missing Features - Action verbs that might indicate requirements
    ACTION_VERBS = [
        'create', 'add', 'delete', 'remove', 'update', 'edit',
        'save', 'load', 'fetch', 'get', 'set', 'send',
        'validate', 'verify', 'check', 'handle', 'process',
        'calculate', 'compute', 'sort', 'filter', 'search',
    ]
    
    def __init__(self):
        """Initialize the rule engine."""
        self.confidence = 0.95  # High confidence for pattern matches
    
    def detect_npc(self, code: str) -> Dict[str, Any]:
        """Detect NPC issues using patterns."""
        issues = []
        
        # Check for debug prints
        for pattern in self.NPC_PATTERNS['debug_prints']:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'debug_code',
                    'pattern': pattern,
                    'message': 'Debug/print statements found',
                    'confidence': self.confidence
                })
        
        # Check for logging
        for pattern in self.NPC_PATTERNS['logging']:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'logging',
                    'pattern': pattern,
                    'message': 'Logging statements found',
                    'confidence': self.confidence
                })
        
        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'rule_engine',
            'confidence': self.confidence if issues else 0
        }
    
    def detect_prompt_bias(self, code: str, prompt: str = "") -> Dict[str, Any]:
        """Detect hardcoded examples from prompt."""
        issues = []
        
        # Extract potential examples from prompt
        if prompt:
            # Look for numbers in prompt
            prompt_numbers = re.findall(r'\b\d+\b', prompt)
            for num in prompt_numbers:
                # Check if this number appears in code (not in comments)
                code_clean = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
                if re.search(rf'\b{num}\b', code_clean):
                    issues.append({
                        'type': 'hardcoded_number',
                        'value': num,
                        'message': f'Number {num} from prompt is hardcoded',
                        'confidence': 0.9
                    })
            
            # Look for names in prompt
            names = re.findall(r'\b[A-Z][a-z]+\b', prompt)
            for name in names:
                if re.search(rf'\b{name}\b', code, re.IGNORECASE):
                    issues.append({
                        'type': 'hardcoded_name',
                        'value': name,
                        'message': f'Example name "{name}" from prompt is hardcoded',
                        'confidence': 0.85
                    })
        
        # Check common example patterns
        for pattern in self.EXAMPLE_PATTERNS['hardcoded_names']:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'example_data',
                    'value': match,
                    'message': f'Example data "{match}" found',
                    'confidence': 0.8
                })
        
        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'rule_engine',
            'confidence': max([i['confidence'] for i in issues]) if issues else 0
        }
    
    def detect_missing_features(self, code: str, prompt: str) -> Dict[str, Any]:
        """Detect potentially missing features based on prompt."""
        issues = []
        
        # Extract action verbs from prompt
        prompt_lower = prompt.lower()
        mentioned_actions = []
        
        for verb in self.ACTION_VERBS:
            if re.search(rf'\b{verb}\b', prompt_lower):
                mentioned_actions.append(verb)
        
        # Check if corresponding code exists
        for action in mentioned_actions:
            # Look for function definitions with this action
            func_pattern = rf'def\s+\w*{action}\w*\s*\('
            if not re.search(func_pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'missing_function',
                    'action': action,
                    'message': f'Prompt mentions "{action}" but no corresponding function found',
                    'confidence': 0.7  # Lower confidence - might be implemented differently
                })
        
        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'rule_engine',
            'confidence': max([i['confidence'] for i in issues]) if issues else 0
        }
    
    def detect_misinterpretation(self, code: str, prompt: str) -> Dict[str, Any]:
        """Basic pattern-based misinterpretation detection."""
        issues = []
        
        # Check for return type mismatches (basic)
        if 'return a list' in prompt.lower() or 'return list' in prompt.lower():
            if not re.search(r'return\s*\[', code):
                issues.append({
                    'type': 'return_type_mismatch',
                    'expected': 'list',
                    'message': 'Prompt expects list return but code may return something else',
                    'confidence': 0.6  # Low confidence - AST should verify
                })
        
        if 'return a dict' in prompt.lower() or 'return dict' in prompt.lower():
            if not re.search(r'return\s*\{', code):
                issues.append({
                    'type': 'return_type_mismatch',
                    'expected': 'dict',
                    'message': 'Prompt expects dict return but code may return something else',
                    'confidence': 0.6
                })
        
        return {
            'found': len(issues) > 0,
            'issues': issues,
            'layer': 'rule_engine',
            'confidence': max([i['confidence'] for i in issues]) if issues else 0
        }


if __name__ == "__main__":
    """Quick test"""
    engine = RuleEngine()
    
    test_code = """
def add_numbers(a, b):
    print(f"Debug: adding {a} and {b}")
    result = a + b
    return result

result = add_numbers(5, 3)
print(result)
"""
    
    test_prompt = "Create a function to add two numbers: 5 and 3"
    
    print("Testing Rule Engine...")
    print("\n1. NPC Detection:")
    npc = engine.detect_npc(test_code)
    print(f"Found: {npc['found']}, Issues: {len(npc['issues'])}")
    
    print("\n2. Prompt Bias Detection:")
    bias = engine.detect_prompt_bias(test_code, test_prompt)
    print(f"Found: {bias['found']}, Issues: {len(bias['issues'])}")
    
    print("\n3. Missing Features:")
    missing = engine.detect_missing_features(test_code, test_prompt)
    print(f"Found: {missing['found']}, Issues: {len(missing['issues'])}")
