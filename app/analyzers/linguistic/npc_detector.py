"""
Detect features added that weren't requested (NPC - Non-Prompted Consideration)
"""
import ast
from typing import Dict, Any, List
from .base_detector import BaseDetector
from .utils.keyword_extractor import KeywordExtractor


class NPCDetector(BaseDetector):
    """Detect Non-Prompted Considerations"""
    
    # Common NPC patterns
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
    
    def detect(self) -> Dict[str, Any]:
        """Main detection method"""
        unprompted_features = []
        
        # Method 1: Pattern matching
        unprompted_features.extend(self._pattern_based_detection())
        
        # Method 2: AST-based detection
        if self.code_ast:
            unprompted_features.extend(self._ast_based_detection())
        
        # Method 3: Keyword difference
        unprompted_features.extend(self._keyword_based_detection())
        
        # Remove duplicates
        unprompted_features = list(set(unprompted_features))
        
        return {
            "found": len(unprompted_features) > 0,
            "features": unprompted_features,
            "count": len(unprompted_features)
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
