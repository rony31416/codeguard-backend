"""
Detect features mentioned in prompt but missing in code
"""
import re
import ast
from typing import Dict, Any, List, Set
from .base_detector import BaseDetector
from .utils.keyword_extractor import KeywordExtractor
from .utils.ast_analyzer import ASTAnalyzer


class MissingFeatureDetector(BaseDetector):
    """Detect features requested but not implemented"""
    
    def __init__(self, prompt: str, code: str, code_ast: ast.AST = None):
        super().__init__(prompt, code, code_ast)
        self.keyword_extractor = KeywordExtractor()
        self.ast_analyzer = ASTAnalyzer(self.code_ast) if self.code_ast else None
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method"""
        missing_features = []
        
        # Method 1: Missing action verbs
        missing_features.extend(self._detect_missing_actions())
        
        # Method 2: Missing data types
        missing_features.extend(self._detect_missing_data_types())
        
        # Method 3: Missing return values
        missing_features.extend(self._detect_missing_returns())
        
        # Method 4: Missing error handling
        if self._is_error_handling_requested():
            missing_features.extend(self._detect_missing_error_handling())
        
        # Remove duplicates and limit
        missing_features = list(set(missing_features))[:5]
        
        return {
            "found": len(missing_features) > 0,
            "features": missing_features,
            "count": len(missing_features)
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
