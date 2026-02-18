"""
Detect features mentioned in prompt but missing in code
Enhanced with 3-layer cascade architecture
"""
import re
import ast
from typing import Dict, Any, List, Set
from .base_detector import BaseDetector
from .utils.keyword_extractor import KeywordExtractor
from .utils.ast_analyzer import ASTAnalyzer as UtilsASTAnalyzer
from .layers import RuleEngine, ASTAnalyzer, LLMReasoner, LayerAggregator


class MissingFeatureDetector(BaseDetector):
    """Detect features requested but not implemented using 3-layer cascade"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        self.keyword_extractor = KeywordExtractor()
        self.utils_ast_analyzer = UtilsASTAnalyzer(self.code_ast) if self.code_ast else None
        
        # Initialize 3-layer architecture
        self.rule_engine = RuleEngine()
        self.ast_analyzer = ASTAnalyzer()
        self.llm_reasoner = LLMReasoner()
        self.aggregator = LayerAggregator()
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method using 3-layer cascade with aggregation"""
        # LAYER 1: Rule Engine (Fast pattern matching ~10ms, 95% confidence)
        layer1_result = self.rule_engine.detect_missing_features(self.code, self.prompt)
        
        # LAYER 2: AST Analyzer (Structural verification ~50ms, 100% confidence)
        layer2_result = None
        if self.code_ast:
            layer2_result = self.ast_analyzer.verify_missing_features(self.code, self.prompt)
        
        # LAYER 3: LLM Reasoner (Deep semantic analysis ~300ms, 98% confidence)
        # Important for semantic feature matching
        layer3_result = None
        if layer1_result.get('confidence', 0) < 0.98 or not layer1_result.get('issues'):
            layer3_result = self.llm_reasoner.deep_semantic_analysis(
                self.prompt,
                self.code,
                previous_findings={
                    'rule_engine': layer1_result,
                    'ast': layer2_result
                }
            )
        
        # AGGREGATE RESULTS from all layers
        aggregated = self.aggregator.aggregate_findings(
            layer1_result,
            layer2_result,
            layer3_result
        )
        
        # Limit features to top 5
        features = aggregated['findings'][:5]
        
        # Return aggregated results in expected format
        return {
            "found": aggregated['found'],
            "features": features,
            "count": len(features),
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
    
    def _detect_missing_actions(self) -> List[str]:
        """Check if requested actions are implemented"""
        missing = []
        
        # Extract action verbs from prompt
        requested_actions = self.keyword_extractor.extract_action_verbs(self.prompt)
        
        # Check if each action is in code
        for action in requested_actions:
            # Look for the action word in code (case insensitive)
            if action not in self.code_lower:
                # Also check if function with that name exists
                if self.ast_analyzer:
                    functions = self.ast_analyzer.get_function_names()
                    if action not in functions:
                        missing.append(f"'{action}' action not implemented")
                else:
                    missing.append(f"'{action}' action not implemented")
        
        return missing
    
    def _detect_missing_data_types(self) -> List[str]:
        """Check if requested data types are used"""
        missing = []
        
        # Extract data types from prompt
        requested_types = self.keyword_extractor.extract_data_types(self.prompt)
        
        # Check if types are mentioned in code
        for dtype in requested_types:
            if dtype not in self.code_lower:
                missing.append(f"'{dtype}' data type not used")
        
        return missing
    
    def _detect_missing_returns(self) -> List[str]:
        """Check if function returns value when expected"""
        missing = []
        
        # Check if prompt asks for return
        return_keywords = ['return', 'output', 'result', 'give back']
        asks_for_return = any(kw in self.prompt_lower for kw in return_keywords)
        
        if asks_for_return and self.code_ast:
            # Check if code has return statements
            has_return = False
            for node in ast.walk(self.code_ast):
                if isinstance(node, ast.Return):
                    if node.value is not None:  # Not just 'return' without value
                        has_return = True
                        break
            
            if not has_return:
                # Check if it prints instead
                has_print = 'print(' in self.code
                if has_print:
                    missing.append("should return value but only prints")
                else:
                    missing.append("missing return statement")
        
        return missing
    
    def _is_error_handling_requested(self) -> bool:
        """Check if prompt asks for error handling"""
        error_keywords = ['error', 'exception', 'handle', 'validate', 'check']
        return any(kw in self.prompt_lower for kw in error_keywords)
    
    def _detect_missing_error_handling(self) -> List[str]:
        """Check if requested error handling exists"""
        missing = []
        
        if self.ast_analyzer:
            if not self.ast_analyzer.has_try_except():
                missing.append("error handling requested but not implemented")
        
        return missing
