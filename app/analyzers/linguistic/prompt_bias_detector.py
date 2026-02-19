"""
Detect hardcoded values from prompt examples (Prompt-Biased Code)
Enhanced with 3-layer evidence → LLM verdict architecture
"""
import re
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .layers import RuleEngine, ASTAnalyzer, LLMReasoner


class PromptBiasDetector(BaseDetector):
    """Detect prompt-biased code (hardcoded example values) using 3-layer cascade"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        
        # Initialize 3-layer architecture (NO aggregator needed)
        self.rule_engine = RuleEngine()
        self.ast_analyzer = ASTAnalyzer()
        self.llm_reasoner = LLMReasoner()
    
    def detect(self) -> Dict[str, Any]:
        """
        NEW 3-Stage Flow:
        Stage 1: Rule Engine collects evidence
        Stage 2: AST Analyzer collects evidence  
        Stage 3: LLM makes final verdict based on combined evidence
        """
        # LAYER 1: Rule Engine - Collect evidence (Fast pattern matching ~10ms)
        layer1_evidence = self.rule_engine.detect_prompt_bias(self.code, self.prompt)
        
        # LAYER 2: AST Analyzer - Collect evidence (Structural verification ~50ms)
        layer2_evidence = self.ast_analyzer.verify_prompt_bias(self.code, self.prompt) if self.code_ast else None
        
        # LAYER 3: LLM makes final verdict based on Layer 1 & 2 evidence (~300ms)
        final_verdict = self.llm_reasoner.final_verdict(
            prompt=self.prompt,
            code=self.code,
            layer1_evidence=layer1_evidence,
            layer2_evidence=layer2_evidence,
            detector_type='prompt_bias'
        )
        
        return final_verdict
    
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
