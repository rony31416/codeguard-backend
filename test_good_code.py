"""Quick test for good code - should NOT report false positives"""
from app.analyzers.static_analyzer import StaticAnalyzer
from app.analyzers.dynamic_analyzer import DynamicAnalyzer
from app.analyzers.classifier import TaxonomyClassifier
from app.analyzers.linguistic_analyzer import LinguisticAnalyzer

prompt = """Write a Python function calculate_average that takes a list of numbers as input and returns their average. Handle the case where the input list is empty by returning 0. Ensure the function works with both integers and floats"""

code = """def calculate_average(numbers):
    \"\"\"
    Calculates the average of a list of numbers.
    Returns 0 if the list is empty.
    \"\"\"
    if not numbers:
        return 0.0
    
    total = sum(numbers)
    average = total / len(numbers)
    
    return average"""

print("Testing GOOD CODE (should have minimal/no bugs)...")
print("="*80)

# Run analysis
static = StaticAnalyzer(code).analyze()
dynamic_result = DynamicAnalyzer(code).analyze()
dynamic = dynamic_result.get("classification", {})
linguistic = LinguisticAnalyzer(prompt, code).analyze()

# Debug output
print("\n📊 Static Analysis Results:")
print(f"  - Prompt Biased: {static.get('prompt_biased', {}).get('found', False)}")
print(f"  - Missing Corner Case: {static.get('missing_corner_case', {}).get('found', False)}")

print("\n📊 Linguistic Analysis Results:")
print(f"  - Missing Features: {linguistic.get('missing_features', {}).get('found', False)}")
if linguistic.get('missing_features', {}).get('found'):
    print(f"    Features: {linguistic['missing_features'].get('features', [])}")

# Classify
classifier = TaxonomyClassifier(static, dynamic, linguistic)
patterns = classifier.classify()

print(f"\n🎯 FINAL RESULT:")
print(f"  Found {len(patterns)} bug pattern(s)")

if patterns:
    print(f"\n  Detected patterns:")
    for p in patterns:
        print(f"    - {p.pattern_name} (Severity: {p.severity}/10)")
        print(f"      {p.description}")
else:
    print(f"  ✅ No bugs detected - CORRECT!")

print("\n" + "="*80)

# Expected: Should find 0 bugs or very minimal
if len(patterns) == 0:
    print("✅ PASS - Good code correctly identified as bug-free!")
elif len(patterns) <= 1:
    print("⚠️  ACCEPTABLE - Only 1 minor issue found")
else:
    print(f"❌ FAIL - Found {len(patterns)} false positives in good code!")
    print("\nThis is GOOD code that correctly implements the requirements.")
    print("The system should not report bugs here.")
