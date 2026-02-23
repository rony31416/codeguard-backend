# Astroid Migration — Results & Comparison Report

**Date:** February 23, 2026 (re-run after Docker dynamic fix)  
**Scope:** Migration of CodeGuard static analysis from Python stdlib `ast` to `astroid` + Docker dynamic execution fix  
**Test method:** 160 HTTP POST requests to Render production backend (`https://codeguard-backend-g7ka.onrender.com/api/analyze`), across 10 test sets of 16 cases each.

> **Re-run note:** The previous `result_astroid/` run (2026-02-21) was performed while Docker dynamic execution was broken — user variables like `result = ...` could overwrite the wrapper's internal state, causing empty container stdout and `ParseError`. This run uses the fixed backend.

---

## 1. What Changed (Astroid Migration)

Eight source files were migrated from stdlib `ast` to `astroid`. The primary motivation was to gain:

- **Semantic type inference** via `node.expr.infer()` — replaces fragile regex-based attribute detection.
- **Scope-aware node classification** — `nodes.Name` is always a read, `nodes.AssignName` is always a write; no context-object check needed.
- **Cleaner traversal API** — `tree.nodes_of_class(NodeType)` replaces nested `ast.walk()` + `isinstance()` combos.
- **Fewer false positives** in hallucination and attribute detection.

### Files Modified

| File | Change Summary |
|---|---|
| `app/analyzers/static/detectors/syntax_detector.py` | `ast.parse` → `astroid.parse`; `SyntaxError` → `AstroidSyntaxError` |
| `app/analyzers/static/detectors/hallucination_detector.py` | Full rewrite using `nodes.Name`, `nodes.AssignName`, scoped traversal |
| `app/analyzers/static/detectors/wrong_attribute_detector.py` | Eliminated regex; now uses `node.expr.infer()` to detect dict objects semantically |
| `app/analyzers/static/detectors/wrong_input_type_detector.py` | `nodes.Const`, `nodes.Call` via `nodes_of_class()`, `node.func.name`/`attrname` |
| `app/analyzers/static/static_analyzer.py` | `import ast` → `import astroid` |
| `app/analyzers/linguistic/layers/layer2_ast_analyzer.py` | All `ast.walk()` → `nodes_of_class()`, `arg.arg` → `arg.name`, `node.module` → `node.modname` |
| `app/analyzers/linguistic/utils/ast_analyzer.py` | Full rewrite, decorators via `node.decorators.nodes`, recursion via scoped `nodes_of_class(nodes.Call)` |
| `requirements.txt` | Added `astroid` dependency |

### Key API Differences Applied

```
ast.walk(tree)                   →  tree.nodes_of_class(nodes.ClassName)
ast.Name (with ast.Load ctx)     →  nodes.Name  (always a read)
ast.Name (with ast.Store ctx)    →  nodes.AssignName
ast.Constant                     →  nodes.Const
ast.Attribute.attr               →  nodes.Attribute.attrname
ast.Name.id                      →  nodes.Name.name
ast.ImportFrom.module            →  nodes.ImportFrom.modname
arg.arg  (function params)       →  arg.name
ast.parse(code)                  →  astroid.parse(code)
except SyntaxError               →  except astroid_exceptions.AstroidSyntaxError
```

---

## 2. Test Configuration

| Parameter | Value |
|---|---|
| Backend | Render (production) |
| API endpoint | `/api/analyze` |
| Total test sets | 10 |
| Total test cases | 160 |
| Cases per set | 16 (8 buggy, 8 clean) |
| Request timeout | 120 s |
| Baseline run date | 2026-02-20 (stdlib ast, dynamic broken) |
| This run date | 2026-02-23 (astroid + Docker dynamic fixed) |

---

## 3. Overall Metrics Comparison

