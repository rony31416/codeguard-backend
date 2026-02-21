# NEW 3-Stage Linguistic Analysis Architecture ✅

## Overview
**Complete redesign** to fix aggregation issues where bugs were vanishing (NPC missing, features disappearing).

### Old Architecture (REMOVED ❌)
```
Layer 1 (Rule Engine) → result
Layer 2 (AST Analyzer) → result
Layer 3 (LLM Reasoner) → result
Aggregator → combines all 3 → final verdict
```
**Problem:** Aggregation caused bugs to disappear when layers disagreed.

### New Architecture (IMPLEMENTED ✅)
```
Layer 1 (Rule Engine) → evidence
Layer 2 (AST Analyzer) → evidence  
Layer 3 (LLM) → receives both evidences → final verdict
```
**Solution:** LLM sees all evidence and makes one unified decision.

---

## 3-Stage Flow

### Stage 1: Rule Engine Evidence Collection
- **Purpose:** Fast pattern matching (~10ms)
- **Method:** Regex-based detection
- **Output:** Evidence dict with issues found

```python
layer1_evidence = self.rule_engine.detect_npc(self.code)
# Returns: {'found': True, 'issues': [...], 'confidence': 0.95}
```

### Stage 2: AST Analyzer Evidence Collection
- **Purpose:** Structural verification (~50ms)
- **Method:** Python AST analysis
- **Output:** Evidence dict with structural findings

```python
layer2_evidence = self.ast_analyzer.verify_npc(self.code)
# Returns: {'found': True, 'issues': [...], 'confidence': 1.0}
```

### Stage 3: LLM Final Verdict
- **Purpose:** Unified decision based on all evidence (~300ms)
- **Method:** AI-powered semantic analysis using **Dual APIs**:
  - **Primary:** Ollama (local/cloud, free, fast)  
  - **Fallback:** OpenRouter (free tier, if Ollama fails)
- **Input:** Prompt + Code + Layer 1 & 2 evidence
- **Output:** Final verdict with all bug details

```python
final_verdict = self.llm_reasoner.final_verdict(
    prompt=self.prompt,
    code=self.code,
    layer1_evidence=layer1_evidence,
    layer2_evidence=layer2_evidence,
    detector_type='npc'  # or 'prompt_bias', 'missing_feature', 'misinterpretation'
)
```

---

## Detector Types

### 1. NPC Detector (Non-Prompted Considerations)
Detects features added that weren't requested.

**Example:**
```python
Prompt: "add two numbers"
Code: Includes logging, validation, debug prints ← NPC bugs!
```

**Verdict Format:**
```json
{
    "found": true,
    "features": ["logging not requested", "validation not requested"],
    "count": 2,
    "confidence": 0.98,
    "severity": 6,
    "layers_used": ["layer1", "layer2", "layer3_llm"],
    "verdict_by": "llm"
}
```

### 2. Prompt Bias Detector (Hardcoded Example Values)
Detects hardcoded values from prompt examples.

**Example:**
```python
Prompt: "sort [3,1,2]"
Code: numbers = [3, 1, 2]  # Hardcoded! ← Prompt bias!
```

**Verdict Format:**
```json
{
    "found": true,
    "values": ["[3, 1, 2] hardcoded from prompt"],
    "count": 1,
    "confidence": 0.95,
    "severity": 7,
    "layers_used": ["layer1", "layer2", "layer3_llm"],
    "verdict_by": "llm"
}
```

### 3. Missing Feature Detector
Detects features explicitly requested but not implemented.

**Example:**
```python
Prompt: "validate email and phone"
Code: Only validates email ← Missing phone validation!
```

**Verdict Format:**
```json
{
    "found": true,
    "features": ["phone validation not implemented"],
    "count": 1,
    "confidence": 0.98,
    "severity": 8,
    "layers_used": ["layer1", "layer2", "layer3_llm"],
    "verdict_by": "llm"
}
```

### 4. Misinterpretation Detector
Detects fundamental misunderstanding of the task.

**Example:**
```python
Prompt: "calculate average"
Code: return sum(numbers)  # Returns sum not average! ← Misinterpretation!
```

**Verdict Format:**
```json
{
    "found": true,
    "reasons": ["returns sum instead of average"],
    "score": 8,
    "confidence": 0.98,
    "severity": 9,
    "layers_used": ["layer1", "layer2", "layer3_llm"],
    "verdict_by": "llm"
}
```

---

## LLM Final Verdict Method

### Method Signature
```python
def final_verdict(
    self, 
    prompt: str, 
    code: str, 
    layer1_evidence: Dict, 
    layer2_evidence: Dict, 
    detector_type: str
) -> Dict[str, Any]:
```

### How It Works

1. **Format Evidence:** Combine Layer 1 & 2 findings into readable text
2. **Create Targeted Prompt:** Build LLM prompt specific to detector type
3. **Get LLM Response:** Ask LLM for final verdict in JSON format
4. **Parse & Format:** Convert LLM response to standard format
5. **Fallback:** If LLM unavailable, combine Layer 1 & 2 directly

### LLM Prompts

Each detector has a specific prompt template:

