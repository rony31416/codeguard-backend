# this is TODO, have to implement 

import re
import ast
from typing import Dict, Any, List, Set
import json

class LinguisticAnalyzer:
    """
    Stage 3: Linguistic Analysis - Compares prompt intent with code implementation
    
    Detects:
    1. NPC (Non-Prompted Consideration) - unrequested features
    2. Prompt-Biased Code - hardcoded example values
    3. Missing Corner Cases - features requested but not implemented
    4. Misinterpretation - fundamental intent mismatch
    """
    
    def __init__(self, prompt: str, code: str):
        self.prompt = prompt.lower()
        self.code = code
        self.prompt_keywords = self._extract_prompt_keywords()
        self.code_features = self._extract_code_features()
    
    def analyze(self) -> Dict[str, Any]:
        """Run linguistic analysis comparing prompt vs code"""
        results = {
            "npc": self._detect_npc(),
            "prompt_biased": self._detect_prompt_biased(),
            "missing_features": self._detect_missing_features(),
            "misinterpretation": self._detect_misinterpretation(),
            "intent_match_score": self._calculate_intent_match()
        }
        return results
    
    def _extract_prompt_keywords(self) -> Set[str]:
        """
        Extract key requirements from prompt
        TODO: Implement NLP-based keyword extraction
        For now: simple keyword matching
        """
        keywords = set()
        
        # Extract action verbs
        action_verbs = ['create', 'write', 'implement', 'calculate', 'return', 
                       'get', 'find', 'check', 'validate', 'sort', 'filter']
        for verb in action_verbs:
            if verb in self.prompt:
                keywords.add(verb)
        
        # Extract data types
        data_types = ['list', 'dict', 'string', 'int', 'float', 'tuple', 
                     'array', 'set', 'object']
        for dtype in data_types:
            if dtype in self.prompt:
                keywords.add(dtype)
        
        # Extract domain-specific terms
        # TODO: Add more sophisticated NLP extraction
        words = re.findall(r'\b\w+\b', self.prompt)
        keywords.update([w for w in words if len(w) > 4])
        
        return keywords
    
    def _extract_code_features(self) -> Set[str]:
        """
        Extract implemented features from code using AST
        TODO: Add more sophisticated feature detection
        """
        features = set()
        
        try:
            tree = ast.parse(self.code)
            
            # Extract function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        features.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        features.add(node.func.attr)
            
            # Extract imported modules
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        features.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        features.add(alias.name)
            
        except SyntaxError:
            # If code has syntax errors, fall back to regex
            features = set(re.findall(r'\b\w+\b', self.code))
        
        return features
    
    def _detect_npc(self) -> Dict[str, Any]:
        """
        Detect Non-Prompted Consideration (NPC)
        Features added that weren't requested
        
        TODO: Implement sophisticated diff analysis
        Examples:
        - Sorting when not asked
        - Security checks not requested
        - Logging not requested
        - Input validation beyond requirements
        """
        unprompted = []
        
        # Common NPC patterns
        npc_patterns = {
            'sorted': 'sorting',
            'raise Exception': 'exception raising',
            'admin': 'authentication/authorization',
            'log': 'logging',
            'print': 'debugging output',
            'assert': 'assertions',
            'validate': 'extra validation'
        }
        
        for pattern, feature_name in npc_patterns.items():
            if pattern in self.code and pattern not in self.prompt:
                unprompted.append(feature_name)
        
        # TODO: Add AST-based detection for:
        # - Try-except blocks not mentioned in prompt
        # - Security checks (if admin, if authorized)
        # - Performance optimizations not requested
        
        return {
            "found": len(unprompted) > 0,
            "features": unprompted
        }
    
    def _detect_prompt_biased(self) -> Dict[str, Any]:
        """
        Detect hardcoded values from prompt examples
        
        TODO: Implement example extraction from prompt
        Example: If prompt says "e.g., 'Example_Item_A'"
        and code has hardcoded check for "Example_Item_A"
        """
        hardcoded = []
        
        # Extract quoted strings from prompt (potential examples)
        prompt_examples = re.findall(r'["\']([^"\']+)["\']', self.prompt)
        
        # Check if these appear as hardcoded values in code
        for example in prompt_examples:
            if example in self.code:
                # Check if it's used in comparison (hardcoded logic)
                if f'== "{example}"' in self.code or f"== '{example}'" in self.code:
                    hardcoded.append(example)
        
        # TODO: Detect hardcoded magic numbers from examples
        # TODO: Detect hardcoded boundary values
        
        return {
            "found": len(hardcoded) > 0,
            "values": hardcoded
        }
    
    def _detect_missing_features(self) -> Dict[str, Any]:
        """
        Detect features mentioned in prompt but not in code
        
        TODO: Implement semantic matching
        """
        missing = []
        
        # Simple keyword matching for now
        # TODO: Use NLP to understand semantic equivalence
        for keyword in self.prompt_keywords:
            if keyword not in self.code.lower():
                missing.append(keyword)
        
        return {
            "found": len(missing) > 0,
            "features": missing[:5]  # Limit to top 5 to avoid noise
        }
    
    def _detect_misinterpretation(self) -> Dict[str, Any]:
        """
        Detect if code fundamentally misunderstands the task
        
        TODO: This is the hardest pattern to detect
        Requires understanding expected output vs actual output
        """
        misinterpretation_score = 0.0
        reasons = []
        
        # Heuristic 1: Prompt asks for return, code prints
        if 'return' in self.prompt and 'print' in self.code and 'return' not in self.code:
            misinterpretation_score += 0.3
            reasons.append("Returns nothing but prints instead")
        
        # Heuristic 2: Prompt asks for list, code returns string
        if 'list' in self.prompt and 'str' in self.code:
            misinterpretation_score += 0.2
            reasons.append("Wrong return type (string instead of list)")
        
        # TODO: Add more sophisticated heuristics
        # TODO: Use test case failures to confirm misinterpretation
        
        return {
            "found": misinterpretation_score > 0.5,
            "score": misinterpretation_score,
            "reasons": reasons
        }
    
    def _calculate_intent_match(self) -> float:
        """
        Calculate how well the code matches the prompt intent
        
        TODO: Implement proper semantic similarity
        For now: simple keyword overlap
        """
        prompt_words = set(self.prompt.split())
        code_words = set(self.code.lower().split())
        
        if not prompt_words:
            return 0.0
        
        overlap = len(prompt_words & code_words)
        match_score = overlap / len(prompt_words)
        
        return min(match_score, 1.0)
