"""
Test Dual API Fallback: Ollama (Primary) → OpenRouter (Fallback)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.linguistic.LLM_response import get_llm


def test_dual_api_fallback():
    print("\n" + "="*70)
    print("DUAL API FALLBACK TEST")
    print("="*70)
    
    llm = get_llm()
    
    print(f"\n🔍 LLM Configuration:")
    print(f"   - Overall Enabled: {llm.enabled}")
    print(f"   - Ollama Enabled: {llm.ollama_enabled}")
    print(f"   - OpenRouter Enabled: {llm.openrouter_enabled}")
    
    if llm.ollama_enabled:
        print(f"   - Ollama Model: {llm.ollama_model}")
    if llm.openrouter_enabled:
        print(f"   - OpenRouter Model: {llm.openrouter_model}")
    
    print("\n" + "-"*70)
    print("Testing API Fallback Chain: Ollama → OpenRouter → None")
    print("-"*70)
    
    if not llm.enabled:
        print("\n❌ No LLM APIs available!")
        print("   Set OLLAMA_API_KEY or OPENROUTER_API_KEY in .env")
        return
    
    # Simple test question
    test_question = """Is this code buggy?
    
Code:
def add(a, b):
    return a + b

Answer with YES or NO and brief reason."""
    
    print("\n📤 Sending test question to LLM...")
    print(f"   Question: {test_question[:50]}...")
    
    response = llm.ask(test_question)
    
    if response:
        print(f"\n✅ LLM Response Received!")
        print(f"   Length: {len(response)} characters")
        print(f"\n📝 Response Preview:")
        print("   " + response[:200].replace("\n", "\n   "))
        if len(response) > 200:
            print("   ...")
    else:
        print("\n❌ No response from LLM (all APIs failed)")
    
    print("\n" + "="*70)


def test_api_priority():
    """Test which API is tried first"""
    print("\n" + "="*70)
    print("API PRIORITY TEST")
    print("="*70)
    
    llm = get_llm()
    
    print("\n🎯 API Call Order:")
    if llm.ollama_enabled:
        print("   1️⃣  PRIMARY: Ollama (local/cloud, fast, free)")
        if llm.openrouter_enabled:
            print("   2️⃣  FALLBACK: OpenRouter (only if Ollama fails)")
    elif llm.openrouter_enabled:
        print("   1️⃣  ONLY: OpenRouter")
    else:
        print("   ❌ NO APIs available")
    
    print("\n💡 Benefits of Dual API:")
    print("   ✅ Faster: Ollama is tried first (local/cloud)")
    print("   ✅ Reliable: Falls back to OpenRouter if Ollama fails")
    print("   ✅ No single point of failure")
    print("   ✅ Rate limits: If one API is rate limited, uses the other")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n🚀 DUAL LLM API SYSTEM TEST\n")
    
    test_dual_api_fallback()
    test_api_priority()
    
    print("\n✅ Test Complete!\n")
