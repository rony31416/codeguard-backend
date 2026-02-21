# Quick Start Guide - Linguistic Analysis

## Installation

### 1. Install NLP Libraries (Recommended)
```bash
cd F:\Codeguard\backend
pip install spacy sentence-transformers keybert scikit-learn
```

### 2. Download spaCy Model (Optional but recommended)
```bash
python -m spacy download en_core_web_sm
```

**Note**: System works without NLP libraries using regex fallback!

## Usage Examples

### Example 1: Detect NPC (Non-Prompted Consideration)
```python
from app.analyzers.linguistic_analyzer import LinguisticAnalyzer

prompt = "Write a function to add two numbers"
code = """
def add(a, b):
    # NPC: Logging not requested!
    print(f"Adding {a} + {b}")
    
    # NPC: Validation not requested!
    if not isinstance(a, (int, float)):
        raise TypeError("Invalid input")
    
    return a + b
"""

analyzer = LinguisticAnalyzer(prompt, code)
results = analyzer.analyze()

print(results['npc'])
# Output: {
#   "found": True,
#   "features": ["logging", "validation"],
#   "count": 2
# }
```

### Example 2: Detect Prompt-Biased Code
```python
prompt = "Check if name is valid. For example, 'Alice' is valid."
code = """
def is_valid_name(name):
    # WRONG: Hardcoded the example value!
    if name == "Alice":
        return True
    return False
"""

analyzer = LinguisticAnalyzer(prompt, code)
results = analyzer.analyze()

print(results['prompt_biased'])
# Output: {
#   "found": True,
#   "values": ["string: \"Alice\"", "hardcoded comparison: \"Alice\""],
#   "count": 2
# }
```

### Example 3: Detect Missing Features
```python
prompt = "Create a function that filters, removes duplicates, and sorts a list"
code = """
def process(items):
    # Only filters - missing dedup and sort!
    return [x for x in items if x > 0]
"""

analyzer = LinguisticAnalyzer(prompt, code)
results = analyzer.analyze()

print(results['missing_features'])
# Output: {
#   "found": True,
#   "features": ["'sort' action not implemented"],
#   "count": 1
# }
```

### Example 4: Detect Misinterpretation
```python
prompt = "Write a function that returns a list of even numbers"
code = """
def get_evens(nums):
    # WRONG: Prints instead of returning
    # WRONG: Returns string instead of list
    for n in nums:
        if n % 2 == 0:
            print(n)
    return "2, 4, 6, 8"
"""

analyzer = LinguisticAnalyzer(prompt, code)
results = analyzer.analyze()

print(results['misinterpretation'])
# Output: {
#   "found": True,
#   "score": 0.7,
#   "reasons": [
#     "prints instead of returning",
#     "returns string but expects list"
#   ]
# }
```

## Testing

### Run All Linguistic Tests
```bash
cd F:\Codeguard\backend
python test\test_linguistic_analysis.py
```

### Run Full 3-Stage Pipeline
```bash
python test\test_full_pipeline.py
```

### Quick Validation
```bash
python -c "from app.analyzers.linguistic_analyzer import LinguisticAnalyzer; print(' Working!')"
```

## Understanding Results

### `intent_match_score`
- **Range**: 0.0 to 1.0
- **0.0-0.2**: Very poor match (likely misinterpretation)
- **0.2-0.5**: Weak match (missing features or wrong approach)
- **0.5-0.8**: Good match (minor issues)
- **0.8-1.0**: Excellent match

### `npc` (Non-Prompted Consideration)
- **found**: Boolean - any unrequested features?
- **features**: List of unrequested features
- **count**: Number of violations

Common NPC patterns detected:
- Logging/debugging output
- Input validation
- Error handling
- Admin/auth checks
- Performance optimizations
- Sorting (when not requested)

### `prompt_biased`
- **found**: Boolean - any hardcoded examples?
- **values**: List of hardcoded values
- **count**: Number of violations

Detects:
- String literals from prompt examples
- Magic numbers from examples
- Hardcoded comparisons

### `missing_features`
- **found**: Boolean - any missing implementations?
- **features**: List of missing features
- **count**: Number of issues (max 5 shown)

Detects:
- Missing action verbs (create, sort, filter, etc.)
- Missing data types (list, dict, etc.)
- Missing return statements
- Missing error handling

### `misinterpretation`
- **found**: Boolean - fundamental misunderstanding?
- **score**: 0.0-1.0 severity score (>0.4 = serious)
- **reasons**: List of specific issues

Detects:
- Print vs Return mismatch
- Wrong data type
- Low semantic similarity
- Missing core function
- Wrong algorithm

## Troubleshooting

### Import Errors
If you see import warnings in VS Code, they're expected. The code has proper fallback mechanisms.

### Slow Performance
First run may be slow (downloading models). Subsequent runs are fast.

### No NLP Libraries
System works fine with regex fallback! Just less accurate for complex cases.

## Integration with Backend

Already integrated in `main.py`:
```python
# Stage 3 automatically runs in /api/analyze
linguistic_analyzer = LinguisticAnalyzer(request.prompt, request.code)
linguistic_results = linguistic_analyzer.analyze()
```

No code changes needed - just start using it!

## Example API Request
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to sum a list",
    "code": "def sum_list(nums): for n in nums: print(n)"
  }'
```

Response includes full linguistic analysis in `linguistic_results`.

---

**Status**:  Production Ready
**Last Updated**: February 17, 2026
