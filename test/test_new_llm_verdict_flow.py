"""
Test the new 3-stage flow: Layer 1 & 2 evidence → LLM verdict
This replaces the old aggregation approach.
"""
import ast
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.linguistic.npc_detector import NPCDetector
from app.analyzers.linguistic.prompt_bias_detector import PromptBiasDetector
from app.analyzers.linguistic.missing_feature_detector import MissingFeatureDetector
from app.analyzers.linguistic.misinterpretation_detector import MisinterpretationDetector


def test_npc_detector():
    """Test NPC detector with new LLM verdict flow"""
    print("\n" + "="*70)
    print("TEST 1: NPC Detector (Non-Prompted Considerations)")
    print("="*70)
    
    prompt = "Create a function to add two numbers"
    code = """
def add_numbers(a, b):
    # NPC: Debug print not requested
    print(f"Debug: Adding {a} + {b}")
    
    # NPC: Logging not requested
    import logging
    logging.info("Addition operation")
    
    # NPC: Validation not requested
    if not isinstance(a, (int, float)):
        raise ValueError("Must be number")
    
    return a + b
"""
    
    detector = NPCDetector(prompt, code, ast.parse(code))
    result = detector.detect()
    
    print(f"\n✅ Found: {result['found']}")
    print(f"📊 Features: {result.get('features', [])}")
    print(f"🔢 Count: {result.get('count', 0)}")
    print(f"💯 Confidence: {result.get('confidence', 0)}")
    print(f"⚠️  Severity: {result.get('severity', 0)}/10")
    print(f"🔍 Layers Used: {result.get('layers_used', [])}")
    print(f"🎯 Verdict By: {result.get('verdict_by', 'N/A')}")
    if result.get('summary'):
        print(f"📝 Summary: {result['summary']}")


def test_prompt_bias_detector():
    """Test Prompt Bias detector with new LLM verdict flow"""
    print("\n" + "="*70)
    print("TEST 2: Prompt Bias Detector (Hardcoded Example Values)")
    print("="*70)
    
    prompt = "Sort this list: [3, 1, 2]"
    code = """
def sort_list():
    # Prompt bias: hardcoded example values
    numbers = [3, 1, 2]
    return sorted(numbers)
"""
    
    detector = PromptBiasDetector(prompt, code, ast.parse(code))
    result = detector.detect()
    
    print(f"\n✅ Found: {result['found']}")
    print(f"📊 Values: {result.get('values', [])}")
    print(f"🔢 Count: {result.get('count', 0)}")
    print(f"💯 Confidence: {result.get('confidence', 0)}")
    print(f"⚠️  Severity: {result.get('severity', 0)}/10")
    print(f"🔍 Layers Used: {result.get('layers_used', [])}")
    print(f"🎯 Verdict By: {result.get('verdict_by', 'N/A')}")
    if result.get('summary'):
        print(f"📝 Summary: {result['summary']}")


def test_missing_feature_detector():
    """Test Missing Feature detector with new LLM verdict flow"""
    print("\n" + "="*70)
    print("TEST 3: Missing Feature Detector (Requested but Not Implemented)")
    print("="*70)
    
    prompt = "Create a function to validate email and phone number"
    code = """
def validate_email(email):
    # Only email validation - phone is missing!
    return '@' in email
"""
    
    detector = MissingFeatureDetector(prompt, code, ast.parse(code))
    result = detector.detect()
    
    print(f"\n✅ Found: {result['found']}")
    print(f"📊 Features: {result.get('features', [])}")
    print(f"🔢 Count: {result.get('count', 0)}")
    print(f"💯 Confidence: {result.get('confidence', 0)}")
    print(f"⚠️  Severity: {result.get('severity', 0)}/10")
    print(f"🔍 Layers Used: {result.get('layers_used', [])}")
    print(f"🎯 Verdict By: {result.get('verdict_by', 'N/A')}")
    if result.get('summary'):
        print(f"📝 Summary: {result['summary']}")


def test_misinterpretation_detector():
    """Test Misinterpretation detector with new LLM verdict flow"""
    print("\n" + "="*70)
    print("TEST 4: Misinterpretation Detector (Fundamental Misunderstanding)")
    print("="*70)
    
    prompt = "Calculate the average of a list of numbers"
    code = """
def calculate(numbers):
    # Misinterpretation: returns sum instead of average!
    return sum(numbers)
"""
    
    detector = MisinterpretationDetector(prompt, code, ast.parse(code))
    result = detector.detect()
    
    print(f"\n✅ Found: {result['found']}")
    print(f"📊 Reasons: {result.get('reasons', [])}")
    print(f"🔢 Score: {result.get('score', 0)}/10")
    print(f"💯 Confidence: {result.get('confidence', 0)}")
    print(f"⚠️  Severity: {result.get('severity', 0)}/10")
    print(f"🔍 Layers Used: {result.get('layers_used', [])}")
    print(f"🎯 Verdict By: {result.get('verdict_by', 'N/A')}")
    if result.get('summary'):
        print(f"📝 Summary: {result['summary']}")


def test_simple_case():
    """Test with the user's example from screenshot"""
    print("\n" + "="*70)
    print("TEST 5: User's Example (Add Numbers with Missing Corner Case)")
    print("="*70)
    
    prompt = "give me a python addition code for adding two numbers"
    code = """
def add_numbers(a, b):
    # NPC: Debug print
    print(f"Debug: Adding {a} + {b}")
    
    # NPC: Logging
    import logging
    logging.info("Addition")
    
    # NPC: Validation
    if not isinstance(a, (int, float)):
        raise ValueError("Must be number")
    
    return a + b
"""
    
    # Test all detectors
    detectors = [
        ("NPC", NPCDetector(prompt, code, ast.parse(code))),
        ("Prompt Bias", PromptBiasDetector(prompt, code, ast.parse(code))),
        ("Missing Feature", MissingFeatureDetector(prompt, code, ast.parse(code))),
        ("Misinterpretation", MisinterpretationDetector(prompt, code, ast.parse(code)))
    ]
    
    print("\n🔍 Running all 4 detectors on user's code...")
    
    for name, detector in detectors:
        result = detector.detect()
        if result['found']:
            print(f"\n✅ {name}: FOUND")
            print(f"   - Count: {result.get('count', result.get('score', 0))}")
            print(f"   - Confidence: {result.get('confidence', 0)}")
            print(f"   - Severity: {result.get('severity', 0)}/10")
            print(f"   - Verdict By: {result.get('verdict_by', 'N/A')}")
        else:
            print(f"\n❌ {name}: NOT FOUND")


if __name__ == "__main__":
    print("\n" + "🚀 "* 30)
    print("NEW 3-STAGE FLOW TEST")
    print("Stage 1: Rule Engine Evidence")
    print("Stage 2: AST Analyzer Evidence")  
    print("Stage 3: LLM Final Verdict")
    print("🚀 "* 30)
    
    test_npc_detector()
    test_prompt_bias_detector()
    test_missing_feature_detector()
    test_misinterpretation_detector()
    test_simple_case()
    
    print("\n" + "="*70)
    print("✅ All Tests Completed!")
    print("="*70)
