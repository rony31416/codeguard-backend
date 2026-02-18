"""
Detect fundamental misunderstanding of the task
Enhanced with 3-layer cascade architecture
"""
import re
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .utils.similarity_calculator import SimilarityCalculator
from .layers import RuleEngine, ASTAnalyzer, LLMReasoner, LayerAggregator


class MisinterpretationDetector(BaseDetector):
    """Detect if code fundamentally misunderstood the prompt using 3-layer cascade"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        self.similarity_calculator = SimilarityCalculator()
        
        # Initialize 3-layer architecture
        self.rule_engine = RuleEngine()
        self.ast_analyzer = ASTAnalyzer()
        self.llm_reasoner = LLMReasoner()
        self.aggregator = LayerAggregator()
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method using 3-layer cascade with aggregation"""
        # LAYER 1: Rule Engine (Fast pattern matching ~10ms, 95% confidence)
        layer1_result = self.rule_engine.detect_misinterpretation(self.code, self.prompt)
        
        # LAYER 2: AST Analyzer (Structural verification ~50ms, 100% confidence)
        layer2_result = None
        if self.code_ast:
            layer2_result = self.ast_analyzer.analyze_return_type_mismatch(self.code, self.prompt)
        
        # LAYER 3: LLM Reasoner (ALWAYS invoke - most important for misinterpretation)
        layer3_result = self.llm_reasoner.verify_misinterpretation(
            self.prompt,
            self.code
        )
        
        # AGGREGATE RESULTS from all layers
        aggregated = self.aggregator.aggregate_findings(
            layer1_result,
            layer2_result,
            layer3_result
        )
        
        # Semantic similarity check (backup for edge cases)
        similarity = self.similarity_calculator.calculate_similarity(self.prompt, self.code)
        if similarity < 0.2 and not aggregated['findings']:
            aggregated['findings'].append(f"low semantic similarity ({round(similarity, 2)})")
            aggregated['found'] = True
            aggregated['severity'] = max(aggregated.get('severity', 0), 3.0)
        
        # Calculate misinterpretation score from severity
        misinterpretation_score = aggregated.get('severity', 0) / 10.0
        
        # Return aggregated results in expected format
        return {
            "found": aggregated['found'] or misinterpretation_score > 0.4,
            "score": round(misinterpretation_score, 2),
            "reasons": aggregated['findings'],
            "confidence": aggregated['confidence'],
            "severity": aggregated.get('severity'),
            "consensus": aggregated['consensus'],
            "primary_detection": aggregated['primary_detection'],
            "layers_used": aggregated['layers_used'],
            "layers_detail": aggregated['layers_detail'],
            "reliability": self.aggregator.calculate_reliability_score(
                aggregated['consensus'], 
                aggregated['confidence']
            )
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