| Metric | Baseline (stdlib ast) | Post-Fix (astroid + Docker) | Change |
|---|---|---|---|
| **Total Cases** | 160 | 160 | — |
| **Correct Predictions** | 115 | **117** | **+2** |
| **Accuracy** | **71.88%** | **73.12%** | **+1.25%** ↑ |
| **Precision** | **68.42%** | **67.96%** | -0.46% |
| **Recall** | **81.25%** | **87.50%** | **+6.25%** ↑ |
| **F1 Score** | **74.29%** | **76.50%** | **+2.21%** ↑ |
| **Specificity** | **62.50%** | **58.75%** | -3.75% |
| **False Positive Rate** | 37.50% | 41.25% | +3.75% |
| **False Negative Rate** | 18.75% | **12.50%** | **-6.25%** ↓ |

### Confusion Matrix

|  | Predicted Bug | Predicted Clean |
|---|---|---|
| **Actual Bug** | TP: 65 → **70** | FN: 15 → **10** |
| **Actual Clean** | FP: 30 → **33** | TN: 50 → **47** |

> **Key change:** Working Docker dynamic execution now catches runtime bugs (ZeroDivisionError, AttributeError, NameError, TypeError) that the static layer alone missed. This raises Recall significantly (+6.25%) and reduces False Negatives from 15 → 10. The slight FPR increase (+3.75%) is a known trade-off when enabling dynamic detection — some clean code now triggers runtime-based signals.

---

## 4. Per-Test-Set Breakdown

| Set | Name | Baseline | Post-Fix | Δ | Notes |
|---|---|---|---|---|---|
| 1 | Basic Bug Patterns | 87.50% (14/16) | **93.75% (15/16)** | **+6.25%** ↑ | Improved |
| 2 | Advanced Bug Patterns | 68.75% (11/16) | **75.00% (12/16)** | **+6.25%** ↑ | Improved |
| 3 | Real-World Code Scenarios | 81.25% (13/16) | **81.25% (13/16)** | = | No change |
| 4 | Data Structures & API Usage | 68.75% (11/16) | **75.00% (12/16)** | **+6.25%** ↑ | Improved |
| 5 | Complex & Real-World Scenarios | 75.00% (12/16) | **75.00% (12/16)** | = | No change |
| 6 | Mixed Bugs & Complex Logic | 75.00% (12/16) | **68.75% (11/16)** | **-6.25%** ↓ | Regressed |
| 7 | Security & Edge Cases | 68.75% (11/16) | **68.75% (11/16)** | = | No change |
| 8 | OOP & Structural Bugs | 75.00% (12/16) | **68.75% (11/16)** | **-6.25%** ↓ | Regressed |
| 9 | Regression & Stress Testing | 62.50% (10/16) | **62.50% (10/16)** | = | No change |
| 10 | Production-Ready Code Patterns | 56.25% (9/16) | **62.50% (10/16)** | **+6.25%** ↑ | Improved |

---

## 5. Analysis

### 5.1 Where the Fix Helped (Improved Sets)

**Set 1 (+6.25%) — Basic Bug Patterns**  
With Docker dynamic execution now working, the `Missing Corner Case - Division Without Check` case is caught at runtime (ZeroDivisionError when called with `divide(10, 0)`), adding a detection signal on top of the static astroid check.

**Sets 2 & 4 (+6.25% each) — Advanced Bug Patterns / Data Structures & API Usage**  
The combination of astroid-based `wrong_attribute_detector` (semantic inference via `node.expr.infer()`) and runtime AttributeError capture jointly improves detection of dict dot-access and advanced attribute misuse.

**Set 10 (+6.25%) — Production-Ready Code Patterns**  
Runtime dynamic execution catches production-style bugs that require code execution to surface (e.g., resource leaks, deprecated-function calls that raise exceptions under certain inputs).

### 5.2 Where Regression Occurred

**Set 6 (-6.25%) — Mixed Bugs & Complex Logic**  
Some mixed-pattern cases involving advanced Python constructs (multiple inheritance, async functions, abstract base classes, `map`/`filter`) are now flagged by the dynamic layer when they were previously classified as clean by a static-only pipeline. The LLM is likely reacting to new dynamic signals.

