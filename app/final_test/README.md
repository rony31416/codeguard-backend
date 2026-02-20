# Final Test Suite - HTTP API Testing

This folder contains comprehensive test cases for the CodeGuard bug detection system using HTTP API testing to simulate the VSCode extension behavior.

## Important: HTTP Testing Approach

This test suite uses **HTTP POST requests** to test the backend API, simulating how the VSCode extension will communicate with the backend deployed on Render.

**Why HTTP Testing?**
- Simulates real production workflow (VSCode extension → Render deployment)
- Tests the complete API stack (FastAPI → 3-stage analysis → Response)
- Matches actual user experience

## Structure

### Test Sets (JSON Format)
- **test_sets/test_set_1.json**: Basic syntax errors and simple bugs (16 cases)
- **test_sets/test_set_2.json**: Attribute errors and type issues (16 cases)
- **test_sets/test_set_3.json**: Real-world code scenarios (16 cases)
- **test_sets/test_set_4.json**: Data structures & API usage (16 cases)
- **test_sets/test_set_5.json**: Complex & real-world scenarios (16 cases)
- **test_sets/test_set_6.json**: Advanced patterns (16 cases)
- **test_sets/test_set_7.json**: Edge cases (16 cases)
- **test_sets/test_set_8.json**: Library usage (16 cases)
- **test_sets/test_set_9.json**: Advanced topics (16 cases)
- **test_sets/test_set_10.json**: Production-ready code patterns (16 cases)

### Test Runner & Metrics
- **run_all_tests.py**: HTTP API test runner for all test sets
- **calculate_metrics.py**: Calculates Accuracy, Precision, Recall, F1 Score
- **results/**: JSON files with test results and metrics

## Running Tests

### Prerequisites
**IMPORTANT**: The backend server MUST be running before testing!

```bash
# Terminal 1: Start the backend server
cd backend
uvicorn app.main:app --reload
```

### Run All Tests via HTTP (Recommended)
```bash
# Terminal 2: Run tests
cd backend
python app/final_test/run_all_tests.py
```

This will:
- Check if backend server is running
- Send HTTP POST requests to http://localhost:8000/api/analyze
- Test all 10 test sets (160 test cases total)
- Save results to `results/test_set_N_results.json`
- Display per-test-set and overall accuracy
- **Time:** ~80-160 minutes (30-60s per test with LLM API)

### Calculate Detailed Metrics
```bash
python app/final_test/calculate_metrics.py
```

This will:
- Load all test results from the results/ folder
- Calculate confusion matrix (TP, TN, FP, FN)
- Compute comprehensive metrics
- Display detailed report

## API Endpoint Configuration

By default, tests use: `http://localhost:8000/api/analyze`

To test against a deployed Render instance, edit `run_all_tests.py`:
```python
API_URL = "https://your-app.onrender.com/api/analyze"
```

## Adding New Test Sets

To add a new test set:

1. Create a JSON file in `test_sets/` directory:
```json
{
  "test_set_id": 11,
  "name": "Your Test Set Name",
  "description": "What this test set covers",
  "total_cases": 16,
  "test_cases": [
    {
      "id": 161,
      "name": "Test case description",
      "expected": "bug",
      "bug_type": "syntax_error",
      "prompt": "Write a function to...",
      "code": "def my_func():\n    pass"
    }
  ]
}
```

2. Run `run_all_tests.py` - it will automatically detect and run the new test set

## Metrics Explained

- **Accuracy**: (TP + TN) / Total - Overall correctness
- **Precision**: TP / (TP + FP) - How many detected bugs are real (low false positives)
- **Recall**: TP / (TP + FN) - How many real bugs are caught (low false negatives)
- **F1 Score**: Harmonic mean of Precision & Recall (balanced performance)
- **Specificity**: TN / (TN + FP) - Correctly identifying clean code

## Binary Classification

The system uses binary classification:
- **"bug"**: Any bugs detected (even if multiple bug types)
- **"clean"**: No bugs detected

## Test Coverage

**Total: 160 test cases (10 sets × 16 cases each)**
- Buggy code samples: 80
- Clean code samples: 80

**Bug Types Tested:**
1. Syntax Error
2. Hallucinated Object
3. Incomplete Generation
4. Silly Mistake
5. Wrong Attribute
6. Wrong Input Type
7. Prompt Bias
8. NPC (Non-Pertinent Code)
9. Missing Corner Case

## Results Format

Each test result JSON contains:
```json
{
  "test_set_id": 1,
  "test_set_name": "...",
  "total_cases": 16,
  "correct": 12,
  "accuracy": 75.0,
  "timestamp": "2024-02-20T...",
  "results": [
    {
      "test_case_id": 1,
      "name": "...",
      "expected": "bug",
      "predicted": "bug",
      "correct": true,
      "bug_count": 1,
      "bugs_found": [...]
    }
  ]
}
```
