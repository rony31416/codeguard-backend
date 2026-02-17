"""
Integration test for the entire CodeGuard analysis pipeline
Tests the full 3-stage analysis with linguistic analysis
"""

import sys
sys.path.append('F:\\Codeguard\\backend')

from app.analyzers.static_analyzer import StaticAnalyzer
from app.analyzers.classifier import TaxonomyClassifier
from app.analyzers.linguistic_analyzer import LinguisticAnalyzer
import json


def test_full_pipeline():
    """Test complete analysis pipeline"""
    print("\n" + "="*60)
    print("🔬 FULL PIPELINE TEST")
    print("="*60)
    
    # Real buggy LLM-generated code
    prompt = """
Write a Python function called 'get_even_numbers' that takes a list 
of integers and returns a list of only the even numbers, sorted in 
ascending order.
"""
    
    buggy_code = """
def get_evens(nums):
    # Wrong function name (should be get_even_numbers)
    # Added sorting (good!) 
    # But hardcoded the example from prompt
    if nums == [1,2,3,4,5]:  # PROMPT BIASED!
        return [2,4]
    
    # Added logging (NOT REQUESTED - NPC)
    print("Processing numbers:", nums)
    
    # Missing return statement - just prints
    for n in nums:
        if n % 2 = 0:  # SYNTAX ERROR: single = instead of ==
            print(n)  # Should return, not print
"""
    
    print("\n📝 Prompt:")
    print(prompt)
    print("\n🐛 Buggy Code:")
    print(buggy_code)
    
    # Stage 1: Static Analysis
    print("\n" + "="*60)
    print("STAGE 1: Static Analysis")
    print("="*60)
    static_analyzer = StaticAnalyzer(buggy_code)
    static_results = static_analyzer.analyze()
    
    # Count total issues found
    total_issues = 0
    for key, value in static_results.items():
        if isinstance(value, dict) and value.get('found'):
            total_issues += 1
            print(f"  ✓ {key}: {value.get('error') or value.get('objects') or 'Found'}")
    
    print(f"\nTotal static issues: {total_issues}")
    
    # Stage 2: Classification
    print("\n" + "="*60)
    print("STAGE 2: Bug Classification")
    print("="*60)
    
    # Create classifier with static results (no dynamic for this test)
    dynamic_results = {"timeout": False, "exit_code": 0, "stdout": "", "stderr": ""}
    linguistic_results_for_classifier = {}  # Will be populated in stage 3
    classifier = TaxonomyClassifier(static_results, dynamic_results, linguistic_results_for_classifier)
    
    # Get all detected patterns
    detected_patterns = classifier.classify()
    
    print(f"Detected {len(detected_patterns)} bug patterns:")
    for pattern in detected_patterns:
        print(f"  - {pattern.pattern_name}: Severity {pattern.severity}")
    
    classifications = detected_patterns
    
    # Stage 3: Linguistic Analysis
    print("\n" + "="*60)
    print("STAGE 3: Linguistic Analysis")
    print("="*60)
    linguistic_analyzer = LinguisticAnalyzer(prompt, buggy_code)
    linguistic_results = linguistic_analyzer.analyze()
    
    print(f"\n📊 Linguistic Results:")
    print(json.dumps(linguistic_results, indent=2))
    
    # Summary
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Static Issues: {total_issues}")
    print(f"Bug Classifications: {len(classifications)}")
    print(f"NPC Violations: {linguistic_results['npc']['count']}")
    print(f"Prompt-Biased Values: {linguistic_results['prompt_biased']['count']}")
    print(f"Missing Features: {linguistic_results['missing_features']['count']}")
    print(f"Misinterpretation Score: {linguistic_results['misinterpretation']['score']}")
    print(f"Intent Match Score: {linguistic_results['intent_match_score']}")
    
    print("\n✅ FULL PIPELINE TEST COMPLETED!")
    return True


if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
