"""
Test script for the new Linguistic Analysis system
Tests all 4 detectors with sample prompt-code pairs
"""

import sys
sys.path.append('F:\\Codeguard\\backend')

from app.analyzers.linguistic_analyzer import LinguisticAnalyzer
import json


def test_npc_detection():
    """Test Non-Prompted Consideration detection"""
    print("\n" + "="*60)
    print("TEST 1: NPC (Non-Prompted Consideration) Detection")
    print("="*60)
    
    prompt = "Write a function that calculates the sum of two numbers"
    code = """
def calculate_sum(a, b):
    # Add logging (NOT REQUESTED!)
    print(f"Calculating sum of {a} and {b}")
    
    # Add validation (NOT REQUESTED!)
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Inputs must be numbers")
    
    # Add sorting (NOT REQUESTED!)
    result = sorted([a, b])[0] + sorted([a, b])[1]
    return result
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\nPrompt: {prompt}")
    print(f"\nNPC Detection Result:")
    print(json.dumps(result['npc'], indent=2))
    print(f"\nIntent Match Score: {result['intent_match_score']}")


def test_prompt_bias_detection():
    """Test Prompt-Biased Code detection"""
    print("\n" + "="*60)
    print("TEST 2: Prompt-Biased Code Detection")
    print("="*60)
    
    prompt = "Write a function to check if item name is valid. For example, 'Example_Item_A' should return True."
    code = """
def is_valid_item(name):
    # HARDCODED the example value!
    if name == "Example_Item_A":
        return True
    return False
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\nPrompt: {prompt}")
    print(f"\nPrompt-Biased Detection Result:")
    print(json.dumps(result['prompt_biased'], indent=2))


def test_missing_features_detection():
    """Test Missing Features detection"""
    print("\n" + "="*60)
    print("TEST 3: Missing Features Detection")
    print("="*60)
    
    prompt = "Create a function that filters a list of numbers, removes duplicates, sorts them, and returns the result"
    code = """
def process_numbers(numbers):
    # Only filters, missing sort and dedup!
    result = [n for n in numbers if n > 0]
    return result
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\nPrompt: {prompt}")
    print(f"\nMissing Features Detection Result:")
    print(json.dumps(result['missing_features'], indent=2))


def test_misinterpretation_detection():
    """Test Misinterpretation detection"""
    print("\n" + "="*60)
    print("TEST 4: Misinterpretation Detection")
    print("="*60)
    
    prompt = "Write a function that returns a list of even numbers from 1 to 10"
    code = """
def get_numbers():
    # WRONG: Prints instead of returning!
    # WRONG: Returns string instead of list!
    for i in range(1, 11):
        if i % 2 == 0:
            print(i)
    return "2, 4, 6, 8, 10"
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\nPrompt: {prompt}")
    print(f"\nMisinterpretation Detection Result:")
    print(json.dumps(result['misinterpretation'], indent=2))


def test_complete_analysis():
    """Test complete analysis with all detectors"""
    print("\n" + "="*60)
    print("TEST 5: Complete Analysis")
    print("="*60)
    
    prompt = "Create a function to calculate factorial of a number"
    code = """
def factorial(n):
    if n == 5:  # PROMPT BIASED - hardcoded example value
        return 120
    
    # NPC - admin check not requested
    if not is_admin():
        raise PermissionError("Admin only")
    
    # Missing error handling for negative numbers
    result = 1
    for i in range(1, n + 1):
        result *= i
    
    # NPC - logging not requested
    print(f"Calculated factorial: {result}")
    return result
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\nPrompt: {prompt}")
    print(f"\n📊 COMPLETE ANALYSIS RESULT:")
    print(json.dumps(result, indent=2))


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 LINGUISTIC ANALYSIS TEST SUITE")
    print("="*60)
    
    try:
        test_npc_detection()
        test_prompt_bias_detection()
        test_missing_features_detection()
        test_misinterpretation_detection()
        test_complete_analysis()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
