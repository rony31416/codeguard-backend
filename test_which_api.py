"""
Test which LLM API is being used (Ollama vs OpenRouter)
"""
import sys
sys.path.insert(0, "F:/Codeguard/backend")

from app.analyzers.linguistic.LLM_response import get_llm

print("\n" + "="*80)
print("🔍 Testing LLM API Priority (Ollama → OpenRouter → Skip)")
print("="*80)

llm = get_llm()

# Test API status
print(f"\n✅ Ollama Enabled: {llm.ollama_enabled}")
print(f"✅ OpenRouter Enabled: {llm.openrouter_enabled}")
print(f"✅ Overall LLM Enabled: {llm.enabled}")

# Test simple question
print("\n" + "-"*80)
print("Testing with simple question...")
print("-"*80)

response = llm.ask("What is 2+2? Reply with just the number.")

if response:
    print(f"\n✅ Response received: {response[:100]}")
    
    # Check which API was used by testing individual APIs
    print("\n" + "-"*80)
    print("🔍 Determining which API was used...")
    print("-"*80)
    
    if llm.ollama_enabled:
        ollama_test = llm._ask_ollama("Reply with 'OLLAMA'", max_retries=1)
        if ollama_test:
            print(f"✅ Ollama is WORKING (likely used for analysis)")
        else:
            print(f"⚠️ Ollama test failed")
    
    if llm.openrouter_enabled:
        openrouter_test = llm._ask_openrouter("Reply with 'OPENROUTER'", max_retries=1)
        if openrouter_test:
            print(f"✅ OpenRouter is WORKING")
        else:
            print(f"⚠️ OpenRouter test failed (rate limited)")
else:
    print("\n❌ No response from any API")

print("\n" + "="*80)
