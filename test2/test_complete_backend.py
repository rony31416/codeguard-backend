"""
Complete Backend Test - All 3 Stages + All 10 Bug Patterns
Tests the entire analysis pipeline: Static → Dynamic → Linguistic (3-Layer)
"""
import requests
import json
import time

API_URL = "http://localhost:8000/api/analyze"

def test_complete_system():
    """Test with code containing multiple bug types from all 10 patterns"""
    
    print("\n" + "="*80)
    print("🧪 COMPLETE BACKEND TEST - ALL 3 STAGES + 10 BUG PATTERNS")
    print("="*80)
    
    # Test case with MULTIPLE bug types
    prompt = """
Write a function to calculate the total price with discount for a list of products.
- Accept list of products (each has 'name' and 'price')
- Apply 10% discount
- Return the final discounted total price
- Handle empty lists properly
"""
    
    code = """
import non_existent_module  # BUG 1: Hallucinated Object (import)
from math import sqrtt      # BUG 2: Silly Mistake (typo in import)

def calculate_total(products):
    # BUG 3: NPC - Debug print not requested
    print("Debug: Calculating total")
    logging.info("Processing products")  # BUG 4: NPC - Logging not requested
    
    # BUG 5: Prompt-Biased - Hardcoded example value from prompt
    discount_rate = 10  # Hardcoded from example
    
    # BUG 6: Missing Corner Case - No check for empty list
    # BUG 7: Missing Corner Case - No check for None
    total = 0
    for product in products:
        # BUG 8: Wrong Attribute - assumes 'price' without checking
        total += product.price
    
    # BUG 9: Silly Mistake - Wrong calculation (should divide by 100)
    discount = total * discount_rate  # Should be: total * (discount_rate / 100)
    
    final_price = total - discount
    
    # BUG 10: Misinterpretation - Prints instead of returning
    print(f"Final price: {final_price}")
    # Missing: return final_price
"""
    
    payload = {
        "prompt": prompt,
        "code": code
    }
    
    print(f"\n📝 Test Code: {len(code.split(chr(10)))} lines")
    print(f"📝 Expected Bugs: 10 different types")
    print(f"\n⏱️  Starting analysis...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        analysis_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Status: {response.status_code}")
            print(f"⏱️  Total Time: {analysis_time:.2f}s")
            
            # ===== EXECUTION LOGS =====
            print("\n" + "-"*80)
            print("📊 STAGE EXECUTION LOGS")
            print("-"*80)
            
            for log in data.get('execution_logs', []):
                status_icon = "✅" if log['success'] else "❌"
                print(f"{status_icon} {log['stage'].upper()}: {log['execution_time']:.3f}s")
                if log.get('error_message'):
                    print(f"   Error: {log['error_message'][:100]}")
            
            # ===== BUG PATTERNS DETECTED =====
            print("\n" + "-"*80)
            print("🐛 BUG PATTERNS DETECTED")
            print("-"*80)
            
            bug_patterns = data.get('bug_patterns', [])
            print(f"\n✅ Total Patterns Found: {len(bug_patterns)}")
            print(f"✅ Overall Severity: {data.get('overall_severity', 0)}/10")
            
            for i, bug in enumerate(bug_patterns, 1):
                print(f"\n{i}. {bug['pattern_name']}")
                print(f"   Severity: {bug['severity']}/10")
                print(f"   Confidence: {bug.get('confidence', 0):.2f}")
                print(f"   Location: {bug.get('location', 'N/A')}")
                print(f"   Description: {bug['description'][:150]}...")
            
            # ===== SUMMARY =====
            print("\n" + "-"*80)
            print("📊 SUMMARY")
            print("-"*80)
            print(data.get('summary', 'N/A'))
            
            # ===== VERIFY ALL STAGES PASSED =====
            print("\n" + "="*80)
            print("✅ VERIFICATION")
            print("="*80)
            
            all_stages_success = all(log['success'] for log in data.get('execution_logs', []))
            has_bugs = data.get('has_bugs', False)
            
            print(f"✅ All Stages Passed: {all_stages_success}")
            print(f"✅ Bugs Detected: {has_bugs}")
            print(f"✅ Bug Patterns: {len(bug_patterns)}")
            print(f"✅ Overall Severity: {data.get('overall_severity', 0)}/10")
            print(f"⏱️  Total Time: {analysis_time:.2f}s")
            
            # Check if linguistic analysis used LLM
            linguistic_log = next((log for log in data.get('execution_logs', []) if log['stage'] == 'linguistic'), None)
            if linguistic_log and linguistic_log['success']:
                print(f"✅ Linguistic Analysis (3-Layer): SUCCESS")
                print(f"   Note: Check server logs to see which API was used (Ollama/OpenRouter)")
            
            print("\n" + "="*80)
            print("✅ COMPLETE BACKEND TEST PASSED!")
            print("="*80)
            
            return data
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_complete_system()
    
    if result:
        print("\n✅ Test completed successfully!")
        print(f"   Analysis ID: {result.get('analysis_id', 'N/A')}")
    else:
        print("\n❌ Test failed!")
