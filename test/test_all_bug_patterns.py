"""
Comprehensive Test Suite for All 10 Bug Patterns
Based on real VSCode extension testing results
"""
import ast
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.linguistic.npc_detector import NPCDetector
from app.analyzers.linguistic.prompt_bias_detector import PromptBiasDetector
from app.analyzers.linguistic.missing_feature_detector import MissingFeatureDetector
from app.analyzers.linguistic.misinterpretation_detector import MisinterpretationDetector


class BugPatternTest:
    def __init__(self, name, prompt, code, expected_detectors):
        self.name = name
        self.prompt = prompt
        self.code = code
        self.expected_detectors = expected_detectors  # Which detectors should fire


# Test cases documented from VSCode extension testing
TEST_CASES = [
    # Pattern 1: Hallucinated Object
    BugPatternTest(
        name="Hallucinated Object",
        prompt="Write a Python function that calculates the area of a circle given its radius.",
        code="""def area(radius):
    return math_magic.pi * radius * radius""",
        expected_detectors=["missing_features"]  # Missing import
    ),
    
    # Pattern 2: Wrong Attribute  
    BugPatternTest(
        name="Wrong Attribute",
        prompt="Create a function that returns the username from a user dictionary.",
        code="""def get_username(user):
    return user.name""",
        expected_detectors=["missing_features"]  # Should use dict access
    ),
    
    # Pattern 3: Non-Prompted Consideration (NPC)
    BugPatternTest(
        name="Non-Prompted Consideration (NPC)",
        prompt="Write a function to multiply two numbers.",
        code="""def multiply(a, b):
    print("Multiplying numbers...")  
    import logging
    logging.info("Multiplication started")
    return a * b""",
        expected_detectors=["npc"]  # Unrequested logging and print
    ),
    
    # Pattern 4: Prompt-Biased Code  
    BugPatternTest(
        name="Prompt-Biased Code",
        prompt="Sort this list: [5, 2, 9]",
        code="""def sort_numbers():
    nums = [5, 2, 9]
    return sorted(nums)""",
        expected_detectors=["prompt_bias", "npc"]  # Hardcoded values + extra function
    ),
    
    # Pattern 5: Missing Features
    BugPatternTest(
        name="Missing Features",
        prompt="Write a function that returns the square and cube of a number.",
        code="""def powers(n):
    return n*n""",
        expected_detectors=["missing_features"]  # Missing cube
    ),
    
    # Pattern 6: Missing Corner Case
    BugPatternTest(
        name="Missing Corner Case",
        prompt="Write a function to return the first element of a list.",
        code="""def first(lst):
    return lst[0]""",
        expected_detectors=[]  # This is detected by static analysis, not linguistic
    ),
    
    # Pattern 7: Misinterpretation (FIXED!)
    BugPatternTest(
        name="Misinterpretation - Print vs Return",
        prompt="Write a function that returns the sum of two numbers.",
        code="""def add(a, b):
    print(a + b)""",
        expected_detectors=["misinterpretation"]  # Should return, not print
    ),
    
    # Pattern 8: Silly Mistake (FIXED!)
    BugPatternTest(
        name="Silly Mistake - Wrong Exponent",
        prompt="Write a function that returns the square of a number.",
        code="""def square(n):
    return n ** 3""",
        expected_detectors=["missing_features"]  # Wrong operation (cube vs square)
    ),
]


def test_pattern(test_case: BugPatternTest):
    """Test a single bug pattern"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_case.name}")
    print(f"{'='*80}")
    print(f"Prompt: {test_case.prompt[:70]}...")
    print(f"Expected Detectors: {', '.join(test_case.expected_detectors) if test_case.expected_detectors else 'None (static only)'}")
    
    # Parse code
    try:
        code_ast = ast.parse(test_case.code)
    except SyntaxError:
        code_ast = None
    
    # Run all detectors
    detectors = {
        "npc": NPCDetector(test_case.prompt, test_case.code, code_ast),
        "prompt_bias": PromptBiasDetector(test_case.prompt, test_case.code, code_ast),
        "missing_features": MissingFeatureDetector(test_case.prompt, test_case.code, code_ast),
        "misinterpretation": MisinterpretationDetector(test_case.prompt, test_case.code, code_ast)
    }
    
    results = {}
    for name, detector in detectors.items():
        results[name] = detector.detect()
    
    # Display results
    print(f"\n📊 Detection Results:")
    detected = []
    
    for name, result in results.items():
        if result.get('found', False):
            detected.append(name)
            count = result.get('count', result.get('score', 0))
            confidence = result.get('confidence', 0)
            verdict = result.get('verdict_by', 'N/A')
            
            print(f"  ✅ {name.upper()}: FOUND")
            print(f"     Count: {count}, Confidence: {confidence:.2f}, Verdict: {verdict}")
            
            # Show details
            if name == 'npc' and result.get('features'):
                print(f"     Features: {result['features'][:2]}")
            elif name == 'prompt_bias' and result.get('values'):
                print(f"     Values: {result['values'][:2]}")
            elif name == 'missing_features' and result.get('features'):
                print(f"     Missing: {result['features'][:2]}")
            elif name == 'misinterpretation' and result.get('reasons'):
                print(f"     Reasons: {result['reasons'][:1]}")
    
    # Verification
    print(f"\n🎯 Verification:")
    if set(detected) >= set(test_case.expected_detectors):
        print(f"  ✅ PASS - All expected detectors found!")
        return True
    else:
        missing = set(test_case.expected_detectors) - set(detected)
        unexpected = set(detected) - set(test_case.expected_detectors)
        
        if missing:
            print(f"  ⚠️  Missing: {', '.join(missing)}")
        if unexpected:
            print(f"  ℹ️  Also found: {', '.join(unexpected)}")
        
        return False


def run_all_tests():
    """Run all test cases"""
    print("\n" + "🚀 "*40)
    print("COMPREHENSIVE BUG PATTERN TEST SUITE")
    print("Testing all 8 linguistic bug patterns with real VSCode extension examples")
    print("🚀 "*40)
    
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        try:
            if test_pattern(test_case):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*80}")
    print(f"✅ Passed: {passed}/{len(TEST_CASES)}")
    print(f"❌ Failed: {failed}/{len(TEST_CASES)}")
    
    accuracy = (passed / len(TEST_CASES)) * 100 if TEST_CASES else 0
    print(f"📈 Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print(f"\n🎉 EXCELLENT! System is production-ready!")
    elif accuracy >= 75:
        print(f"\n✅ GOOD! Minor tuning needed.")
    else:
        print(f"\n⚠️  Needs improvement - review failed cases.")
    
    print(f"\n{'='*80}\n")
    
    return passed == len(TEST_CASES)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
