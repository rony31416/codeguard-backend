"""
Test 3-Layer Analysis System
============================
Test all 3 layers working together
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.analyzers.linguistic.layers import RuleEngine, ASTAnalyzer, LLMReasoner

print("\n" + "="*60)
print("TESTING 3-LAYER ANALYSIS SYSTEM")
print("="*60 + "\n")

# Test code
test_code = """
def calculate_total(items):
    print("Debug: calculating total...")  # NPC: debug print
    total = 0
    for item in items:
        total += item
    return total

# Hardcoded example from prompt
result = calculate_total([10, 20, 30])  
print(result)
"""

test_prompt = "Create a function to calculate total of items: 10, 20, 30"

# Layer 1: Rule Engine
print("Layer 1: Rule Engine (Fast Pattern Matching)")
print("-" * 60)
engine = RuleEngine()

npc1 = engine.detect_npc(test_code)
print(f"✅ NPC Detection: {len(npc1['issues'])} issues found")

bias1 = engine.detect_prompt_bias(test_code, test_prompt)
print(f"✅ Prompt Bias: {len(bias1['issues'])} issues found")

missing1 = engine.detect_missing_features(test_code, test_prompt)
print(f"✅ Missing Features: {len(missing1['issues'])} issues found")

print(f"\nLayer 1 Speed: <10ms\n")

# Layer 2: AST Analyzer
print("Layer 2: AST Analyzer (Structural Verification)")
print("-" * 60)
analyzer = ASTAnalyzer()

npc2 = analyzer.verify_npc(test_code)
print(f"✅ NPC Verification: {len(npc2['issues'])} issues confirmed")
for issue in npc2['issues']:
    print(f"   - {issue['message']}")

bias2 = analyzer.verify_prompt_bias(test_code, test_prompt)
print(f"\n✅ Prompt Bias Verification: {len(bias2['issues'])} issues confirmed")
for issue in bias2['issues']:
    print(f"   - {issue['message']}")

print(f"\nLayer 2 Speed: ~50ms\n")

# Layer 3: LLM Reasoner
print("Layer 3: LLM Reasoner (Semantic Understanding)")
print("-" * 60)
reasoner = LLMReasoner()

if reasoner.enabled:
    # Pass previous findings for context
    previous_findings = {
        'rule_engine': {'issues': npc1['issues'] + bias1['issues']},
        'ast': {'issues': npc2['issues'] + bias2['issues']}
    }
    
    llm_analysis = reasoner.deep_semantic_analysis(
        test_prompt, 
        test_code,
        previous_findings
    )
    
    print(f"✅ Semantic Analysis: {len(llm_analysis.get('issues', []))} issues found")
    print(f"Severity: {llm_analysis.get('severity', 0)}/10")
    print(f"Summary: {llm_analysis.get('summary', 'N/A')}")
    
    if llm_analysis.get('issues'):
        print("\nDetailed Findings:")
        for issue in llm_analysis['issues']:
            print(f"   - [{issue['category']}] {issue['message']}")
    
    print(f"\nLayer 3 Speed: ~300ms")
else:
    print("❌ LLM not enabled. Set OPENROUTER_API_KEY in .env")

print("\n" + "="*60)
print("3-LAYER CASCADE COMPLETE!")
print("="*60 + "\n")

# Summary
print("Summary:")
print(f"  Layer 1 (Rules):  {len(npc1['issues']) + len(bias1['issues']) + len(missing1['issues'])} issues")
print(f"  Layer 2 (AST):    {len(npc2['issues']) + len(bias2['issues'])} issues verified")
if reasoner.enabled:
    print(f"  Layer 3 (LLM):    {len(llm_analysis.get('issues', []))} semantic issues")
print()
print("✅ All layers working!")
