"""
COMPREHENSIVE BACKEND TEST
==========================
Tests ALL 3 Stages + ALL 10 Bug Patterns + 3-Layer Linguistic Aggregation

Stage 1: Static Analysis
Stage 2: Dynamic Analysis  
Stage 3: Linguistic Analysis (3-Layer: Rule Engine → AST → LLM + Aggregation)
Classification: Maps to 10 bug patterns
"""
import requests
import json
import time

API_URL = "http://localhost:8000/api/analyze"

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_section(title):
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)

def test_full_backend():
    """
    Test code designed to trigger ALL 10 bug patterns:
    
    STATIC ANALYSIS (Patterns 1-4):
    1. Syntax Error - malformed code
    2. Hallucinated Object - non-existent imports/functions
    3. Incomplete Generation - missing logic
    4. Silly Mistake - typos, wrong operators
    
    DYNAMIC ANALYSIS (Patterns 5-6):
    5. Wrong Attribute - incorrect attribute access
    6. Wrong Input Type - type mismatches
    
    LINGUISTIC ANALYSIS (Patterns 7-10) - 3-Layer Cascade:
    7. NPC (Non-Prompted Consideration) - unrequested features
    8. Prompt-Biased Code - hardcoded example values
    9. Missing Features - requested but not implemented
    10. Misinterpretation - wrong understanding
    """
    
    print_header("🧪 COMPREHENSIVE BACKEND TEST - ALL 10 BUG PATTERNS")
    
    # Complex test case covering all bug types
    prompt = """
Create a user authentication system with the following features:
1. Register new user with username and password
2. Login with credentials
3. Return success/failure status
4. Hash passwords for security
5. Handle invalid inputs gracefully
"""
    
    code = """
import hashlib
import non_existent_auth_lib  # BUG 1: Hallucinated Object (fake import)
from math import sqrtt        # BUG 2: Silly Mistake (typo)

def authenticate_user(username, password):
    # BUG 3: NPC - Debug prints not requested
    print(f"Debug: Authenticating {username}")
    logging.info(f"Login attempt for {username}")  # BUG 4: NPC - Logging not requested
    
    # BUG 5: Prompt-Biased - Hardcoded example from typical auth examples
    if username == "admin" and password == "admin123":
        print("Admin login detected")  # Hardcoded example values
    
    # BUG 6: Missing Feature - NO password hashing (requested in prompt)
    # BUG 7: Missing Feature - NO user registration function (requested)
    # BUG 8: Missing Feature - NO error handling (requested)
    
    # BUG 9: Wrong Attribute - Assumes user object has .password attribute
    user = get_user(username)
    if user.password == password:  # Should use dict syntax or method
        return True
    
    # BUG 10: Misinterpretation - Returns boolean instead of status dict
    # Prompt asked for "success/failure status" (should return dict/object)
    return False
    
# BUG 11: Incomplete Generation - Function declared but not defined
def hash_password(password):
    pass  # Incomplete implementation

# BUG 12: Syntax Error - Invalid syntax
def get_user(username)
    users = {"admin": {"password": "admin123"}
    return users.get(username)
"""
    
    payload = {
        "prompt": prompt,
        "code": code
    }
    
    print(f"\n📝 Prompt: {len(prompt)} chars")
    print(f"📝 Code: {len(code.split(chr(10)))} lines")
    print(f"📝 Expected: 10+ bug patterns across all 3 stages")
    
    print_section("⏱️  Starting Analysis...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=180)
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ HTTP Status: {response.status_code} OK")
            print(f"⏱️  Total Analysis Time: {total_time:.2f}s")
            
            # ============================================================
            # STAGE EXECUTION LOGS
            # ============================================================
            print_section("📊 STAGE 1-4: EXECUTION LOGS")
            
            logs = data.get('execution_logs', [])
            stage_times = {}
            
            for log in logs:
                stage = log['stage']
                success = log['success']
                exec_time = log.get('execution_time', 0)
                stage_times[stage] = exec_time
                
                status_icon = "✅" if success else "❌"
                print(f"\n{status_icon} STAGE: {stage.upper()}")
                print(f"   Time: {exec_time:.3f}s")
                print(f"   Success: {success}")
                
                if log.get('error_message'):
                    print(f"   Error: {log['error_message'][:150]}...")
                if log.get('error_type'):
                    print(f"   Type: {log['error_type']}")
            
            # ============================================================
            # BUG PATTERNS DETECTED (ALL 10 PATTERNS)
            # ============================================================
            print_section("🐛 BUG PATTERNS DETECTED (10 Categories)")
            
            bug_patterns = data.get('bug_patterns', [])
            overall_severity = data.get('overall_severity', 0)
            has_bugs = data.get('has_bugs', False)
            
            print(f"\n✅ Total Patterns Found: {len(bug_patterns)}")
            print(f"✅ Overall Severity: {overall_severity}/10")
            print(f"✅ Has Bugs: {has_bugs}")
            
            # Group by pattern name
            pattern_counts = {}
            for bug in bug_patterns:
                name = bug['pattern_name']
                pattern_counts[name] = pattern_counts.get(name, 0) + 1
            
            print(f"\n📊 Pattern Distribution:")
            for i, bug in enumerate(bug_patterns, 1):
                print(f"\n  {i}. {bug['pattern_name']}")
                print(f"     Severity: {bug['severity']}/10")
                print(f"     Confidence: {bug.get('confidence', 0):.2f}")
                print(f"     Location: {bug.get('location', 'N/A')[:60]}...")
                print(f"     Description: {bug['description'][:120]}...")
            
            # ============================================================
            # LINGUISTIC ANALYSIS DETAILS (3-Layer Aggregation)
            # ============================================================
            print_section("🧠 LINGUISTIC ANALYSIS - 3-LAYER AGGREGATION")
            
            # Check if linguistic stage has detailed results
            linguistic_successful = any(
                log['stage'] == 'linguistic' and log['success'] 
                for log in logs
            )
            
            if linguistic_successful:
                print(f"\n✅ Linguistic Analysis: SUCCESSFUL")
                print(f"⏱️  Time: {stage_times.get('linguistic', 0):.3f}s")
                print(f"\n📌 3-Layer Cascade Architecture:")
                print(f"   Layer 1: Rule Engine (Pattern Matching) ~10ms")
                print(f"   Layer 2: AST Analyzer (Structural) ~50ms")
                print(f"   Layer 3: LLM Reasoner (Semantic) ~300ms")
                print(f"   Aggregation: Weighted Voting + Consensus")
                
                # Show linguistic bug patterns detected
                linguistic_patterns = [
                    bp for bp in bug_patterns 
                    if bp['pattern_name'] in [
                        'Non-Prompted Consideration',
                        'Prompt-Biased Code', 
                        'Missing Core Feature',
                        'Misinterpretation'
                    ]
                ]
                
                print(f"\n📊 Linguistic Patterns Detected: {len(linguistic_patterns)}")
                for lp in linguistic_patterns:
                    print(f"   • {lp['pattern_name']} (Severity: {lp['severity']}/10)")
                
                # Note about aggregation
                print(f"\n💡 Aggregation Features:")
                print(f"   • Confidence: MAX(layer1, layer2, layer3)")
                print(f"   • Severity: WEIGHTED(layer1×0.3 + layer2×0.3 + layer3×0.4)")
                print(f"   • Consensus: all_agree | majority_agree | single_layer")
                print(f"   • Reliability: very_high | high | medium | low")
                print(f"\n   Note: Detailed aggregation fields stored in database")
                print(f"         Check linguistic_analysis table for full details")
            else:
                print(f"\n⚠️ Linguistic Analysis: FAILED or SKIPPED")
            
            # ============================================================
            # VERIFICATION CHECKLIST
            # ============================================================
            print_section("✅ VERIFICATION CHECKLIST")
            
            # Check each stage
            stages = ['static', 'dynamic', 'linguistic', 'classification']
            stage_status = {
                stage: any(log['stage'] == stage and log['success'] for log in logs)
                for stage in stages
            }
            
            print(f"\n📋 Stage Completion:")
            for stage, success in stage_status.items():
                icon = "✅" if success else "❌"
                print(f"   {icon} {stage.upper()}: {'PASSED' if success else 'FAILED'}")
            
            # Check bug pattern coverage
            all_patterns = [
                "Syntax Error",
                "Hallucinated Object", 
                "Incomplete Generation",
                "Silly Mistake",
                "Wrong Attribute",
                "Wrong Input Type",
                "Non-Prompted Consideration",
                "Prompt-Biased Code",
                "Missing Core Feature",
                "Misinterpretation"
            ]
            
            detected_patterns = set(bp['pattern_name'] for bp in bug_patterns)
            
            print(f"\n📋 Bug Pattern Coverage ({len(detected_patterns)}/10):")
            for pattern in all_patterns:
                detected = pattern in detected_patterns
                icon = "✅" if detected else "⬜"
                print(f"   {icon} {pattern}")
            
            # Performance metrics
            print(f"\n📋 Performance Metrics:")
            print(f"   Total Time: {total_time:.2f}s")
            print(f"   Static: {stage_times.get('static', 0):.3f}s")
            print(f"   Dynamic: {stage_times.get('dynamic', 0):.3f}s")
            print(f"   Linguistic: {stage_times.get('linguistic', 0):.3f}s")
            print(f"   Classification: {stage_times.get('classification', 0):.3f}s")
            
            # ============================================================
            # SUMMARY
            # ============================================================
            print_section("📊 FINAL SUMMARY")
            
            print(f"\n{data.get('summary', 'N/A')}")
            
            # ============================================================
            # TEST RESULT
            # ============================================================
            print_header("🎯 TEST RESULT")
            
            all_stages_passed = all(stage_status.values())
            bugs_detected = has_bugs and len(bug_patterns) > 0
            linguistic_passed = stage_status.get('linguistic', False)
            
            if all_stages_passed and bugs_detected and linguistic_passed:
                print(f"\n✅ ✅ ✅  COMPLETE BACKEND TEST: PASSED  ✅ ✅ ✅")
                print(f"\n✓ All 3 stages executed successfully")
                print(f"✓ {len(bug_patterns)} bug patterns detected")
                print(f"✓ Linguistic analysis with 3-layer cascade: SUCCESS")
                print(f"✓ Overall severity: {overall_severity}/10")
                print(f"✓ Analysis ID: {data.get('analysis_id', 'N/A')}")
                print(f"✓ Total time: {total_time:.2f}s")
            else:
                print(f"\n⚠️  TEST COMPLETED WITH WARNINGS")
                if not all_stages_passed:
                    print(f"   Some stages failed")
                if not bugs_detected:
                    print(f"   No bugs detected (unexpected)")
                if not linguistic_passed:
                    print(f"   Linguistic analysis failed")
            
            print("\n" + "="*80 + "\n")
            
            return data
            
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(response.text[:500])
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout (>180s)")
        print("   This might indicate the LLM API is slow or unresponsive")
        return None
        
    except Exception as e:
        print(f"\n❌ Exception: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_full_backend()
    
    if result:
        print("\n✅ Test execution completed successfully!")
    else:
        print("\n❌ Test execution failed!")
