import sys
sys.path.insert(0, "F:/Codeguard/backend")

from app.analyzers.linguistic.LLM_response import get_llm

print("Testing LLM connection...")
llm = get_llm()

print(f"LLM Enabled: {llm.enabled}")
print(f"API Key exists: {bool(llm.api_key)}")

if llm.enabled:
    print("\nTesting is_alive()...")
    result = llm.is_alive()
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"Response: {result.get('response', 'N/A')}")
else:
    print("LLM not enabled - check API key")
