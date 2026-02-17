"""
Quick test for Linguistic Analysis - Without heavy NLP models
Tests using regex fallback (fast)
"""

import sys
sys.path.append('F:\\Codeguard\\backend')

from app.analyzers.linguistic_analyzer import LinguisticAnalyzer
import json


def test_quick_analysis():
    """Quick test without loading heavy NLP models"""
    print("\n" + "="*60)
    print("🚀 QUICK LINGUISTIC ANALYSIS TEST (Regex Mode)")
    print("="*60)
    
    # Disable heavy models for quick test
    import app.analyzers.linguistic.utils.keyword_extractor as ke
    import app.analyzers.linguistic.utils.similarity_calculator as sc
    
    # Force regex fallback (skip heavy models)
    ke.KEYBERT_AVAILABLE = False
    ke.SPACY_AVAILABLE = False
    sc.SBERT_AVAILABLE = False
    
    prompt = "Write a function to add two numbers"
    code = """
def add(a, b):
    # NPC: Logging not requested
    print(f"Adding {a} and {b}")
    
    # NPC: Validation not requested
    if not isinstance(a, (int, float)):
        raise TypeError("Must be number")
    
    return a + b
"""
    
    print(f"\nPrompt: {prompt}")
    print(f"\nCode: (with NPC violations)")
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"\n✅ RESULTS:")
    print(f"  NPC Violations: {result['npc']['count']}")
    print(f"  Features: {result['npc']['features'][:3]}")  # Show first 3
    print(f"  Intent Match: {result['intent_match_score']}")
    
    # Test all 4 detectors
    all_working = (
        'npc' in result and
        'prompt_biased' in result and
        'missing_features' in result and
        'misinterpretation' in result and
        'intent_match_score' in result
    )
    
    if all_working:
        print(f"\n✅ ALL 4 DETECTORS WORKING!")
        print(f"  - NPC: {'✅ Found' if result['npc']['found'] else '❌ Not found'}")
        print(f"  - Prompt Biased: {'✅ Found' if result['prompt_biased']['found'] else '✅ None'}")
        print(f"  - Missing Features: {'✅ Found' if result['missing_features']['found'] else '✅ None'}")
        print(f"  - Misinterpretation: {'✅ Found' if result['misinterpretation']['found'] else '✅ None'}")
        return True
    else:
        print(f"\n❌ SOME DETECTORS FAILED")
        return False


def test_prompt_bias():
    """Test prompt bias detection"""
    print("\n" + "="*60)
    print("🔍 Test Prompt Bias Detection")
    print("="*60)
    
    # Disable heavy models
    import app.analyzers.linguistic.utils.keyword_extractor as ke
    ke.KEYBERT_AVAILABLE = False
    ke.SPACY_AVAILABLE = False
    
    prompt = "Check if name is 'Alice'"
    code = """
def check_name(name):
    if name == "Alice":  # HARDCODED!
        return True
    return False
"""
    
    analyzer = LinguisticAnalyzer(prompt, code)
    result = analyzer.analyze()
    
    print(f"  Prompt Biased: {result['prompt_biased']['found']}")
    print(f"  Values: {result['prompt_biased']['values']}")
    
    if result['prompt_biased']['found']:
        print(f"  ✅ Correctly detected hardcoded 'Alice'")
        return True
    else:
        print(f"  ❌ Failed to detect")
        return False


def main():
    """Run quick tests"""
    print("\n" + "="*60)
    print("🧪 QUICK TEST SUITE (No Heavy Models)")
    print("="*60)
    print("⚡ Using regex fallback for speed")
    print("="*60)
    
    try:
        test1 = test_quick_analysis()
        test2 = test_prompt_bias()
        
        print("\n" + "="*60)
        if test1 and test2:
            print("✅ ALL QUICK TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\n💡 To test with full NLP: python test\\test_linguistic_analysis.py")
        print("   (Takes 30-60s to load models, but more accurate)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
