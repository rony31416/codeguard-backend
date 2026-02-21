"""
Layer 3: LLM Reasoner
====================
Semantic understanding using Dual LLM APIs:
- Primary: Ollama (local/cloud, free, fast)
- Fallback: OpenRouter (free tier, if Ollama fails)
Handles edge cases and nuanced interpretation (~300ms).
"""

import json
from typing import Dict, List, Any
from ..LLM_response import get_llm


class LLMReasoner:
    """AI-powered semantic analysis using Dual APIs (Ollama → OpenRouter fallback)."""
    
    def __init__(self):
        """Initialize LLM reasoner."""
        self.llm = get_llm()
        self.enabled = self.llm.enabled
        self.confidence = 0.98  # High confidence for AI analysis
        
        # Debug logging
        if self.enabled:
            print(f"✓ Layer 3 (LLM)  Enabled - Using {'Ollama' if self.llm.ollama_enabled else ''} {'OpenRouter' if self.llm.openrouter_enabled else ''}")
        else:
            print("✗ Layer 3 (LLM)  Disabled - No API keys configured")
    
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
            print("  Layer 3 (LLM)  Skipped - No LLM APIs available")
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

CRITICAL DEFINITIONS - Read carefully before analyzing:

1. **NPC (Non-Prompted Consideration)**: Features/code added that were NOT requested
   - Example: User asks "add two numbers" but code includes logging, validation, type checking
   - Example: User asks "sort a list" but code includes caching, error handling, input sanitization
   - Report ONLY truly unrequested additions, not missing validations

2. **Prompt-Biased Code**: Using hardcoded values from prompt examples instead of general logic
   - Example: Prompt says "sort [3,1,2]" and code only works for those exact 3 numbers
   - Example: Using "test@example.com" as a hardcoded default instead of accepting any email

3. **Missing Features**: Features EXPLICITLY mentioned in prompt but NOT implemented
   - ONLY report if the feature was clearly requested in the original prompt
   - Example: Prompt says "validate email and phone" but code only validates email
   - DO NOT report general best practices (error handling, edge cases) unless explicitly requested
   - If prompt is simple (e.g., "add two numbers"), missing_features should be EMPTY []

4. **Misinterpretation**: Code does something fundamentally different from what was asked
   - Example: User asks to "remove duplicates" but code sorts instead
   - Example: User asks for "average" but code returns sum

STRICT RULES:
- Be conservative with "missing_features" - ONLY report explicitly requested items
- If the prompt is simple/minimal, missing_features should be [] or very short
- Don't confuse critiques of NPC with missing features
- Unrequested edge case handling = NPC, not a missing feature
- Ignore standard Pythonic structures like lambda functions, @property decorators, and list comprehensions. They are NOT unrequested features.

