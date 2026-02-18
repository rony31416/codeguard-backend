"""
Simple OpenRouter LLM Test
Test the free model before building 3-layer analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.linguistic.LLM_response import get_llm

print("\n" + "="*60)
print("OPENROUTER LLM TEST")
print("="*60 + "\n")

# Get LLM instance
llm = get_llm()

# Test 1: Check if alive
print("Test 1: Connection Test")
status = llm.is_alive()
print(f" Status: {status['status']}")
print(f" Message: {status['message']}")

if status['status'] == 'alive':
    print(f" Response: {status['response']}\n")
    print("-"*60 + "\n")
    
    # Test 2: Code analysis
    print("Test 2: Code Analysis")
    
    test_code = """def calculate_total(items):
    print("Calculating total...")  # Debug print
    total = 0
    for item in items:
        total += item
    return total

# Hardcoded example from prompt
result = calculate_total([10, 20, 30])
print(result)"""
    
    analysis = llm.analyze_code(
        prompt="Create a function to calculate total of items",
        code=test_code
    )
    
    if analysis['success']:
        print(f" Model: {analysis['model']}")
        print(f"\n Analysis:\n{analysis['analysis']}")
    else:
        print(f" Error: {analysis['error']}")
else:
    print(f"\n API not working: {status['message']}")

print("\n" + "="*60)
print("Ready to build 3-layer analysis!")
print("="*60 + "\n")
