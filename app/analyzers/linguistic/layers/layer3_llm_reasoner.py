"""
Layer 3: LLM Reasoner
====================
Semantic understanding using OpenRouter AI.
Handles edge cases and nuanced interpretation (~300ms).
"""

import json
from typing import Dict, List, Any
from ..LLM_response import get_llm


class LLMReasoner:
    """AI-powered semantic analysis using OpenRouter."""
    
    def __init__(self):
        """Initialize LLM reasoner."""
        self.llm = get_llm()
        self.enabled = self.llm.enabled
        self.confidence = 0.98  # High confidence for AI analysis
        
        # Debug logging
        if self.enabled:
            print(f"✓ Layer 3 (LLM) ✅ Enabled - Using {'Ollama' if self.llm.ollama_enabled else ''} {'OpenRouter' if self.llm.openrouter_enabled else ''}")
        else:
            print("✗ Layer 3 (LLM) ❌ Disabled - No API keys configured")
    
    def deep_semantic_analysis(self, prompt: str, code: str, previous_findings: Dict = None) -> Dict[str, Any]:
        """
        Perform deep semantic analysis with context from previous layers.
        
        Args:
            prompt: User's original prompt
            code: Generated code
            previous_findings: Results from Layer 1 and Layer 2
        
        Returns:
            Dict with semantic analysis results
        """
        if not self.enabled:
            print("⚠️  Layer 3 (LLM) ❌ Skipped - No LLM APIs available")
            return {
                'found': False,
                'issues': [],
                'layer': 'llm',
                'confidence': 0,
                'message': 'LLM not enabled'
            }
        
        # Build context from previous findings
        context = ""
        if previous_findings:
            context = "\n\nPrevious Analysis Findings:\n"
            if previous_findings.get('rule_engine'):
                context += f"- Rule Engine: {len(previous_findings['rule_engine'].get('issues', []))} issues\n"
            if previous_findings.get('ast'):
                context += f"- AST Analysis: {len(previous_findings['ast'].get('issues', []))} issues\n"
        
        # Construct analysis prompt
        question = f"""You are a code analysis expert. Analyze this code for semantic bugs and misinterpretations.

USER'S ORIGINAL PROMPT:
{prompt}

GENERATED CODE:
```python
{code}
```{context}

Your task:
1. Check if the code semantically matches what the user asked for
2. Look for subtle NPC bugs (non-prompted considerations like missing edge cases)
3. Identify prompt-biased implementations (too literal interpretation)
4. Find missing features the user likely expected
5. Detect misinterpretations of user intent

Focus on:
- Semantic correctness (does it do what was asked?)
- Edge cases and error handling
- User expectations vs implementation
- Subtle bugs that patterns/AST can't catch

Return ONLY valid JSON in this exact format:
{{
    "npc_issues": ["semantic NPC bugs found"],
    "prompt_bias_issues": ["prompt interpretation issues"],
    "missing_features": ["expected but missing features"],
    "misinterpretation": ["intent mismatches"],
    "severity": 0-10,
    "summary": "brief semantic analysis summary",
    "confidence": 0.0-1.0
}}"""
        
        try:
            result = self.llm.ask(question)
            
            if not result:
                return {
                    'found': False,
                    'issues': [],
                    'layer': 'llm',
                    'confidence': 0,
                    'error': 'No response from LLM'
                }
            
            # Try to parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if '```json' in result:
                    result = result.split('```json')[1].split('```')[0].strip()
                elif '```' in result:
                    result = result.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(result)
                
                # Validate structure
                required_keys = ['npc_issues', 'prompt_bias_issues', 'missing_features', 'misinterpretation']
                if not all(k in analysis for k in required_keys):
                    raise ValueError("Missing required keys in LLM response")
                
                # Extract issues
                all_issues = []
                
                for npc in analysis.get('npc_issues', []):
                    all_issues.append({
                        'type': 'npc_semantic',
                        'message': npc,
                        'category': 'npc',
                        'confidence': analysis.get('confidence', self.confidence)
                    })
                
                for bias in analysis.get('prompt_bias_issues', []):
                    all_issues.append({
                        'type': 'prompt_bias_semantic',
                        'message': bias,
                        'category': 'prompt_bias',
                        'confidence': analysis.get('confidence', self.confidence)
                    })
                
                for missing in analysis.get('missing_features', []):
                    all_issues.append({
                        'type': 'missing_feature_semantic',
                        'message': missing,
                        'category': 'missing',
                        'confidence': analysis.get('confidence', self.confidence)
                    })
                
                for misint in analysis.get('misinterpretation', []):
                    all_issues.append({
                        'type': 'misinterpretation_semantic',
                        'message': misint,
                        'category': 'misinterpretation',
                        'confidence': analysis.get('confidence', self.confidence)
                    })
                
                return {
                    'found': len(all_issues) > 0,
                    'issues': all_issues,
                    'severity': analysis.get('severity', 0),
                    'summary': analysis.get('summary', ''),
                    'layer': 'llm',
                    'confidence': analysis.get('confidence', self.confidence),
                    'raw_response': result
                }
            
            except (json.JSONDecodeError, ValueError) as e:
                # LLM didn't return valid JSON, try to extract meaning
                return {
                    'found': True,
                    'issues': [{
                        'type': 'llm_analysis',
                        'message': result[:500],  # First 500 chars
                        'confidence': 0.7
                    }],
                    'layer': 'llm',
                    'confidence': 0.7,
                    'error': f'JSON parse error: {str(e)}',
                    'raw_response': result
                }
        
        except Exception as e:
            return {
                'found': False,
                'issues': [],
                'layer': 'llm',
                'confidence': 0,
                'error': str(e)
            }
    
    def verify_misinterpretation(self, prompt: str, code: str) -> Dict[str, Any]:
        """
        Focused analysis on whether code matches user intent.
        
        Args:
            prompt: User's prompt
            code: Generated code
        
        Returns:
            Dict with misinterpretation analysis
        """
        if not self.enabled:
            return {'found': False, 'issues': [], 'layer': 'llm', 'confidence': 0}
        
        question = f"""Does this code correctly implement what the user asked for?

USER ASKED FOR:
{prompt}

CODE GENERATED:
```python
{code}
```

Analyze if there's any misinterpretation:
1. Does the code do what was asked?
2. Are there assumptions that don't match the request?
3. Is the implementation approach appropriate?

Return JSON:
{{
    "correct_interpretation": true/false,
    "mismatches": ["list of intent mismatches"],
    "severity": 0-10
}}"""
        
        try:
            result = self.llm.ask(question)
            
            if result and '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            
            analysis = json.loads(result)
            
            issues = []
            for mismatch in analysis.get('mismatches', []):
                issues.append({
                    'type': 'intent_mismatch',
                    'message': mismatch,
                    'confidence': self.confidence
                })
            
            return {
                'found': len(issues) > 0,
                'issues': issues,
                'correct': analysis.get('correct_interpretation', True),
                'severity': analysis.get('severity', 0),
                'layer': 'llm',
                'confidence': self.confidence
            }
        
        except Exception as e:
            return {
                'found': False,
                'issues': [],
                'layer': 'llm',
                'confidence': 0,
                'error': str(e)
            }


if __name__ == "__main__":
    """Quick test"""
    reasoner = LLMReasoner()
    
    if not reasoner.enabled:
        print("LLM not enabled. Set OPENROUTER_API_KEY in .env")
        exit(1)
    
    test_code = """
def add_numbers(a, b):
    print(f"Adding {a} and {b}")
    return a + b

result = add_numbers(5, 3)
print(result)
"""
    
    test_prompt = "Create a function to add two numbers"
    
    print("Testing LLM Reasoner...")
    print("-" * 60)
    
    print("\nDeep Semantic Analysis:")
    analysis = reasoner.deep_semantic_analysis(test_prompt, test_code)
    print(f"Found: {analysis['found']}")
    print(f"Issues: {len(analysis.get('issues', []))}")
    print(f"Severity: {analysis.get('severity', 0)}/10")
    print(f"Summary: {analysis.get('summary', 'N/A')}")
    
    if analysis.get('issues'):
        print("\nDetailed Issues:")
        for issue in analysis['issues']:
            print(f"  - [{issue['category']}] {issue['message']}")
    
    print("-" * 60)
