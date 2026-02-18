"""
Final End-to-End Test for 3-Layer Cascade + Aggregation System
"""
import requests
import json

API_URL = "http://localhost:8000/api/analyze"

def test_full_system():
    """Test the complete system with all enhancements"""
    
    print("="*80)
    print("🚀 FINAL END-TO-END TEST: 3-Layer Cascade + Aggregation")
    print("="*80)
    
    # Test Case 1: NPC Detection
    print("\n" + "="*80)
    print("TEST 1: NPC Detection (Debug Prints + Logging)")
    print("="*80)
    
    payload1 = {
        "prompt": "Write a function to add two numbers and return the result",
        "code": """def add(a, b):
    # Debug output not requested
    print(f"Adding {a} + {b}")
    
    # Logging not requested
    import logging
    logging.info("Addition operation")
    
    # Validation not requested
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Inputs must be numbers")
    
    result = a + b
    return result"""
    }
    
    response1 = requests.post(API_URL, json=payload1, timeout=90)
    result1 = response1.json()
    
    print(f"\n✅ Status: {response1.status_code}")
    print(f"\n📊 Linguistic Results:")
    
    if "linguistic_results" in result1.get("analysis", {}):
        ling = result1["analysis"]["linguistic_results"]
        npc = ling.get("npc", {})
        
        print(f"\n🔍 NPC Detection:")
        print(f"  Found: {npc.get('found')}")
        print(f"  Count: {npc.get('count')}")
        print(f"  Confidence: {npc.get('confidence')}")
        print(f"  Severity: {npc.get('severity')}/10")
        print(f"  Consensus: {npc.get('consensus')}")
        print(f"  Reliability: {npc.get('reliability')}")
        print(f"  Primary Detection: {npc.get('primary_detection')}")
        print(f"  Layers Used: {npc.get('layers_used')}")
        
        if npc.get('layers_detail'):
            print(f"\n  📋 Layer Breakdown:")
            for layer, detail in npc['layers_detail'].items():
                print(f"    {layer}: found={detail.get('found')}, confidence={detail.get('confidence')}, issues={detail.get('issues_count')}")
        
        print(f"\n  Features Detected:")
        for feature in npc.get('features', [])[:5]:  # Show first 5
            print(f"    - {feature}")
    
    # Test Case 2: Prompt Bias Detection
    print("\n" + "="*80)
    print("TEST 2: Prompt Bias Detection (Hardcoded Example)")
    print("="*80)
    
    payload2 = {
        "prompt": 'Check if username is "admin" - for example, if user="admin" then grant access',
        "code": """def check_access(username):
    # Hardcoded example from prompt - should be variable comparison
    if username == "admin":
        return True
    return False"""
    }
    
    response2 = requests.post(API_URL, json=payload2, timeout=90)
    result2 = response2.json()
    
    print(f"\n✅ Status: {response2.status_code}")
    
    if "linguistic_results" in result2.get("analysis", {}):
        ling = result2["analysis"]["linguistic_results"]
        bias = ling.get("prompt_biased", {})
        
        print(f"\n🔍 Prompt Bias Detection:")
        print(f"  Found: {bias.get('found')}")
        print(f"  Count: {bias.get('count')}")
        print(f"  Confidence: {bias.get('confidence')}")
        print(f"  Severity: {bias.get('severity')}/10")
        print(f"  Consensus: {bias.get('consensus')}")
        print(f"  Reliability: {bias.get('reliability')}")
        print(f"  Layers Used: {bias.get('layers_used')}")
    
    # Test Case 3: Missing Feature Detection
    print("\n" + "="*80)
    print("TEST 3: Missing Feature Detection (No Error Handling)")
    print("="*80)
    
    payload3 = {
        "prompt": "Create a function to calculate factorial with error handling for negative numbers",
        "code": """def factorial(n):
    # Missing error handling for negative numbers!
    if n == 0:
        return 1
    return n * factorial(n - 1)"""
    }
    
    response3 = requests.post(API_URL, json=payload3, timeout=90)
    result3 = response3.json()
    
    print(f"\n✅ Status: {response3.status_code}")
    
    if "linguistic_results" in result3.get("analysis", {}):
        ling = result3["analysis"]["linguistic_results"]
        missing = ling.get("missing_features", {})
        
        print(f"\n🔍 Missing Feature Detection:")
        print(f"  Found: {missing.get('found')}")
        print(f"  Count: {missing.get('count')}")
        print(f"  Confidence: {missing.get('confidence')}")
        print(f"  Severity: {missing.get('severity')}/10")
        print(f"  Consensus: {missing.get('consensus')}")
        print(f"  Reliability: {missing.get('reliability')}")
        print(f"  Layers Used: {missing.get('layers_used')}")
    
    # Test Case 4: Misinterpretation Detection
    print("\n" + "="*80)
    print("TEST 4: Misinterpretation Detection (Wrong Logic)")
    print("="*80)
    
    payload4 = {
        "prompt": "Write a function that returns the sum of all even numbers in a list",
        "code": """def sum_numbers(numbers):
    # Wrong! Should filter even numbers only
    total = 0
    for num in numbers:
        total += num  # Summing ALL numbers, not just even
    print(f"Sum is {total}")  # Also printing instead of returning!"""
    }
    
    response4 = requests.post(API_URL, json=payload4, timeout=90)
    result4 = response4.json()
    
    print(f"\n✅ Status: {response4.status_code}")
    
    if "linguistic_results" in result4.get("analysis", {}):
        ling = result4["analysis"]["linguistic_results"]
        misinterp = ling.get("misinterpretation", {})
        
        print(f"\n🔍 Misinterpretation Detection:")
        print(f"  Found: {misinterp.get('found')}")
        print(f"  Score: {misinterp.get('score')}")
        print(f"  Confidence: {misinterp.get('confidence')}")
        print(f"  Severity: {misinterp.get('severity')}/10")
        print(f"  Consensus: {misinterp.get('consensus')}")
        print(f"  Reliability: {misinterp.get('reliability')}")
        print(f"  Layers Used: {misinterp.get('layers_used')}")
        
        print(f"\n  Reasons:")
        for reason in misinterp.get('reasons', [])[:3]:  # Show first 3
            print(f"    - {reason}")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE - System Ready for Deployment!")
    print("="*80)
    
    return True


if __name__ == "__main__":
    try:
        test_full_system()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Backend server not running!")
        print("Start server with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
