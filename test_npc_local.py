"""
Test NPC Detection Locally
"""
from app.analyzers.linguistic_analyzer import LinguisticAnalyzer
import json

prompt = "Write a simple function to add two numbers and return the result"

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
print("TESTING NPC DETECTION LOCALLY")
print("=" * 60)
print(f"\nPrompt: {prompt}")
print(f"\nCode:\n{code}")
print("\n" + "=" * 60)
print("LINGUISTIC ANALYSIS RESULTS:")
print("=" * 60)

analyzer = LinguisticAnalyzer(prompt, code)
result = analyzer.analyze()

print(json.dumps(result, indent=2))

# Check NPC detection
if result.get('npc'):
    npc_data = result['npc']
    print("\n✅ NPC DETECTED!")
    print(f"Count: {len(npc_data.get('npc_features', []))}")
    print(f"Features: {npc_data.get('npc_features', [])}")
else:
    print("\n❌ NPC NOT DETECTED!")
