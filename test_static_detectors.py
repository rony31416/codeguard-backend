"""
Test Suite for Static Analysis Detectors
=========================================
Comprehensive tests for all 9 static analysis detectors.
"""

import sys
sys.path.insert(0, 'F:/Codeguard/backend')

from app.analyzers.static import StaticAnalyzer
from app.analyzers.static.detectors import (
    SyntaxErrorDetector,
    HallucinatedObjectDetector,
    IncompleteGenerationDetector,
    SillyMistakeDetector,
    WrongAttributeDetector,
    WrongInputTypeDetector,
    PromptBiasDetector,
    NPCDetector,
    CornerCaseDetector
)


def print_header(title):
    """Print test section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(pattern_name, result, expected=True):
    """Print test result."""
    found = result.get('found', False)
    status = "✅ PASS" if found == expected else "❌ FAIL"
    print(f"{status} | {pattern_name}: Found={found} (Expected={expected})")
    
    if found:
        if 'error' in result and result['error']:
            print(f"     └─ Error: {result['error']}")
        if 'details' in result:
            print(f"     └─ Details: {len(result['details'])} issues")
            for detail in result['details'][:3]:
                print(f"        • {detail}")
        if 'objects' in result:
            print(f"     └─ Objects: {len(result['objects'])} found")
            for obj in result['objects'][:3]:
                print(f"        • {obj}")


def test_syntax_error():
    """Test #1: Syntax Error Detection"""
    print_header("TEST #1: Syntax Error Detector")
    
    # Buggy code (missing colon)
    buggy_code = """
def calculate_total(items)  # Missing colon here
    total = 0
    for item in items:
        total += item
    return total
"""
    
    detector = SyntaxErrorDetector(buggy_code)
    result = detector.detect()
    print_result("Syntax Error (Missing Colon)", result, expected=True)
    
    # Good code
    good_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
"""
    
    detector = SyntaxErrorDetector(good_code)
    result = detector.detect()
    print_result("Syntax Error (Good Code)", result, expected=False)


def test_hallucinated_objects():
    """Test #2: Hallucinated Object Detection"""
    print_header("TEST #2: Hallucinated Object Detector")
    
    # Buggy code (undefined class)
    buggy_code = """
def process_data():
    validator = DataValidator()  # This class doesn't exist
    cleaner = DataCleaner()      # This class doesn't exist
    return validator.validate()
"""
    
    detector = HallucinatedObjectDetector(buggy_code)
    result = detector.detect()
    print_result("Hallucinated Objects", result, expected=True)
    
    # Good code
    good_code = """
class DataValidator:
    pass

def process_data():
    validator = DataValidator()
    return validator
"""
    
    detector = HallucinatedObjectDetector(good_code)
    result = detector.detect()
    print_result("Hallucinated Objects (Good Code)", result, expected=False)


def test_incomplete_generation():
    """Test #3: Incomplete Generation Detection"""
    print_header("TEST #3: Incomplete Generation Detector")
    
    # Buggy code (incomplete assignment)
    buggy_code = """
def process_order():
    total = 
    items = []
    # TODO: Complete this function
    for item in items:
        pass
    return total
"""
    
    detector = IncompleteGenerationDetector(buggy_code)
    result = detector.detect()
    print_result("Incomplete Generation", result, expected=True)
    
    # Good code
    good_code = """
def process_order():
    total = 0
    items = []
    for item in items:
        total += item
    return total
"""
    
    detector = IncompleteGenerationDetector(good_code)
    result = detector.detect()
    print_result("Incomplete Generation (Good Code)", result, expected=False)


def test_silly_mistakes():
    """Test #4: Silly Mistake Detection"""
    print_header("TEST #4: Silly Mistake Detector")
    
    # Buggy code (identical if/else branches)
    buggy_code = """
def calculate_discount(price, is_member):
    if is_member:
        final_price = price * 0.9
        return final_price
    else:
        final_price = price * 0.9  # Same as if branch!
        return final_price
"""
    
    detector = SillyMistakeDetector(buggy_code)
    result = detector.detect()
    print_result("Silly Mistake (Identical Branches)", result, expected=True)
    
    # Good code
    good_code = """
def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    else:
        return price
"""
    
    detector = SillyMistakeDetector(good_code)
    result = detector.detect()
    print_result("Silly Mistake (Good Code)", result, expected=False)


def test_wrong_attribute():
    """Test #5: Wrong Attribute Detection"""
    print_header("TEST #5: Wrong Attribute Detector")
    
    # Buggy code (dict.key instead of dict['key'])
    buggy_code = """
def get_item_cost(item):
    return item.cost  # Should be item['cost']
"""
    
    detector = WrongAttributeDetector(buggy_code)
    result = detector.detect()
    print_result("Wrong Attribute (dict.key)", result, expected=True)
    
    # Good code
    good_code = """
def get_item_cost(item):
    return item['cost']
"""
    
    detector = WrongAttributeDetector(good_code)
    result = detector.detect()
    print_result("Wrong Attribute (Good Code)", result, expected=False)


