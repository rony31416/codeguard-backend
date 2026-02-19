"""
Dual LLM API Integration - Ollama (Primary) + OpenRouter (Fallback)
Fallback Chain: Ollama → OpenRouter → Skip LLM

Primary: Ollama Cloud (gpt-oss:20b-cloud) - Fast & Reliable
Fallback: OpenRouter (google/gemma-3-12b-it:free) - Free tier
"""

import os
import requests
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Try to import Ollama client (graceful fail if not installed)
OLLAMA_AVAILABLE = False
try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    print("⚠️ Ollama client not installed. Install with: pip install ollama")
    Client = None


class LLM:
    """Dual LLM wrapper with Ollama (primary) and OpenRouter (fallback)."""
    
    def __init__(self):
        # Ollama configuration
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY", "")
        self.ollama_enabled = OLLAMA_AVAILABLE and bool(self.ollama_api_key and self.ollama_api_key != "*****")
        self.ollama_model = "gpt-oss:20b-cloud"
        self.ollama_client = None
        
        # OpenRouter configuration (fallback)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_enabled = bool(self.openrouter_api_key and self.openrouter_api_key != "*****")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_model = "google/gemma-3-12b-it:free"
        
        # Initialize Ollama client if available
        if self.ollama_enabled:
            try:
                self.ollama_client = Client(
                    host='https://ollama.com',
                    headers={'Authorization': f'Bearer {self.ollama_api_key}'}
                )
            except Exception as e:
                print(f"⚠️ Failed to initialize Ollama client: {e}")
                self.ollama_enabled = False
        
        # Overall LLM status
        self.enabled = self.ollama_enabled or self.openrouter_enabled
        
        # Debug logging
        if not self.enabled:
            print(f"❌ LLM Disabled: OLLAMA_AVAILABLE={OLLAMA_AVAILABLE}, Ollama Key={'[SET]' if self.ollama_api_key else '[MISSING]'}, OpenRouter Key={'[SET]' if self.openrouter_api_key else '[MISSING]'}")
        else:
            print(f"✓ LLM Enabled: Ollama={self.ollama_enabled}, OpenRouter={self.openrouter_enabled}")
    
    def ask(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """
        Ask LLM with fallback chain: Ollama → OpenRouter → None
        
        Args:
            prompt: Question to ask the LLM
            max_retries: Number of retries per API (default: 2)
        
        Returns:
            LLM response string or None if all APIs fail
        """
        if not self.enabled:
            return None
        
        # Try Ollama first (primary)
        if self.ollama_enabled:
            response = self._ask_ollama(prompt, max_retries)
            if response:
                return response
            print("⚠️ Ollama failed, falling back to OpenRouter...")
        
        # Fallback to OpenRouter
        if self.openrouter_enabled:
            response = self._ask_openrouter(prompt, max_retries)
            if response:
                return response
            print("⚠️ OpenRouter failed, skipping LLM analysis...")
        
        # Both APIs failed
        return None
    
    def _ask_ollama(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Ask Ollama Cloud API with streaming."""
        if not self.ollama_enabled or not self.ollama_client:
            return None
        
        messages = [{"role": "user", "content": prompt}]
        
        for attempt in range(max_retries):
            try:
                stream = self.ollama_client.chat(
                    model=self.ollama_model,
                    messages=messages,
                    stream=True
                )
                
                full_response = ""
                for part in stream:
                    content = part.message.content
                    full_response += content
                
                if full_response:
                    return full_response
                
            except Exception as e:
                print(f"⚠️ Ollama attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief pause before retry
        
        return None
    
    def _ask_openrouter(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Ask OpenRouter API (fallback)."""
        if not self.openrouter_enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.openrouter_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    self.openrouter_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                
                elif r.status_code == 429:
                    wait = 2 ** attempt
                    print(f"⚠️ OpenRouter rate limited. Retry in {wait}s...")
                    time.sleep(wait)
                
                else:
                    print(f"⚠️ OpenRouter error {r.status_code}: {r.text[:100]}")
                    
            except Exception as e:
                print(f"⚠️ OpenRouter attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def is_alive(self) -> Dict[str, Any]:
        """Test if LLM APIs are working (both Ollama and OpenRouter)."""
        if not self.enabled:
            return {"status": "disabled", "message": "No API keys configured"}
        
        results = {
            "ollama": {"enabled": self.ollama_enabled, "working": False},
            "openrouter": {"enabled": self.openrouter_enabled, "working": False}
        }
        
        # Test Ollama
        if self.ollama_enabled:
            try:
                response = self._ask_ollama("Reply with OK", max_retries=1)
                if response:
                    results["ollama"]["working"] = True
                    results["ollama"]["response"] = response[:50]
            except Exception as e:
                results["ollama"]["error"] = str(e)
        
        # Test OpenRouter
        if self.openrouter_enabled:
            try:
                response = self._ask_openrouter("Reply with OK", max_retries=1)
                if response:
                    results["openrouter"]["working"] = True
                    results["openrouter"]["response"] = response[:50]
            except Exception as e:
                results["openrouter"]["error"] = str(e)
        
        # Determine overall status
        if results["ollama"]["working"] or results["openrouter"]["working"]:
            status = "alive"
            message = f"Working: {'Ollama' if results['ollama']['working'] else ''} {'OpenRouter' if results['openrouter']['working'] else ''}".strip()
        else:
            status = "error"
            message = "All LLM APIs failed"
        
        return {
            "status": status,
            "message": message,
            "apis": results
        }
    
    def analyze_code(self, prompt: str, code: str) -> Dict[str, Any]:
        """Analyze code for bugs using fallback chain."""
        if not self.enabled:
            return {"success": False, "error": "No API enabled", "api_used": None}
        
        question = f"""Analyze this code for bugs.

USER PROMPT:
{prompt}

GENERATED CODE:
{code}

Find these bug types:
1. NPC (Non-Prompted Considerations): Debug prints, hardcoded values, missing error handling
2. Prompt Bias: Hardcoded examples from the prompt
3. Missing Features: Features user expected but not implemented
4. Misinterpretation: Code doesn't match user intent

Return ONLY valid JSON in this format:
{{
    "npc_issues": ["list of NPC bugs found"],
    "prompt_bias_issues": ["list of prompt-biased bugs"],
    "missing_features": ["list of missing features"],
    "misinterpretation": ["list of misinterpretations"],
    "severity": 0-10,
    "summary": "brief summary"
}}"""
        
        try:
            # Try Ollama first
            api_used = None
            response = None
            
            if self.ollama_enabled:
                response = self._ask_ollama(question, max_retries=1)
                if response:
                    api_used = "ollama"
            
            # Fallback to OpenRouter
            if not response and self.openrouter_enabled:
                response = self._ask_openrouter(question, max_retries=1)
                if response:
                    api_used = "openrouter"
            
            if response:
                return {
                    "success": True,
                    "analysis": response,
                    "api_used": api_used,
                    "model": self.ollama_model if api_used == "ollama" else self.openrouter_model
                }
            else:
                return {
                    "success": False,
                    "error": "All LLM APIs failed",
                    "api_used": None
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "api_used": None
            }


# Singleton
_llm = None

def get_llm():
    """Get LLM singleton instance."""
    global _llm
    if _llm is None:
        _llm = LLM()
    return _llm


if __name__ == "__main__":
    """Quick test for dual LLM system"""
    llm = get_llm()
    
    print("=" * 80)
    print("🧪 Testing Dual LLM System (Ollama + OpenRouter)")
    print("=" * 80)
    print(f"\n✅ Ollama Enabled: {llm.ollama_enabled}")
    print(f"✅ OpenRouter Enabled: {llm.openrouter_enabled}")
    print(f"✅ Overall Status: {'ENABLED' if llm.enabled else 'DISABLED'}")
    
    if not llm.enabled:
        print("\n⚠️ No LLM APIs configured. Add API keys to .env file.")
        exit(1)
    
    print("\n" + "-" * 80)
    print("Testing API Connectivity...")
    print("-" * 80)
    
    result = llm.is_alive()
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"\nAPI Details:")
    for api_name, api_info in result.get('apis', {}).items():
        print(f"  {api_name.upper()}:")
        print(f"    Enabled: {api_info['enabled']}")
        print(f"    Working: {api_info['working']}")
        if 'response' in api_info:
            print(f"    Response: {api_info['response']}")
        if 'error' in api_info:
            print(f"    Error: {api_info['error']}")
    
    if result['status'] == 'alive':
        print("\n" + "-" * 80)
        print("Testing Code Analysis...")
        print("-" * 80)
        
        analysis = llm.analyze_code(
            prompt="Create a function to add two numbers",
            code="""def add(a, b):
    print(f"Adding {a} and {b}")  # debug print
    result = a + b
    return result

result = add(5, 3)  # hardcoded example"""
        )
        
        if analysis['success']:
            print(f"\n✅ Analysis successful!")
            print(f"API Used: {analysis['api_used'].upper()}")
            print(f"Model: {analysis['model']}")
            print(f"\nResponse:\n{analysis['analysis'][:500]}...")
        else:
            print(f"\n❌ Analysis failed: {analysis['error']}")
    
    print("\n" + "=" * 80)

