"""
Detect fundamental misunderstanding of the task
"""
import re
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .utils.similarity_calculator import SimilarityCalculator


class MisinterpretationDetector(BaseDetector):
    """Detect if code fundamentally misunderstood the prompt"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        self.similarity_calculator = SimilarityCalculator()
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method"""
        misinterpretation_score = 0.0
        reasons = []
        
        # Method 1: Return vs Print mismatch
        score, reason = self._detect_return_print_mismatch()
        if reason:
            misinterpretation_score += score
            reasons.append(reason)
        
        # Method 2: Wrong data type
        score, reason = self._detect_wrong_data_type()
        if reason:
            misinterpretation_score += score
            reasons.append(reason)
        
        # Method 3: Semantic similarity too low
        similarity = self.similarity_calculator.calculate_similarity(self.prompt, self.code)
        if similarity < 0.2:  # Very low similarity
            misinterpretation_score += 0.3
            reasons.append(f"low semantic similarity ({similarity})")
        
        # Method 4: Missing core functionality
        score, reason = self._detect_missing_core_function()
        if reason:
            misinterpretation_score += score
            reasons.append(reason)
        
        # Method 5: Wrong algorithm/approach
        score, reason = self._detect_wrong_approach()
        if reason:
            misinterpretation_score += score
            reasons.append(reason)
        
        return {
            "found": misinterpretation_score > 0.4,  # Threshold for misinterpretation
            "score": round(misinterpretation_score, 2),
            "reasons": reasons
        }
    
    def _detect_return_print_mismatch(self) -> tuple:
        """Check if code prints when it should return"""
        # Prompt asks for return
        asks_for_return = any(kw in self.prompt_lower for kw in ['return', 'output', 'give'])
        
        if asks_for_return and self.code_ast:
            has_return = any(isinstance(node, ast.Return) for node in ast.walk(self.code_ast) if isinstance(node, ast.Return) and node.value)
            has_print = 'print(' in self.code
            
            if has_print and not has_return:
                return (0.4, "prints instead of returning")
        
        return (0.0, None)
    
    def _detect_wrong_data_type(self) -> tuple:
        """Check for wrong return type"""
        # Expected types from prompt
        type_mapping = {
            'list': ['list', 'array'],
            'dict': ['dict', 'dictionary', 'object'],
            'string': ['string', 'str', 'text'],
            'number': ['int', 'integer', 'float', 'number'],
            'bool': ['bool', 'boolean', 'true', 'false']
        }
        
        # Find expected type
        expected_type = None
        for canonical, keywords in type_mapping.items():
            if any(kw in self.prompt_lower for kw in keywords):
                expected_type = canonical
                break
        
        if not expected_type:
            return (0.0, None)
        
        # Check return type in code
        if self.code_ast:
            for node in ast.walk(self.code_ast):
                if isinstance(node, ast.Return) and node.value:
                    # Check if returning wrong type
                    if isinstance(node.value, ast.Constant):
                        actual_type = type(node.value.value).__name__
                        
                        # Map Python types
                        actual_canonical = {
                            'str': 'string',
                            'int': 'number',
                            'float': 'number',
                            'list': 'list',
                            'dict': 'dict',
                            'bool': 'bool'
                        }.get(actual_type, actual_type)
                        
                        if actual_canonical != expected_type:
                            return (0.3, f"returns {actual_canonical} but expects {expected_type}")
        
        return (0.0, None)
    
    def _detect_missing_core_function(self) -> tuple:
        """Check if main function definition is missing"""
        # Extract function name from prompt
        func_pattern = r'(?:function|write|create|implement)\s+(?:a\s+)?(?:function\s+)?(?:called\s+)?["\']?(\w+)["\']?'
        matches = re.findall(func_pattern, self.prompt_lower)
        
        if matches and self.code_ast:
            requested_func = matches[0]
            
            # Get all function names in code
            actual_funcs = set()
            for node in ast.walk(self.code_ast):
                if isinstance(node, ast.FunctionDef):
                    actual_funcs.add(node.name.lower())
            
            if requested_func not in actual_funcs:
                return (0.3, f"missing requested function '{requested_func}'")
        
        return (0.0, None)
    
    def _detect_wrong_approach(self) -> tuple:
        """Detect if using completely wrong algorithm"""
        # Check for algorithm-specific keywords
        algorithm_keywords = {
            'sort': ['sorted', 'sort(', '.sort'],
            'search': ['search', 'find', 'index'],
            'filter': ['filter', 'comprehension', '['],
            'sum': ['sum(', '+='],
            'count': ['count(', 'len(']
        }
        
        for algo, keywords in algorithm_keywords.items():
            if algo in self.prompt_lower:
                # Check if ANY of the expected keywords appear in code
                if not any(kw in self.code for kw in keywords):
                    return (0.2, f"'{algo}' requested but not found in implementation")
        
        return (0.0, None)
