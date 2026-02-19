"""
Comprehensive Test Suite for All 10 Bug Patterns
Based on user's deployment test results
"""
import ast
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.static_analyzer import StaticAnalyzer
from app.analyzers.dynamic_analyzer import DynamicAnalyzer
from app.analyzers.classifier import TaxonomyClassifier
from app.analyzers.linguistic_analyzer import LinguisticAnalyzer


def test_pattern(name, prompt, code, expected_patterns):
    """Test a single bug pattern"""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"Expected: {', '.join(expected_patterns)}")
    
    # Run analysis
    static = StaticAnalyzer(code).analyze()
    dynamic_result = DynamicAnalyzer(code).analyze()
    dynamic = dynamic_result.get("classification", {})
    linguistic = LinguisticAnalyzer(prompt, code).analyze()
    
    # Classify
    classifier = TaxonomyClassifier(static, dynamic, linguistic)
    patterns = classifier.classify()
    
    # Get detected pattern names
    detected = [p.pattern_name for p in patterns]
    
    print(f"Detected: {', '.join(detected)}")
    
    # Check if all expected patterns were found
    success = all(exp in detected for exp in expected_patterns)
    
    if success:
        print("✅ PASS")
    else:
        missing = set(expected_patterns) - set(detected)
        extra = set(detected) - set(expected_patterns)
        if missing:
            print(f"❌ FAIL - Missing: {', '.join(missing)}")
        if extra:
            print(f"⚠️  Extra detected: {', '.join(extra)}")
    
    return success


def run_all_tests():
    """Run all 10 bug pattern tests"""
    print("\n" + "🚀 "*40)
    print("COMPREHENSIVE BUG PATTERN TEST SUITE - All 10 Patterns")
    print("🚀 "*40)
    
    tests = [
        # Test 1: Syntax Error
        {
            "name": "1. Syntax Error",
            "prompt": "Write a function to calculate the total price of items in a list.",
            "code": """def calculate_total(items)  # missing colon
    total = 0
    for item in items:
        total += item
    return total""",
            "expected": ["Syntax Error"]
        },
        
        # Test 2: Hallucinated Object
        {
            "name": "2. Hallucinated Object",
            "prompt": "Create a function that converts temperatures from Celsius to Fahrenheit.",
            "code": """def convert_c_to_f(c):
    converter = TemperatureConverter()  # class not defined/imported
    return converter.c_to_f(c)""",
            "expected": ["Hallucinated Object"]
        },
        
        # Test 3: Incomplete Generation
        {
            "name": "3. Incomplete Generation",
            "prompt": "Implement a function to check if a string is a palindrome.",
            "code": """def is_palindrome(text):
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        # model stopped here, rest of loop missing""",
            "expected": ["Incomplete Generation"]
        },
        
        # Test 4: Silly Mistake
        {
            "name": "4. Silly Mistake",
            "prompt": "Write a function that returns True if a number is positive, otherwise False.",
            "code": """def is_positive(x):
    if x > 0:
        return True
    else:
        return True  # both branches identical""",
            "expected": ["Silly Mistake"]
        },
        
        # Test 5: Wrong Attribute
        {
            "name": "5. Wrong Attribute",
            "prompt": "Create a function that returns the username from a user dictionary.",
            "code": """def get_username(user):
    return user.name  # should use dict access user['name']""",
            "expected": ["Wrong Attribute"]
        },
        
        # Test 6: Wrong Input Type
        {
            "name": "6. Wrong Input Type",
            "prompt": "Write a function that returns the square root of a number.",
            "code": """import math

def safe_sqrt(x):
    return math.sqrt("16")  # passes string instead of numeric""",
            "expected": ["Wrong Input Type"]
        },
        
        # Test 7: Non-Prompted Consideration (NPC)
        {
            "name": "7. Non-Prompted Consideration (NPC)",
            "prompt": "Write a function to sum a list of integers.",
            "code": """def sum_numbers(nums):
    nums.sort()  # unnecessary sorting, not requested
    total = 0
    for n in nums:
        total += n
    return total""",
            "expected": ["Non-Prompted Consideration (NPC)"]
        },
        
        # Test 8: Prompt-Biased Code
        {
            "name": "8. Prompt-Biased Code",
            "prompt": "Process orders from a file, for example 'orders_demo.csv'.",
            "code": """def process_orders(filename):
    if filename == "orders_demo.csv":  # hardcoded example from prompt
        with open("orders_demo.csv") as f:
            data = f.read()
        # ... process data ...
    else:
        return None""",
            "expected": ["Prompt-Biased Code"]
        },
        
        # Test 9: Missing Corner Case
        {
            "name": "9. Missing Corner Case",
            "prompt": "Write a function that returns the average of a list of numbers.",
            "code": """def average(nums):
    return sum(nums) / len(nums)  # fails when nums is empty""",
            "expected": ["Missing Corner Case"]
        },
        
        # Test 10: Misinterpretation
        {
            "name": "10. Misinterpretation",
            "prompt": "Implement a function to compute the median of a list of numbers.",
            "code": """def median(nums):
    # actually computes mean, not median
    return sum(nums) / len(nums)""",
            "expected": ["Misinterpretation"]
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test_pattern(test["name"], test["prompt"], test["code"], test["expected"]):
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
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    accuracy = (passed / len(tests)) * 100 if tests else 0
    print(f"📈 Accuracy: {accuracy:.1f}%")
    
    if accuracy == 100:
        print(f"\n🎉 PERFECT! All 10 patterns detected correctly!")
    elif accuracy >= 90:
        print(f"\n✅ EXCELLENT! System is production-ready!")
    elif accuracy >= 70:
        print(f"\n✅ GOOD! Minor tuning needed.")
    else:
        print(f"\n⚠️  Needs improvement - review failed cases.")
    
    print(f"\n{'='*80}\n")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
