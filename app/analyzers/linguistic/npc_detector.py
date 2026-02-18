"""
Detect features added that weren't requested (NPC - Non-Prompted Consideration)
Enhanced with 3-layer cascade architecture
"""
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .utils.keyword_extractor import KeywordExtractor
from .layers import RuleEngine, ASTAnalyzer, LLMReasoner, LayerAggregator


class NPCDetector(BaseDetector):
    """Detect Non-Prompted Considerations using 3-layer cascade"""
    
    # Common NPC patterns (kept for backward compatibility)
    NPC_PATTERNS = {
        'sorted': 'sorting',
        'sort(': 'sorting',
        '.sort': 'sorting',
        'raise': 'exception raising',
        'Exception': 'exception handling',
        'admin': 'admin checks',
        'auth': 'authentication',
        'permission': 'permission checks',
        'role': 'role-based access',
        'log': 'logging',
        'logger': 'logging',
        'print(': 'debugging output',
        'assert': 'assertions',
        'validate': 'validation',
        'cache': 'caching',
        '@lru_cache': 'memoization',
        'lock': 'thread locking',
        'mutex': 'synchronization',
        'semaphore': 'synchronization'
    }
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        self.keyword_extractor = KeywordExtractor()
        self.prompt_keywords = self.keyword_extractor.extract_from_prompt(prompt)
        
        # Initialize 3-layer architecture
        self.rule_engine = RuleEngine()
        self.ast_analyzer = ASTAnalyzer()
        self.llm_reasoner = LLMReasoner()
        self.aggregator = LayerAggregator()
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method using 3-layer cascade with aggregation"""
        # LAYER 1: Rule Engine (Fast pattern matching ~10ms, 95% confidence)
        layer1_result = self.rule_engine.detect_npc(self.code)
        
        # LAYER 2: AST Analyzer (Structural verification ~50ms, 100% confidence)
        layer2_result = None
        if self.code_ast and layer1_result.get('issues'):
            layer2_result = self.ast_analyzer.verify_npc(self.code)
        
        # LAYER 3: LLM Reasoner (Deep semantic analysis ~300ms, 98% confidence)
        layer3_result = None
        if layer1_result.get('confidence', 0) < 0.98 and layer1_result.get('issues'):
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
        
        # Return aggregated results in expected format
        return {
            "found": aggregated['found'],
            "features": aggregated['findings'],
            "count": aggregated['count'],
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
    
    def _pattern_based_detection(self) -> List[str]:
        """Check for common NPC patterns in code"""
        found = []
        
        for pattern, feature_name in self.NPC_PATTERNS.items():
            if pattern in self.code and pattern.lower() not in self.prompt_lower:
                found.append(feature_name)
        
        return found
    
    def _ast_based_detection(self) -> List[str]:
        """Use AST to detect structural NPC"""
        found = []
        
        # 1. Try-except blocks not mentioned
        try_blocks = [node for node in ast.walk(self.code_ast) if isinstance(node, ast.Try)]
        if try_blocks and 'error' not in self.prompt_lower and 'exception' not in self.prompt_lower:
            found.append("error handling not requested")
        
        # 2. Security/admin checks
        for node in ast.walk(self.code_ast):
            if isinstance(node, ast.If):
                try:
                    # Python 3.9+
                    if hasattr(ast, 'unparse'):
                        condition_str = ast.unparse(node.test).lower()
                    else:
                        condition_str = ""
                    
                    security_keywords = ['admin', 'auth', 'permission', 'role', 'authorized']
                    if any(kw in condition_str for kw in security_keywords):
                        if not any(kw in self.prompt_lower for kw in security_keywords):
                            found.append("security checks not requested")
                            break
                except:
                    pass
        
        # 3. Performance optimizations (decorators)
        for node in ast.walk(self.code_ast):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if 'cache' in decorator.id.lower() or 'memo' in decorator.id.lower():
                            if 'cache' not in self.prompt_lower and 'optimize' not in self.prompt_lower:
                                found.append("performance optimization not requested")
        
        # 4. Logging statements
        log_calls = 0
        for node in ast.walk(self.code_ast):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if 'log' in node.func.attr.lower():
                        log_calls += 1
        
        if log_calls > 0 and 'log' not in self.prompt_lower:
            found.append("logging not requested")
        
        return found
    
    def _keyword_based_detection(self) -> List[str]:
        """Detect features in code not mentioned in prompt"""
        found = []
        
        # Extract code features
        code_keywords = self.keyword_extractor.extract_from_prompt(self.code)
        
        # Find code features not in prompt
        unprompted_keywords = code_keywords - self.prompt_keywords
        
        # Filter to significant additions only
        significant_additions = {
            'security', 'validation', 'optimization', 'caching', 
            'logging', 'monitoring', 'authentication'
        }
        
        for keyword in unprompted_keywords:
            if any(sig in keyword for sig in significant_additions):
                found.append(f"'{keyword}' feature not requested")
        
        return found
