"""
Test Static Analyzer Fix - Hallucinated Objects
"""
from app.analyzers.static_analyzer import StaticAnalyzer
import json

code = '''def add_numbers(a, b):
    # NPC Bug 1: Debug print (NOT requested)
    print(f"Debug: Adding {a} + {b}")
    
    # NPC Bug 2: Logging (NOT requested)
    import logging
    logging.info("Addition operation")
    
    # NPC Bug 3: Validation (NOT requested)
    if not isinstance(a, (int, float)):
        raise ValueError("Must be number")
    
    return a + b'''

print("=" * 60)
print("TESTING STATIC ANALYZER - HALLUCINATED OBJECTS")
print("=" * 60)
print(f"\nCode:\n{code}")
print("\n" + "=" * 60)
print("STATIC ANALYSIS RESULTS:")
print("=" * 60)

analyzer = StaticAnalyzer(code)
result = analyzer.analyze()

print(json.dumps(result['hallucinated_objects'], indent=2))

if result['hallucinated_objects']['found']:
    print(f"\n❌ HALLUCINATED OBJECTS DETECTED (WRONG!)")
    print(f"Objects: {[obj['name'] for obj in result['hallucinated_objects']['objects']]}")
else:
    print(f"\n✅ NO HALLUCINATED OBJECTS (CORRECT!)")