def test_wrong_input_type():
    """Test #6: Wrong Input Type Detection"""
    print_header("TEST #6: Wrong Input Type Detector")
    
    # Buggy code (string to math function)
    buggy_code = """
import math

def calculate_square_root(value):
    result = math.sqrt("16")  # String instead of number!
    return result
"""
    
    detector = WrongInputTypeDetector(buggy_code)
    result = detector.detect()
    print_result("Wrong Input Type (String to math.sqrt)", result, expected=True)
    
    # Good code
    good_code = """
import math

def calculate_square_root(value):
    result = math.sqrt(16)
    return result
"""
    
    detector = WrongInputTypeDetector(good_code)
    result = detector.detect()
    print_result("Wrong Input Type (Good Code)", result, expected=False)


def test_prompt_bias():
    """Test #7: Prompt Bias Detection"""
    print_header("TEST #7: Prompt Bias Detector")
    
    # Buggy code (hardcoded example filename)
    buggy_code = """
def process_file(filename):
    if filename == "orders_demo.csv":  # Hardcoded example!
        return "Processing demo file"
    return "Processing regular file"
"""
    
    detector = PromptBiasDetector(buggy_code)
    result = detector.detect()
    print_result("Prompt Bias (Hardcoded Example)", result, expected=True)
    
    # Good code
    good_code = """
def process_file(filename):
    if filename.endswith('.csv'):
        return "Processing CSV file"
    return "Processing file"
"""
    
    detector = PromptBiasDetector(good_code)
    result = detector.detect()
    print_result("Prompt Bias (Good Code)", result, expected=False)


def test_npc():
    """Test #8: NPC (Non-Prompted Consideration) Detection"""
    print_header("TEST #8: NPC Detector")
    
    # Buggy code (unrequested security check)
    buggy_code = """
def add_user(username, email):
    if username == "admin":  # Unrequested admin check!
        raise PermissionError("Cannot add admin users")
    return {"username": username, "email": email}
"""
    
    detector = NPCDetector(buggy_code)
    result = detector.detect()
    print_result("NPC (Unrequested Feature)", result, expected=True)
    
    # Good code
    good_code = """
def add_user(username, email):
    return {"username": username, "email": email}
"""
    
    detector = NPCDetector(good_code)
    result = detector.detect()
    print_result("NPC (Good Code)", result, expected=False)


def test_corner_case():
    """Test #9: Missing Corner Case Detection"""
    print_header("TEST #9: Corner Case Detector")
    
    # Buggy code (division without zero check)
    buggy_code = """
def calculate_average(numbers):
    total = sum(numbers)
    average = total / len(numbers)  # No empty list check!
    return average
"""
    
    detector = CornerCaseDetector(buggy_code)
    result = detector.detect()
    print_result("Missing Corner Case (No Zero Check)", result, expected=True)
    
    # Good code
    good_code = """
def calculate_average(numbers):
    if not numbers:
        return 0.0
    total = sum(numbers)
    average = total / len(numbers)
    return average
"""
    
    detector = CornerCaseDetector(good_code)
    result = detector.detect()
    print_result("Missing Corner Case (Good Code)", result, expected=False)


def test_orchestrator():
    """Test #10: StaticAnalyzer Orchestrator (All Detectors)"""
    print_header("TEST #10: StaticAnalyzer Orchestrator")
    
    # Code with multiple bugs
    buggy_code = """
import math

def process_orders(orders)  # Missing colon (syntax error)
    validator = OrderValidator()  # Undefined class (hallucination)
    
    total = 
    
    for order in orders:
        discount = order.price - 0.1  # Should be price * 0.9 (reversed operands)
        cost = order.cost  # Should be order['cost'] (wrong attribute)
        sqrt_val = math.sqrt("100")  # String to math function (wrong type)
    
    if filename == "demo_orders.csv":  # Hardcoded example (prompt bias)
        pass
    
    return total / len(orders)  # No zero check (corner case)
"""
    
    print("\n🔍 Analyzing code with MULTIPLE bugs...")
    analyzer = StaticAnalyzer(buggy_code)
    results = analyzer.analyze()
    
    print("\n📊 ORCHESTRATOR RESULTS:")
    print("-" * 70)
    
    bug_count = 0
    for pattern, result in results.items():
        if result.get('found'):
            bug_count += 1
            symbol = "🔴"
        else:
            symbol = "🟢"
        
        print(f"{symbol} {pattern.replace('_', ' ').title()}: {result.get('found', False)}")
        
        if result.get('error'):
            print(f"   └─ {result['error'][:80]}")
    
    print("-" * 70)
    print(f"\n📈 TOTAL BUGS DETECTED: {bug_count}/9 patterns")
    
    # Expected: Should detect syntax, hallucination, incomplete, silly, wrong_attr, wrong_type, prompt_bias, corner_case
    expected_min = 5  # At least 5 should be detected
    if bug_count >= expected_min:
        print(f"✅ PASS: Detected {bug_count} bugs (Expected: ≥{expected_min})")
    else:
        print(f"❌ FAIL: Only detected {bug_count} bugs (Expected: ≥{expected_min})")


def main():
    """Run all tests."""
    print("\n" + "🧪" * 35)
    print("  STATIC ANALYSIS DETECTORS - COMPREHENSIVE TEST SUITE")
    print("🧪" * 35)
    
    try:
        test_syntax_error()
        test_hallucinated_objects()
        test_incomplete_generation()
        test_silly_mistakes()
        test_wrong_attribute()
        test_wrong_input_type()
        test_prompt_bias()
        test_npc()
        test_corner_case()
        test_orchestrator()
        
        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS COMPLETED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
