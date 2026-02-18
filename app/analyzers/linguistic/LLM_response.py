"""
OpenRouter API Integration - Simple & Free
Using google/gemma-3-12b-it:free model
"""

import os
import requests
import time
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")


class LLM:
    """Simple LLM wrapper using OpenRouter free model."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemma-3-12b-it:free"
        self.enabled = bool(self.api_key and self.api_key != "*****")
    
    def ask(self, prompt: str, max_retries: int = 3) -> str:
        """Ask the LLM a question."""
        if not self.enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=60
                )
                
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                
                elif r.status_code == 429:
                    wait = 2 ** attempt
                    print(f"Rate limited. Retry in {wait}s")
                    time.sleep(wait)
                
                else:
                    print(f"Error {r.status_code}:", r.text)
                    return None
            
            except Exception as e:
                print(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
        
        return None
    
    def is_alive(self) -> Dict[str, Any]:
        """Test if API works."""
        if not self.enabled:
            return {"status": "disabled", "message": "No API key"}
        
        try:
            response = self.ask("Reply with OK")
            if response:
                return {
                    "status": "alive",
                    "message": "Working",
                    "response": response
                }
            else:
                return {
                    "status": "error",
                    "message": "No response from API"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def analyze_code(self, prompt: str, code: str) -> Dict[str, Any]:
        """Analyze code for bugs."""
        if not self.enabled:
            return {"success": False, "error": "API not enabled"}
        
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
            response = self.ask(question)
            
            if response:
                return {
                    "success": True,
                    "analysis": response,
                    "model": self.model
                }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
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
    """Quick test"""
    llm = get_llm()
    
    print("Testing OpenRouter API...")
    print("-" * 60)
    
    result = llm.is_alive()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'alive':
        print(f"Response: {result.get('response', 'N/A')}")
        print("-" * 60)
        
        # Test code analysis
        print("\nTesting code analysis...")
        analysis = llm.analyze_code(
            prompt="Create a function to add two numbers",
            code="""def add(a, b):
    print(f"Adding {a} and {b}")  # debug print
    result = a + b
    return result

result = add(5, 3)  # hardcoded example"""
        )
        
        if analysis['success']:
            print("Analysis:")
            print(analysis['analysis'])
        else:
            print(f"Error: {analysis['error']}")
    
    print("-" * 60)