**Set 8 (-6.25%) — OOP & Structural Bugs**  
OOP patterns like `super().__init__()`, property setters, magic methods, and abstract properties trigger dynamic analysis signals that push borderline cases over the bug threshold. These are false positives introduced by the more sensitive dynamic layer.

### 5.3 Stable Sets (No Change)

Sets 3, 5, 7, 9 are unchanged, confirming the core detection pipeline is stable. These sets involve code patterns that neither benefit from runtime detection nor regress from it.

---

## 6. Migration Quality Validation

The astroid migration unit tests (`test_astroid_migration.py`) passed all 7 groups before deployment:

```
1. SyntaxErrorDetector     [PASS] Good code / Bad code
2. HallucinatedObjectDetector  [PASS] CamelCase class / Clean code
3. WrongAttributeDetector  [PASS] Dict dot-access / Class attribute (no false positive)
4. WrongInputTypeDetector  [PASS] math.sqrt("hello") / math.sqrt(4)
5. Layer2 ASTAnalyzer      [PASS] NPC / Prompt bias / Return mismatch
6. Utils ASTAnalyzer       [PASS] Function names / calls / loops / recursion
7. StaticAnalyzer pipeline [PASS] End-to-end syntax error detection
```

---

## 7. Summary & Recommendations

| Finding | Detail |
|---|---|
| **Overall accuracy delta** | **+1.25%** (71.88% → 73.12%) |
| **Net gain in correct predictions** | +2 (115 → 117) |
| **Recall improvement** | +6.25% (81.25% → 87.50%) — 5 more bugs caught |
| **False Negative Rate** | -6.25% (18.75% → 12.50%) — 5 fewer misses |
| **FPR trade-off** | +3.75% (37.50% → 41.25%) — 3 more clean cases falsely flagged |
| **Migration stability** | 4/10 sets improved, 4/10 unchanged, 2/10 regressed |
| **Primary gain** | Docker dynamic execution catches runtime errors (ZeroDivision, AttributeError, NameError, TypeError) that static analysis misses |
| **Primary risk** | Dynamic layer increases FPR for complex OOP / async patterns |

### Next Steps (Recommended)

1. **Tune FP threshold for OOP patterns** — Sets 6 and 8 false positives involve complex clean OOP (multiple inheritance, property, async). Add a guard in `classifier.py` that discounts dynamic signals when the code contains no function calls with literal arguments.
2. **Calibrate severity scoring** — Cases falsely flagged carry severity 5–8. Raising the clean/bug threshold from `severity > 0` to `severity >= 4` would reduce false positives at small recall cost.
3. **Expand dynamic test harness** — The `test_docker_analysis.py` suite (20 cases) should be extended to cover OOP patterns — `super()`, property setters, abstract methods — to catch future regressions early.
4. **Track FPR separately per pattern** — Log which specific `_cg_result` error types drive false positives in Sets 6/8 to build a targeted suppression list.

---

## 8. Result File Locations

| Location | Contents |
|---|---|
| `app/final_test/results/` | Baseline (stdlib ast, dynamic broken) — 2026-02-20 |
| `app/final_test/result_astroid/` | Post-fix (astroid + working Docker dynamic) — 2026-02-23 |
| `app/final_test/run_tests_astroid.py` | Test runner used for this run (targets Render, saves to `result_astroid/`) |
| `app/final_test/compare_results.py` | Comparison script that generated `DYNAMIC_FIX_RESULTS.md` |
| `app/final_test/DYNAMIC_FIX_RESULTS.md` | Auto-generated diff report between results/ and result_astroid/ |
| `backend/test_astroid_migration.py` | Unit tests validating individual migrated components |
| `backend/test_docker_analysis.py` | 20-case Docker dynamic executor test suite |
