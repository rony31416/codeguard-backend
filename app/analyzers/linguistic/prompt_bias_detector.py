"""
Detect hardcoded values from prompt examples (Prompt-Biased Code)
Enhanced with 3-layer cascade architecture
"""
import re
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .layers import RuleEngine, ASTAnalyzer, LLMReasoner, LayerAggregator


class PromptBiasDetector(BaseDetector):
    """Detect prompt-biased code (hardcoded example values) using 3-layer cascade"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        
        # Initialize 3-layer architecture
        self.rule_engine = RuleEngine()
        self.ast_analyzer = ASTAnalyzer()
        self.llm_reasoner = LLMReasoner()
        self.aggregator = LayerAggregator()
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method using 3-layer cascade with aggregation"""
        # LAYER 1: Rule Engine (Fast pattern matching ~10ms, 95% confidence)
        layer1_result = self.rule_engine.detect_prompt_bias(self.code, self.prompt)
        
        # LAYER 2: AST Analyzer (Structural verification ~50ms, 100% confidence)
        layer2_result = None
        if self.code_ast and layer1_result.get('issues'):
            layer2_result = self.ast_analyzer.verify_prompt_bias(self.code, self.prompt)
        
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
            "values": aggregated['findings'],
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
    
    def _detect_string_literals(self) -> List[str]:
        """Extract quoted strings from prompt and check if hardcoded"""
        hardcoded = []
        
        # Extract examples from prompt
        prompt_examples = []
        
        # Pattern 1: Quoted strings
        prompt_examples.extend(re.findall(r'["\']([^"\']{3,})["\']', self.prompt))
        
        # Pattern 2: "e.g., Example"
        prompt_examples.extend(re.findall(r'e\.g\.,?\s+["\']?([a-zA-Z_][a-zA-Z0-9_]{2,})["\']?', self.prompt, re.IGNORECASE))
        
        # Pattern 3: "for example: value"
        prompt_examples.extend(re.findall(r'example[:\s]+["\']?([a-zA-Z_][a-zA-Z0-9_]{2,})["\']?', self.prompt, re.IGNORECASE))
        
        # Pattern 4: "like 'value'"
        prompt_examples.extend(re.findall(r'like\s+["\']([^"\']+)["\']', self.prompt, re.IGNORECASE))
        
        # Check if examples are hardcoded in comparisons
        for example in prompt_examples:
            if example and len(example) > 2:
                # Check for hardcoded equality checks
                patterns = [
                    f'== "{example}"',
                    f"== '{example}'",
                    f'== {example}',
                    f'if "{example}"',
                    f"if '{example}'"
                ]
                
                if any(pattern in self.code for pattern in patterns):
                    hardcoded.append(f'string: "{example}"')
        
        return hardcoded
    
    def _detect_magic_numbers(self) -> List[str]:
        """Detect hardcoded numbers from prompt examples"""
        hardcoded = []
        
        # Extract numbers from prompt
        prompt_numbers = re.findall(r'\b(\d+)\b', self.prompt)
        
        # Check if these numbers appear in conditionals
        for num in set(prompt_numbers):
            # Skip common numbers (0, 1, 2)
            if int(num) <= 2:
                continue
            
            # Check if number is in a condition
            conditional_patterns = [
                f'== {num}',
                f'> {num}',
                f'< {num}',
                f'>= {num}',
                f'<= {num}',
                f'!= {num}'
            ]
            
            if any(pattern in self.code for pattern in conditional_patterns):
                hardcoded.append(f'magic number: {num}')
        
        return hardcoded
    
    def _detect_ast_comparisons(self) -> List[str]:
        """Use AST to find hardcoded comparisons"""
        hardcoded = []
        
        # Get all string constants from prompt
        prompt_strings = set(re.findall(r'["\']([^"\']{3,})["\']', self.prompt))
        
        # Find all comparison nodes in code
        for node in ast.walk(self.code_ast):
            if isinstance(node, ast.Compare):
                # Check if comparing with a constant
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant):
                        value = comparator.value
                        
                        # If string constant matches prompt example
                        if isinstance(value, str) and value in prompt_strings:
                            hardcoded.append(f'hardcoded comparison: "{value}"')
                        
                        # If numeric constant from prompt
                        elif isinstance(value, (int, float)):
                            if str(value) in self.prompt:
                                hardcoded.append(f'hardcoded number in condition: {value}')
        
        return hardcoded
