# Dynamic Fix — Full Test Results & Comparison

**Date:** 2026-02-23  
**What changed:** Docker dynamic execution was broken (user variables could collide with
the wrapper's internal `result` dict, causing empty stdout and ParseError).
Fixed by executing user code in an isolated namespace (`_cg_ns`) and renaming
all wrapper variables with `_cg_` prefix.  Added `_parse_json_output()` helper
to extract JSON from mixed container output.  Also hardened Windows path conversion.

**Baseline (pre-fix):** `results/` — run 2026-02-20, stdlib `ast`, dynamic execution non-functional
**New run (post-fix):** `result_astroid/` — run today, astroid + working Docker dynamic execution

---

## 1. Overall Metrics Comparison

| Metric | Baseline (pre-fix) | Post-Fix | Δ | |
|---|---|---|---|---|
| **Total Cases** | 160 | 160 | 0 |  |
| **Correct** | 115 | 117 | +2 |  |
| **Accuracy** | 71.88% | 73.12% | +1.25% ↑ |  |
| **Precision** | 68.42% | 67.96% | -0.46% ↓ |  |
| **Recall** | 81.25% | 87.50% | +6.25% ↑ |  |
| **F1 Score** | 74.29% | 76.50% | +2.22% ↑ |  |
| **Specificity** | 62.50% | 58.75% | -3.75% ↓ |  |
| **False Positive Rate** | 37.50% | 41.25% | +3.75% ↓ | (lower is better) |
| **False Negative Rate** | 18.75% | 12.50% | -6.25% ↑ | (lower is better) |

### Confusion Matrix

|  | Predicted Bug | Predicted Clean |
|---|---|---|
| **Actual Bug**   | TP: 65 → **70** | FN: 15 → **10** |
| **Actual Clean** | FP: 30 → **33** | TN: 50 → **47** |

---

## 2. Per-Test-Set Breakdown

| Set | Name | Baseline | Post-Fix | Δ | Notes |
|---|---|---|---|---|---|
| 1 | Basic Bug Patterns | 87.50% (14/16) | 93.75% (15/16) | +6.25% | **Improved** ↑ |
| 2 | Advanced Bug Patterns | 68.75% (11/16) | 75.00% (12/16) | +6.25% | **Improved** ↑ |
| 3 | Real-World Code Scenarios | 81.25% (13/16) | 81.25% (13/16) | +0.00% | Unchanged = |
| 4 | Data Structures & API Usage | 68.75% (11/16) | 75.00% (12/16) | +6.25% | **Improved** ↑ |
| 5 | Complex & Real-World Scenarios | 75.00% (12/16) | 75.00% (12/16) | +0.00% | Unchanged = |
| 6 | Mixed Bugs & Complex Logic | 75.00% (12/16) | 68.75% (11/16) | -6.25% | **Regressed** ↓ |
| 7 | Security & Edge Cases | 68.75% (11/16) | 68.75% (11/16) | +0.00% | Unchanged = |
| 8 | OOP & Structural Bugs | 75.00% (12/16) | 68.75% (11/16) | -6.25% | **Regressed** ↓ |
| 9 | Regression & Stress Testing | 62.50% (10/16) | 62.50% (10/16) | +0.00% | Unchanged = |
| 10 | Production-Ready Code Patterns | 56.25% (9/16) | 62.50% (10/16) | +6.25% | **Improved** ↑ |

---

## 3. Analysis

### 3.1 Improvements

**Set 1 (+6.25%) — Basic Bug Patterns**  
The working Docker dynamic execution can now actually run user code and catch
runtime errors (ZeroDivisionError, AttributeError, etc.) that the static layer alone
was missing. This is the primary source of accuracy gains in this run.

**Set 2 (+6.25%) — Advanced Bug Patterns**  
The working Docker dynamic execution can now actually run user code and catch
runtime errors (ZeroDivisionError, AttributeError, etc.) that the static layer alone
was missing. This is the primary source of accuracy gains in this run.

**Set 4 (+6.25%) — Data Structures & API Usage**  
The working Docker dynamic execution can now actually run user code and catch
runtime errors (ZeroDivisionError, AttributeError, etc.) that the static layer alone
was missing. This is the primary source of accuracy gains in this run.

**Set 10 (+6.25%) — Production-Ready Code Patterns**  
The working Docker dynamic execution can now actually run user code and catch
runtime errors (ZeroDivisionError, AttributeError, etc.) that the static layer alone
was missing. This is the primary source of accuracy gains in this run.

### 3.2 Regressions

**Set 6 (-6.25%) — Mixed Bugs & Complex Logic**  
Some regressions may stem from the dynamic layer now actively classifying code that
was previously skipped (dynamic analysis returning False < now returning True), or
the LLM verdict being influenced by new dynamic signals that change classification.

**Set 8 (-6.25%) — OOP & Structural Bugs**  
Some regressions may stem from the dynamic layer now actively classifying code that
was previously skipped (dynamic analysis returning False < now returning True), or
the LLM verdict being influenced by new dynamic signals that change classification.

### 3.3 Unchanged Sets

Sets 3, 5, 7, 9 showed no measurable change. These test cases are likely dominated
by static analysis signals that were already working, or involve code patterns
not triggered by the runtime sandbox (e.g., import errors, pure type mismatches).

---

## 4. Key Fix Summary

| Fix | Detail |
|---|---|
| **Isolated exec namespace** | `exec(code, _cg_ns)` — user's `result = ...` can no longer overwrite wrapper bookkeeping |
| **`_cg_` variable prefix** | All wrapper-internal vars renamed to avoid any collision with user code |
| **`_parse_json_output()`** | Scans container logs from last line upward for first valid JSON, handles mixed output |
| **Windows path conversion** | `C:\path` → `/c/path` uses `temp_dir[0].lower() + temp_dir[2:]` — no split(':') edge cases |
| **`remove=False` + finally** | Container kept alive until logs are read, then force-removed |

---

## 5. Result File Locations

| Location | Contents |
|---|---|
| `app/final_test/results/` | Baseline pre-fix results (stdlb ast, dynamic broken) |
| `app/final_test/result_astroid/` | Post-fix results (astroid + working Docker dynamic) |
| `app/final_test/compare_results.py` | This comparison script |
| `app/final_test/DYNAMIC_FIX_RESULTS.md` | Generated comparison report |
