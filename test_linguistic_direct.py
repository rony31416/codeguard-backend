"""
Direct Linguistic Analyzer Test
================================
Tests the 3-layer cascade + aggregation system directly
Shows all aggregation fields: confidence, severity, consensus, reliability
"""
import sys
sys.path.insert(0, "F:/Codeguard/backend")

from app.analyzers.linguistic_analyzer import LinguisticAnalyzer
import json
import time

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_section(title):
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)

def test_linguistic_analyzer():
    """Test linguistic analyzer with 3-layer cascade"""
    
    print_header("🧠 LINGUISTIC ANALYZER TEST - 3-LAYER AGGREGATION")
    
    # Test case with all 4 linguistic bug types
    prompt = """
Create a simple user authentication function.
Accept username and password.
Return True if credentials are valid, False otherwise.
"""
    
    code = """
import hashlib
import logging

def authenticate(username, password):
    # Debug print - NOT requested in prompt (NPC)
    print(f"Debug: Authenticating user {username}")
    logging.info(f"Login attempt: {username}")
    
    # Hardcoded example from typical auth (Prompt-Biased)
    if username == "admin" and password == "admin123":
        return True
    
    # Missing: Password hashing (requested feature)
    # Missing: Actual validation logic
    # Missing: Error handling
    
    # Wrong: Just returns False (Misinterpretation - should validate)
    return False
"""
    
    print(f"\n📝 Prompt: {prompt.strip()}")
    print(f"\n📝 Code:\n{code}")
    
    print_section("⏱️  Running Linguistic Analysis...")
    
    start_time = time.time()
    
    try:
        analyzer = LinguisticAnalyzer(prompt, code)
        results = analyzer.analyze()
        
        analysis_time = time.time() - start_time
        
        print(f"\n✅ Analysis completed in {analysis_time:.2f}s")
        
        # ============================================================
        # 1. NPC DETECTION (Non-Prompted Consideration)
        # ============================================================
        print_section("📌 1. NPC DETECTION (Non-Prompted Consideration)")
        
        npc = results.get('npc', {})
        print(f"\n✅ Found: {npc.get('found', False)}")
        print(f"✅ Count: {npc.get('count', 0)}")
        print(f"✅ Features: {npc.get('features', [])}")
        
        # Aggregation fields
        print(f"\n🔹 Aggregation Details:")
        print(f"   Confidence: {npc.get('confidence', 0):.2f}")
        print(f"   Severity: {npc.get('severity', 'N/A')}")
        print(f"   Consensus: {npc.get('consensus', 'N/A')}")
        print(f"   Reliability: {npc.get('reliability', 'N/A')}")
        print(f"   Primary Detection: {npc.get('primary_detection', 'N/A')}")
        print(f"   Layers Used: {npc.get('layers_used', [])}")
        
        if npc.get('layers_detail'):
            print(f"\n🔹 Layer Details:")
            for layer, detail in npc['layers_detail'].items():
                print(f"   {layer}:")
                print(f"      Found: {detail.get('found', False)}")
                print(f"      Confidence: {detail.get('confidence', 0):.2f}")
                print(f"      Issues: {detail.get('issues_count', 0)}")
        
        # ============================================================
        # 2. PROMPT BIAS DETECTION
        # ============================================================
        print_section("📌 2. PROMPT BIAS DETECTION")
        
        bias = results.get('prompt_biased', {})
        print(f"\n✅ Found: {bias.get('found', False)}")
        print(f"✅ Count: {bias.get('count', 0)}")
        print(f"✅ Values: {bias.get('values', [])}")
        
        print(f"\n🔹 Aggregation Details:")
        print(f"   Confidence: {bias.get('confidence', 0):.2f}")
        print(f"   Severity: {bias.get('severity', 'N/A')}")
        print(f"   Consensus: {bias.get('consensus', 'N/A')}")
        print(f"   Reliability: {bias.get('reliability', 'N/A')}")
        print(f"   Layers Used: {bias.get('layers_used', [])}")
        
        if bias.get('layers_detail'):
            print(f"\n🔹 Layer Details:")
            for layer, detail in bias['layers_detail'].items():
                print(f"   {layer}: Found={detail.get('found')}, Conf={detail.get('confidence', 0):.2f}, Issues={detail.get('issues_count', 0)}")
        
        # ============================================================
        # 3. MISSING FEATURES DETECTION
        # ============================================================
        print_section("📌 3. MISSING FEATURES DETECTION")
        
        missing = results.get('missing_features', {})
        print(f"\n✅ Found: {missing.get('found', False)}")
        print(f"✅ Count: {missing.get('count', 0)}")
        print(f"✅ Features: {missing.get('features', [])}")
        
        print(f"\n🔹 Aggregation Details:")
        print(f"   Confidence: {missing.get('confidence', 0):.2f}")
        print(f"   Severity: {missing.get('severity', 'N/A')}")
        print(f"   Consensus: {missing.get('consensus', 'N/A')}")
        print(f"   Reliability: {missing.get('reliability', 'N/A')}")
        print(f"   Layers Used: {missing.get('layers_used', [])}")
        
        if missing.get('layers_detail'):
            print(f"\n🔹 Layer Details:")
            for layer, detail in missing['layers_detail'].items():
                print(f"   {layer}: Found={detail.get('found')}, Conf={detail.get('confidence', 0):.2f}, Issues={detail.get('issues_count', 0)}")
        
        # ============================================================
        # 4. MISINTERPRETATION DETECTION
        # ============================================================
        print_section("📌 4. MISINTERPRETATION DETECTION")
        
        misinterp = results.get('misinterpretation', {})
        print(f"\n✅ Found: {misinterp.get('found', False)}")
        print(f"✅ Score: {misinterp.get('score', 0):.2f}")
        print(f"✅ Reasons: {misinterp.get('reasons', [])}")
        
        print(f"\n🔹 Aggregation Details:")
        print(f"   Confidence: {misinterp.get('confidence', 0):.2f}")
        print(f"   Severity: {misinterp.get('severity', 'N/A')}")
        print(f"   Consensus: {misinterp.get('consensus', 'N/A')}")
        print(f"   Reliability: {misinterp.get('reliability', 'N/A')}")
        print(f"   Layers Used: {misinterp.get('layers_used', [])}")
        
        if misinterp.get('layers_detail'):
            print(f"\n🔹 Layer Details:")
            for layer, detail in misinterp['layers_detail'].items():
                print(f"   {layer}: Found={detail.get('found')}, Conf={detail.get('confidence', 0):.2f}, Issues={detail.get('issues_count', 0)}")
        
        # ============================================================
        # OVERALL SUMMARY
        # ============================================================
        print_section("📊 OVERALL SUMMARY")
        
        total_issues = (
            npc.get('count', 0) + 
            bias.get('count', 0) + 
            missing.get('count', 0) + 
            (1 if misinterp.get('found', False) else 0)
        )
        
        print(f"\n✅ Total Linguistic Issues: {total_issues}")
        print(f"   - NPC: {npc.get('count', 0)}")
        print(f"   - Prompt Bias: {bias.get('count', 0)}")
        print(f"   - Missing Features: {missing.get('count', 0)}")
        print(f"   - Misinterpretation: {'Yes' if misinterp.get('found', False) else 'No'}")
        
        print(f"\n✅ Intent Match Score: {results.get('intent_match_score', 0):.2f}")
        print(f"⏱️  Analysis Time: {analysis_time:.2f}s")
        
        # ============================================================
        # FULL JSON OUTPUT
        # ============================================================
        print_section("📄 FULL JSON OUTPUT")
        print(json.dumps(results, indent=2))
        
        # ============================================================
        # TEST RESULT
        # ============================================================
        print_header("🎯 TEST RESULT")
        
        has_aggregation = all([
            'confidence' in npc,
            'severity' in npc,
            'consensus' in npc,
            'layers_used' in npc
        ])
        
        if total_issues > 0 and has_aggregation:
            print(f"\n✅ ✅ ✅  LINGUISTIC ANALYZER TEST: PASSED  ✅ ✅ ✅")
            print(f"\n✓ Detected {total_issues} linguistic issues")
            print(f"✓ 3-layer aggregation working")
            print(f"✓ All aggregation fields present")
            print(f"✓ Analysis time: {analysis_time:.2f}s")
        else:
            print(f"\n⚠️  TEST COMPLETED WITH WARNINGS")
            if total_issues == 0:
                print(f"   No linguistic issues detected")
            if not has_aggregation:
                print(f"   Aggregation fields missing")
        
        print("\n" + "="*80 + "\n")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_linguistic_analyzer()
    
    if result:
        print("\n✅ Linguistic analyzer test completed!")
    else:
        print("\n❌ Linguistic analyzer test failed!")