Return ONLY valid JSON in this exact format:
{{
    "npc_issues": ["specific unrequested features found in code"],
    "prompt_bias_issues": ["hardcoded example values or logic"],
    "missing_features": ["features explicitly requested but not implemented - be conservative"],
    "misinterpretation": ["fundamental mismatches between request and implementation"],
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
    
    def final_verdict(self, prompt: str, code: str, layer1_evidence: Dict, layer2_evidence: Dict, detector_type: str) -> Dict[str, Any]:
        """
        LLM makes final verdict based on combined evidence from Layer 1 & 2.
        
        Args:
            prompt: User's original prompt
            code: Generated code
            layer1_evidence: Evidence from Rule Engine (Layer 1)
            layer2_evidence: Evidence from AST Analyzer (Layer 2)
            detector_type: 'npc' | 'prompt_bias' | 'missing_feature' | 'misinterpretation'
        
        Returns:
            Final verdict with all required fields
        """
        if not self.enabled:
            print(f"  Layer 3 (LLM)  Skipped - No LLM APIs available")
            # Fallback to combined Layer 1 & 2 results
            return self._fallback_verdict(layer1_evidence, layer2_evidence, detector_type)
        
        # Build evidence summary
        evidence_summary = self._format_evidence(layer1_evidence, layer2_evidence)
        
        # Create targeted prompt based on detector type
        if detector_type == 'npc':
            question = self._create_npc_verdict_prompt(prompt, code, evidence_summary)
        elif detector_type == 'prompt_bias':
            question = self._create_prompt_bias_verdict_prompt(prompt, code, evidence_summary)
        elif detector_type == 'missing_feature':
            question = self._create_missing_feature_verdict_prompt(prompt, code, evidence_summary)
        elif detector_type == 'misinterpretation':
            question = self._create_misinterpretation_verdict_prompt(prompt, code, evidence_summary)
        else:
            raise ValueError(f"Unknown detector type: {detector_type}")
        
        try:
            result = self.llm.ask(question)
            
            if not result:
                return self._fallback_verdict(layer1_evidence, layer2_evidence, detector_type)
            
            # Parse JSON response
            try:
                if '```json' in result:
                    result = result.split('```json')[1].split('```')[0].strip()
                elif '```' in result:
                    result = result.split('```')[1].split('```')[0].strip()
                
                verdict = json.loads(result)
                
                # Format response based on detector type
                return self._format_verdict_response(verdict, detector_type)
            
            except (json.JSONDecodeError, ValueError) as e:
                print(f"  LLM JSON parse error: {e}")
                return self._fallback_verdict(layer1_evidence, layer2_evidence, detector_type)
        
        except Exception as e:
            print(f"  LLM error: {e}")
            return self._fallback_verdict(layer1_evidence, layer2_evidence, detector_type)
    
    def _format_evidence(self, layer1: Dict, layer2: Dict) -> str:
        """Format Layer 1 & 2 evidence for LLM."""
        evidence = []
        
        if layer1 and layer1.get('issues'):
            evidence.append(f"**Layer 1 (Rule Engine) Findings:**")
            evidence.append(f"- Found: {layer1.get('found', False)}")
            evidence.append(f"- Issues Count: {len(layer1.get('issues', []))}")
            evidence.append(f"- Confidence: {layer1.get('confidence', 0)}")
            for issue in layer1.get('issues', [])[:5]:  # Limit to 5
                evidence.append(f"  - {issue.get('message', issue)}")
        
        if layer2 and layer2.get('issues'):
            evidence.append(f"\n**Layer 2 (AST Analyzer) Findings:**")
            evidence.append(f"- Found: {layer2.get('found', False)}")
            evidence.append(f"- Issues Count: {len(layer2.get('issues', []))}")
            evidence.append(f"- Confidence: {layer2.get('confidence', 0)}")
            for issue in layer2.get('issues', [])[:5]:
                evidence.append(f"  - {issue.get('message', issue)}")
        
        return "\n".join(evidence) if evidence else "No evidence found by Layer 1 or Layer 2"
    
    def _create_npc_verdict_prompt(self, prompt: str, code: str, evidence: str) -> str:
        """Create LLM prompt for NPC detection verdict."""
        return f"""You are analyzing code for Non-Prompted Considerations (NPC).

**USER'S ORIGINAL PROMPT:**
{prompt}

**GENERATED CODE:**
```python
{code}
```

**EVIDENCE FROM PREVIOUS LAYERS:**
{evidence}

**YOUR TASK:**
Based on the evidence from Layer 1 (Rule Engine) and Layer 2 (AST Analyzer), make your final verdict.

**Definition of NPC:** Features or code added that were NOT explicitly requested in the prompt.
- Example: User asks "add two numbers" but code includes logging, validation, type checking
- Example: User asks "sort a list" but code includes caching, error handling

**Be conservative:** Only report truly unrequested additions, not missing validations.

Return JSON in this exact format:
{{
    "found": true/false,
    "features": ["list of unrequested features found"],
    "count": number_of_npc_issues,
    "confidence": 0.0-1.0,
    "severity": 0-10,
    "summary": "brief explanation"
}}"""
    
    def _create_prompt_bias_verdict_prompt(self, prompt: str, code: str, evidence: str) -> str:
        """Create LLM prompt for Prompt Bias detection verdict."""
        return f"""You are analyzing code for Prompt Bias (hardcoded example values).

**USER'S ORIGINAL PROMPT:**
{prompt}

**GENERATED CODE:**
```python
{code}
```

**EVIDENCE FROM PREVIOUS LAYERS:**
{evidence}

**YOUR TASK:**
Based on the evidence, determine if code uses hardcoded values from prompt examples instead of general logic.

**Definition of Prompt Bias:** Using specific example values from prompt as hardcoded defaults.
- Example: Prompt says "sort [3,1,2]" and code only works for those exact 3 numbers
- Example: Using "test@example.com" as hardcoded default instead of accepting any email

Return JSON in this exact format:
{{
    "found": true/false,
    "values": ["list of hardcoded values found"],
    "count": number_of_bias_issues,
    "confidence": 0.0-1.0,
    "severity": 0-10,
    "summary": "brief explanation"
}}"""
    
    def _create_missing_feature_verdict_prompt(self, prompt: str, code: str, evidence: str) -> str:
        """Create LLM prompt for Missing Feature detection verdict."""
        return f"""You are analyzing code for Missing Features.

**USER'S ORIGINAL PROMPT:**
{prompt}

**GENERATED CODE:**
```python
{code}
```

**EVIDENCE FROM PREVIOUS LAYERS:**
{evidence}

**YOUR TASK:**
Based on the evidence, determine what features were EXPLICITLY requested but NOT implemented.

**CRITICAL - BE EXTREMELY CONSERVATIVE:**
- ONLY report features that were EXPLICITLY and CLEARLY mentioned in the original prompt
- DO NOT report:
  - Type variations (e.g., returning 0.0 instead of 0 is fine for numeric functions)
  - General best practices (error handling, validation) unless EXPLICITLY requested
  - Defensive programming (None checks, type checking) unless EXPLICITLY requested
  - Edge case handling unless EXPLICITLY mentioned in prompt
- If the feature is implemented in a slightly different way but achieves the same goal, DO NOT report it
- When in doubt, DO NOT report it
- If prompt is simple (e.g., "add two numbers"), missing_features should be EMPTY []

**Example of what TO report:**
- Prompt: "validate email AND phone" → Code only validates email ← REPORT: Missing phone validation
- Prompt: "return both sum and product" → Code only returns sum ← REPORT: Missing product return

**Example of what NOT to report:**
- Prompt: "return 0" → Code returns 0.0 ← DO NOT REPORT: Same thing
- Prompt: "calculate average" → Code doesn't check for None ← DO NOT REPORT: Not requested
- Prompt: "add numbers" → No error handling ← DO NOT REPORT: Not requested

Return JSON in this exact format:
{{
    "found": true/false,
    "features": ["list of explicitly requested but missing features"],
    "count": number_of_missing_features,
    "confidence": 0.0-1.0,
    "severity": 0-10,
    "summary": "brief explanation"
}}"""
    
    def _create_misinterpretation_verdict_prompt(self, prompt: str, code: str, evidence: str) -> str:
        """Create LLM prompt for Misinterpretation detection verdict."""
        return f"""You are analyzing code for Fundamental Misinterpretation.

**USER'S ORIGINAL PROMPT:**
{prompt}

**GENERATED CODE:**
```python
{code}
```

**EVIDENCE FROM PREVIOUS LAYERS:**
{evidence}

**YOUR TASK:**
Based on the evidence, determine if code does something fundamentally different from what was asked.

**Definition of Misinterpretation:** Code does something fundamentally different from the request.
- Example: User asks to "remove duplicates" but code sorts instead
- Example: User asks for "average" but code returns sum
- Example: User asks for "factorial" but code returns fibonacci

Return JSON in this exact format:
{{
    "found": true/false,
    "reasons": ["list of misinterpretations found"],
    "score": 0-10 (severity),
    "confidence": 0.0-1.0,
    "severity": 0-10,
    "summary": "brief explanation"
}}"""
    
    def _format_verdict_response(self, verdict: Dict, detector_type: str) -> Dict[str, Any]:
        """Format LLM verdict into standard response format."""
        if detector_type == 'npc':
            return {
                'found': verdict.get('found', False),
                'features': verdict.get('features', []),
                'count': verdict.get('count', 0),
                'confidence': verdict.get('confidence', 0.98),
                'severity': verdict.get('severity', 0),
                'summary': verdict.get('summary', ''),
                'layers_used': ['layer1', 'layer2', 'layer3_llm'],
                'verdict_by': 'llm'
            }
        elif detector_type == 'prompt_bias':
            return {
                'found': verdict.get('found', False),
                'values': verdict.get('values', []),
                'count': verdict.get('count', 0),
                'confidence': verdict.get('confidence', 0.98),
                'severity': verdict.get('severity', 0),
                'summary': verdict.get('summary', ''),
                'layers_used': ['layer1', 'layer2', 'layer3_llm'],
                'verdict_by': 'llm'
            }
        elif detector_type == 'missing_feature':
            return {
                'found': verdict.get('found', False),
                'features': verdict.get('features', []),
                'count': verdict.get('count', 0),
                'confidence': verdict.get('confidence', 0.98),
                'severity': verdict.get('severity', 0),
                'summary': verdict.get('summary', ''),
                'layers_used': ['layer1', 'layer2', 'layer3_llm'],
                'verdict_by': 'llm'
            }
        elif detector_type == 'misinterpretation':
            return {
                'found': verdict.get('found', False),
                'reasons': verdict.get('reasons', []),
                'score': verdict.get('score', 0),
                'confidence': verdict.get('confidence', 0.98),
                'severity': verdict.get('severity', 0),
                'summary': verdict.get('summary', ''),
                'layers_used': ['layer1', 'layer2', 'layer3_llm'],
                'verdict_by': 'llm'
            }
    
    def _fallback_verdict(self, layer1: Dict, layer2: Dict, detector_type: str) -> Dict[str, Any]:
        """Fallback verdict when LLM is not available - combine Layer 1 & 2."""
        # Prefer Layer 2 (AST) over Layer 1 (Rules) when both available
        primary = layer2 if (layer2 and layer2.get('found')) else layer1
        
        if not primary or not primary.get('found'):
            # No bugs found
            if detector_type == 'npc':
                return {'found': False, 'features': [], 'count': 0, 'confidence': 0.95, 'severity': 0, 'layers_used': ['layer1', 'layer2'], 'verdict_by': 'fallback'}
            elif detector_type == 'prompt_bias':
                return {'found': False, 'values': [], 'count': 0, 'confidence': 0.95, 'severity': 0, 'layers_used': ['layer1', 'layer2'], 'verdict_by': 'fallback'}
            elif detector_type == 'missing_feature':
                return {'found': False, 'features': [], 'count': 0, 'confidence': 0.95, 'severity': 0, 'layers_used': ['layer1', 'layer2'], 'verdict_by': 'fallback'}
            elif detector_type == 'misinterpretation':
                return {'found': False, 'reasons': [], 'score': 0, 'confidence': 0.95, 'severity': 0, 'layers_used': ['layer1', 'layer2'], 'verdict_by': 'fallback'}
        
        # Combine findings from both layers
        combined_issues = []
        for layer in [layer1, layer2]:
            if layer and layer.get('issues'):
                for issue in layer.get('issues', []):
                    msg = issue.get('message', str(issue))
                    if msg not in combined_issues:
                        combined_issues.append(msg)
        
        confidence = max(
            layer1.get('confidence', 0) if layer1 else 0,
            layer2.get('confidence', 0) if layer2 else 0
        )
        
        if detector_type == 'npc':
            return {
                'found': True,
                'features': combined_issues,
                'count': len(combined_issues),
                'confidence': confidence,
                'severity': primary.get('severity', 5),
                'layers_used': ['layer1', 'layer2'],
                'verdict_by': 'fallback'
            }
        elif detector_type == 'prompt_bias':
            return {
                'found': True,
                'values': combined_issues,
                'count': len(combined_issues),
                'confidence': confidence,
                'severity': primary.get('severity', 5),
                'layers_used': ['layer1', 'layer2'],
                'verdict_by': 'fallback'
            }
        elif detector_type == 'missing_feature':
            return {
                'found': True,
                'features': combined_issues,
                'count': len(combined_issues),
                'confidence': confidence,
                'severity': primary.get('severity', 5),
                'layers_used': ['layer1', 'layer2'],
                'verdict_by': 'fallback'
            }
        elif detector_type == 'misinterpretation':
            return {
                'found': True,
                'reasons': combined_issues,
                'score': primary.get('severity', 5),
                'confidence': confidence,
                'severity': primary.get('severity', 5),
                'layers_used': ['layer1', 'layer2'],
                'verdict_by': 'fallback'
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
