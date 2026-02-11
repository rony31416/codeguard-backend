from typing import List
from ..schemas import BugPatternSchema

class ExplainabilityLayer:
    @staticmethod
    def generate_summary(bug_patterns: List[BugPatternSchema]) -> str:
        """Generate a human-readable summary of the analysis"""
        if not bug_patterns or all(p.pattern_name == "No Bugs Detected" for p in bug_patterns):
            return "No obvious bugs detected in static and dynamic analysis. Code appears syntactically correct and executes without runtime errors."
        
        bug_count = len([p for p in bug_patterns if p.pattern_name != "No Bugs Detected"])
        max_severity = max(p.severity for p in bug_patterns)
        
        severity_label = "Critical" if max_severity >= 8 else "High" if max_severity >= 6 else "Medium" if max_severity >= 4 else "Low"
        
        pattern_names = [p.pattern_name for p in bug_patterns if p.pattern_name != "No Bugs Detected"]
        
        summary = f"Found {bug_count} bug pattern(s) with {severity_label} severity.\n\nDetected patterns:\n"
        for i, pattern in enumerate(pattern_names, 1):
            summary += f"{i}. {pattern}\n"
        summary += "\nReview the detailed analysis below for explanations and fix suggestions."
        
        return summary
