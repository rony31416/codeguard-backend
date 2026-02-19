# Static Analysis Module

## Overview

This module provides **organized static code analysis** for detecting various bug patterns in Python code. Each detector is isolated in its own file for better maintainability.

## Folder Structure

```
static/
├── __init__.py                    # Module exports
├── static_analyzer.py             # Main orchestrator
├── README.md                      # This file
└── detectors/                     # Individual detectors
    ├── __init__.py
    ├── syntax_detector.py         # Syntax errors (9/10)
    ├── hallucination_detector.py  # Undefined objects (8/10)
    ├── incomplete_detector.py     # Incomplete generation (7/10)
    ├── silly_mistake_detector.py  # Non-human patterns (6/10)
    ├── wrong_attribute_detector.py # Dict.key issues (7/10)
    ├── wrong_input_type_detector.py # Type mismatches (6/10)
    ├── prompt_bias_detector.py    # Hardcoded examples (variable)
    ├── npc_detector.py            # Unrequested features (variable)
    └── corner_case_detector.py    # Missing edge cases (5/10)
```

## Detectors

### 🔴 Critical (Severity 7-10)

1. **Syntax Error Detector** (9/10)
   - Detects Python syntax errors using AST parsing
   - Speed: <5ms
   - File: `syntax_detector.py`

2. **Hallucinated Object Detector** (8/10)
   - Detects undefined classes, functions, variables
   - Common with LLM-generated code
   - Speed: ~10ms
   - File: `hallucination_detector.py`

3. **Incomplete Generation Detector** (7/10)
   - Detects code that appears cut off or incomplete
   - Checks for empty assignments, incomplete loops, TODO markers
   - Speed: ~10ms
   - File: `incomplete_detector.py`

4. **Wrong Attribute Detector** (7/10)
   - Detects `dict.key` instead of `dict['key']`
   - Speed: ~5ms
   - File: `wrong_attribute_detector.py`

### 🟡 Medium-High (Severity 5-7)

5. **Silly Mistake Detector** (6/10)
   - Detects identical if/else branches
   - Detects reversed operands, type mismatches
   - Speed: ~10ms
   - File: `silly_mistake_detector.py`

6. **Wrong Input Type Detector** (6/10)
   - Detects string passed to `math.sqrt()`, etc.
   - Speed: ~10ms
   - File: `wrong_input_type_detector.py`

7. **Corner Case Detector** (5/10)
   - Detects missing critical edge case handling
   - Very conservative (only reports critical issues)
   - Speed: ~10ms
   - File: `corner_case_detector.py`

### 🟢 Variable Severity

8. **Prompt Bias Detector** (3-8/10)
   - Detects hardcoded example values from prompts
   - Speed: ~5ms
   - File: `prompt_bias_detector.py`

9. **NPC Detector** (3-6/10)
   - Detects non-prompted considerations
   - Very conservative
   - Speed: ~5ms
   - File: `npc_detector.py`

## Usage

### Basic Usage

```python
from app.analyzers.static import StaticAnalyzer

code = '''
def calculate_total(items)  # missing colon
    total = 0
    return total
'''

analyzer = StaticAnalyzer(code)
results = analyzer.analyze()

# Check for syntax errors
if results['syntax_error']['found']:
    print(f"Syntax error: {results['syntax_error']['error']}")

# Check for hallucinated objects
if results['hallucinated_objects']['found']:
    objects = results['hallucinated_objects']['objects']
    print(f"Undefined objects: {[obj['name'] for obj in objects]}")
```

### Individual Detector Usage

```python
from app.analyzers.static.detectors import SyntaxErrorDetector

detector = SyntaxErrorDetector(code)
result = detector.detect()

if result['found']:
    print(f"Syntax error at line {result['line']}: {result['error']}")
```

## Design Principles

1. **Modularity**: Each detector is independent and can be used standalone
2. **Fault Tolerance**: Individual detector failures don't crash the analysis
3. **Performance**: All detectors run in <20ms total
4. **Accuracy**: Conservative detection to minimize false positives
5. **Extensibility**: Easy to add new detectors

## Adding a New Detector

1. Create new file in `detectors/` folder
2. Implement detector class with `detect()` method
3. Add to `detectors/__init__.py`
4. Add to `static_analyzer.py` orchestrator
5. Update this README

### Template

```python
'''
New Detector
============
Brief description.

Pattern: Pattern Name
Severity: X/10
Speed: ~Xms
'''

from typing import Dict, Any


class NewDetector:
    """Detects specific pattern."""
    
    def __init__(self, code: str, tree: ast.AST = None):
        self.code = code
        self.tree = tree
    
    def detect(self) -> Dict[str, Any]:
        """
        Detect pattern.
        
        Returns:
            Dict with detection results
        """
        return {
            "found": False,
            "details": []
        }
```

## Testing

Run the comprehensive test suite:

```bash
python backend/test/test_comprehensive_patterns.py
```

Test individual detectors:

```bash
python backend/app/analyzers/static/detectors/syntax_detector.py
```

## Performance

- **Total Analysis Time**: <50ms for most code
- **Syntax Error**: <5ms
- **Hallucination Detection**: ~10ms
- **Other Detectors**: <10ms each

## Migration from Old Structure

The detectors were previously in a single `static_analyzer.py` file. This new structure:
- ✅ Separates concerns
- ✅ Improves readability
- ✅ Makes testing easier
- ✅ Allows parallel development
- ✅ Reduces merge conflicts

The old `static_analyzer.py` in the parent folder can be deprecated once migration is complete.