**NPC Prompt Example:**
```
Based on evidence from Layer 1 (Rule Engine) and Layer 2 (AST Analyzer), 
determine if code contains unrequested features.

Evidence:
- Layer 1: Found 2 issues (logging, validation)
- Layer 2: Confirmed 2 structural issues

Return JSON:
{
    "found": true/false,
    "features": ["unrequested features"],
    "count": number,
    "confidence": 0.0-1.0,
    "severity": 0-10,
    "summary": "explanation"
}
```

---

## Fallback Mechanism

When LLM is not available (no API key), the system falls back to combining Layer 1 & 2:

```python
def _fallback_verdict(self, layer1, layer2, detector_type):
    # Prefer Layer 2 (AST) over Layer 1 (Rules)
    primary = layer2 if layer2.get('found') else layer1
    
    # Combine issues from both layers
    combined_issues = []
    for layer in [layer1, layer2]:
        if layer and layer.get('issues'):
            combined_issues.extend(layer['issues'])
    
    return {
        'found': len(combined_issues) > 0,
        'features': combined_issues,
        'confidence': max(layer1_conf, layer2_conf),
        'verdict_by': 'fallback'
    }
```

---

## Benefits Over Old Aggregation

### Old Aggregation Issues ❌
- Bugs vanished when layers disagreed
- Complex weighted averaging obscured findings
- Consensus logic was brittle
- NPC bugs disappeared in some cases
- Missing features got lost in aggregation

### New LLM Verdict Benefits ✅
- ✅ **No bugs disappear:** LLM sees ALL evidence
- ✅ **Simpler:** One verdict, not 3 + aggregation
- ✅ **Smarter:** LLM understands context better
- ✅ **Unified:** Single source of truth
- ✅ **Transparent:** Evidence + verdict clearly separated

---

## Code Changes Summary

### Modified Files:
1. **layer3_llm_reasoner.py** - Added `final_verdict()` method
2. **npc_detector.py** - Removed aggregation, use LLM verdict
3. **prompt_bias_detector.py** - Removed aggregation, use LLM verdict
4. **missing_feature_detector.py** - Removed aggregation, use LLM verdict
5. **misinterpretation_detector.py** - Removed aggregation, use LLM verdict

### Removed:
- `LayerAggregator` imports from all detectors
- Aggregation logic from all `detect()` methods
- Consensus/reliability calculation code

### Added:
- `final_verdict()` method in LLM reasoner
- 4 detector-specific prompt templates
- Evidence formatting helper methods
- Fallback mechanism for when LLM unavailable

---

## Testing

### Run Tests:
```bash
cd backend
python test/test_new_llm_verdict_flow.py
```

### Expected Output:
```
🚀 NEW 3-STAGE FLOW TEST
Stage 1: Rule Engine Evidence
Stage 2: AST Analyzer Evidence  
Stage 3: LLM Final Verdict

TEST 1: NPC Detector
✅ Found: True
📊 Features: ['logging', 'validation', 'debug print']
💯 Confidence: 0.98
⚠️  Severity: 6/10
🔍 Layers Used: ['layer1', 'layer2', 'layer3_llm']
🎯 Verdict By: llm

TEST 2: Prompt Bias Detector
✅ Found: True
📊 Values: ['[3,1,2] hardcoded']
...
```

---

## Migration Guide

### Old Code (REMOVED):
```python
# ❌ OLD: Aggregation approach
layer1 = self.rule_engine.detect()
layer2 = self.ast_analyzer.verify()
layer3 = self.llm_reasoner.analyze()
aggregated = self.aggregator.aggregate(layer1, layer2, layer3)
return aggregated
```

### New Code (CURRENT):
```python
# ✅ NEW: Evidence → LLM verdict
layer1_evidence = self.rule_engine.detect_npc(self.code)
layer2_evidence = self.ast_analyzer.verify_npc(self.code)
final_verdict = self.llm_reasoner.final_verdict(
    prompt=self.prompt,
    code=self.code,
    layer1_evidence=layer1_evidence,
    layer2_evidence=layer2_evidence,
    detector_type='npc'
)
return final_verdict
```

---

## Performance

### Typical Response Times:
- **Layer 1 (Rule Engine):** ~10ms
- **Layer 2 (AST Analyzer):** ~50ms
- **Layer 3 (LLM Verdict):** ~300ms
- **Total:** ~360ms (vs ~400ms with old aggregation)

### When LLM Unavailable:
- **Fallback Time:** ~60ms (Layer 1 + Layer 2 only)

---

## Environment Setup

### Primary LLM (Ollama - Recommended):
Set **OLLAMA_API_KEY** in environment or `.env` file:

```bash
OLLAMA_API_KEY=your-ollama-key-here
```

### Fallback LLM (OpenRouter):
Set **OPENROUTER_API_KEY** in environment or `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Dual API Behavior:
- ✅ **Both keys set:** Tries Ollama first, falls back to OpenRouter
- ✅ **Only Ollama:** Uses only Ollama
- ✅ **Only OpenRouter:** Uses only OpenRouter
- ⚠️ **Neither key:** Uses Layer 1 + Layer 2 combined evidence (no LLM)

---

## Status: ✅ COMPLETE

All 4 linguistic detectors now use the new 3-stage flow:
1. ✅ NPC Detector
2. ✅ Prompt Bias Detector
3. ✅ Missing Feature Detector
4. ✅ Misinterpretation Detector

**No more aggregation issues! LLM makes unified decisions based on all evidence.**
