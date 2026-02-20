# Test Results Summary

## Overview

**Test Suite**: Final Test Suite v2.0 (JSON Format)  
**Total Test Cases**: 160 (10 sets × 16 cases each)  
**Date**: February 20, 2026  
**Test Runner**: `run_all_tests.py` (Unified)

## Overall Performance

| Metric | Value | Description |
|--------|-------|-------------|
| **Accuracy** | 66.88% | Overall correctness (107/160) |
| **Precision** | 72.88% | True bugs / All detected bugs |
| **Recall** | 53.75% | True bugs detected / All real bugs |
| **F1 Score** | 61.87% | Harmonic mean of Precision & Recall |
| **Specificity** | 80.00% | Clean code correctly identified |

## Confusion Matrix

|  | Predicted Bug | Predicted Clean |
|---|---|---|
| **Actual Bug** | TP: 43 | FN: 37 |
| **Actual Clean** | FP: 16 | TN: 64 |

### Error Analysis

- **False Positive Rate**: 20.00% (16 clean codes wrongly flagged as buggy)
- **False Negative Rate**: 46.25% (37 real bugs missed)

## Per Test Set Performance

| Test Set | Name | Accuracy | Correct | Total |
|----------|------|----------|---------|-------|
| 1 | Basic Bug Patterns | 87.50% | 14 | 16 |
| 2 | Advanced Bug Patterns | 68.75% | 11 | 16 |
| 3 | Real-World Code Scenarios | 68.75% | 11 | 16 |
| 4 | Data Structures & API Usage | 68.75% | 11 | 16 |
| 5 | Complex & Real-World Scenarios | 62.50% | 10 | 16 |
| 6 | Mixed Bugs & Complex Logic | 81.25% | 13 | 16 |
| 7 | Security & Edge Cases | 62.50% | 10 | 16 |
| 8 | OOP & Structural Bugs | 62.50% | 10 | 16 |
| 9 | Regression & Stress Testing | 56.25% | 9 | 16 |
| 10 | Production-Ready Code Patterns | 50.00% | 8 | 16 |

## Key Findings

### Strengths ✅

1. **High Specificity (80%)**: Good at correctly identifying clean code
2. **Decent Precision (72.88%)**: Most detected bugs are real bugs
3. **Best Performance**: Test Set 1 (Basic Bugs) - 87.50% accuracy
4. **Syntax Errors**: Detected reliably

### Weaknesses ⚠️

1. **Low Recall (53.75%)**: Missing 46% of real bugs (37 false negatives)
2. **Corner Cases**: Often not detected (division by zero, empty lists, etc.)
3. **Production Patterns**: Lowest accuracy on Test Set 10 (50%)
4. **False Negatives**: 37 bugs missed across all test sets

### Common False Positives (16 total)

- Lambda functions incorrectly flagged as hallucinated
- Context managers (async/await) flagged as undefined
- Standard library usage (json.loads, logging, etc.) marked as hallucinated
- Generator expressions marked as undefined

### Common False Negatives (37 total)

- Missing corner case checks (empty lists, zero division, None values)
- Subtle logic errors (wrong exponent values, impossible conditions)
- Wrong input types not caught
- Silly mistakes overlooked

## Recommendations

### High Priority 🔴

1. **Improve Corner Case Detection**: Currently missing 46% of bugs
   - Add pattern for division operations without zero checks
   - Detect list/array access without length checks
   - Flag None handling issues

2. **Reduce False Positives on Standard Library**:
   - Expand built-in whitelist to include all Python 3.10+ standard library
   - Better context manager detection (async/await, with statements)
   - Recognize common patterns (lambda, generators, comprehensions)

3. **Enhance Recall**: Focus on catching more real bugs
   - Improve edge case detection
   - Better type checking
   - Logic error detection

### Medium Priority 🟡

4. **Production Code Patterns**: Test Set 10 only 50% accurate
   - Improve security pattern detection
   - Better async/await handling
   - Resource management (file handles, connections)

5. **Complex Scenarios**: Test Sets 7-9 underperforming (56-62%)
   - OOP pattern recognition
   - Advanced data structure usage
   - Security vulnerability detection

## Test Coverage

**Bug Types Tested** (80 buggy code samples):
- Syntax Error
- Hallucinated Object
- Incomplete Generation
- Silly Mistake
- Wrong Attribute
- Wrong Input Type
- Prompt Bias
- NPC (Non-Pertinent Code)
- Missing Corner Case

**Clean Code Samples** (80 samples):
- Standard Python patterns
- Context managers
- List/dict comprehensions
- Lambda functions
- Async/await
- Class definitions
- Exception handling
- Standard library usage

## Comparison with Previous Results

| Metric | Previous (32 cases) | Current (160 cases) | Change |
|--------|---------------------|---------------------|--------|
| Accuracy | 78.12% | 66.88% | ⬇ -11.24% |
| Precision | 80.00% | 72.88% | ⬇ -7.12% |
| Recall | 75.00% | 53.75% | ⬇ -21.25% |
| F1 Score | 77.42% | 61.87% | ⬇ -15.55% |

**Analysis**: Performance decreased with broader test coverage. The expanded test suite (5× more cases) exposed weaknesses in:
- Corner case detection
- Production-ready code analysis
- Complex scenario handling

## Files Generated

1. **test_sets/test_set_1.json through test_set_10.json**: Test data (160 cases)
2. **results/test_set_1_results.json through test_set_10_results.json**: Individual test results
3. **results/final_metrics_report.json**: Comprehensive metrics report

## How to Re-run Tests

```bash
# Run all 160 test cases
python backend/app/final_test/run_all_tests.py

# Calculate detailed metrics
python backend/app/final_test/calculate_metrics.py
```

## Next Steps

1. ✅ **Refactored test suite to JSON format** - Complete
2. ✅ **Added 10th test set** - Complete  
3. ✅ **Created unified test runner** - Complete
4. 🔄 **Fix False Positives**: Update hallucination detector to whitelist standard library
5. 🔄 **Improve Corner Case Detection**: Add specific patterns for common edge cases
6. 🔄 **Enhance Test Coverage**: Add more production-quality code examples
7. 🔄 **Tune Detectors**: Balance precision vs recall based on use case
