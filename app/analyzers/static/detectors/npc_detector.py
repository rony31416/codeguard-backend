"""
NPC Detector (Static)
=====================
Detects non-prompted considerations (unrequested features).

Pattern: Non-Prompted Consideration (NPC)
Severity: Variable (3-6/10)
Speed: ~5ms
"""

from typing import Dict, Any, List


class NPCDetector:
    """Detects unrequested features in code."""
    
    def __init__(self, code: str):
        """
        Initialize detector.
        
        Args:
            code: Source code to analyze
        """
        self.code = code
        self.lines = code.split('\n')
    
    def detect(self) -> Dict[str, Any]:
        """
        Detect non-prompted considerations (very conservative).
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (line, description)
        """
        npc_issues = []
        
        # Only detect obvious, unrequested additions
        for i, line in enumerate(self.lines):
            # Pattern 1: Security/auth checks not requested
            if 'raise' in line and any(word in line.lower() for word in ['admin', 'security', 'permission', 'auth']):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added security/authentication logic not requested"
                })
            
            # Pattern 2: Arbitrary threshold validation
            import re
            if re.search(r'if.*>\s*\d{3,}.*raise', line):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added arbitrary threshold validation not requested"
                })
        
        return {
            "found": len(npc_issues) > 0,
            "details": npc_issues
        }
