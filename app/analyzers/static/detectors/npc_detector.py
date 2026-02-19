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
        Detect non-prompted considerations (EXTREMELY conservative).
        
        Returns:
            Dict with detection results containing:
                - found: bool
                - details: List[Dict] (line, description)
        """
        npc_issues = []
        
        # ONLY detect OBVIOUS, unrequested additions (be very strict)
        # Standard implementation details (like due_date for checkout) are NOT NPC
        for i, line in enumerate(self.lines):
            # Pattern 1: Explicit security/permission checks with role hardcoding
            # Only flag if it checks for specific hardcoded roles like "admin", "root"
            if 'raise' in line and ('== "admin"' in line or '== "root"' in line or '== "superuser"' in line):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added hardcoded admin/role check not requested"
                })
            
            # Pattern 2: Arbitrary threshold validation with very high numbers (1000+)
            # Only flag extremely specific/arbitrary limits
            import re
            if re.search(r'if.*>\s*(1000|10000|100000).*raise', line):
                npc_issues.append({
                    "line": i + 1,
                    "description": "Added arbitrary high-value threshold validation not requested"
                })
        
        return {
            "found": len(npc_issues) > 0,
            "details": npc_issues
        }
