"""
Unified Test Runner for All Test Sets - HTTP API
==================================================
Tests all test sets through HTTP API to simulate VSCode extension behavior.
The extension will communicate with backend deployed on Render via HTTP.

Binary Classification:
- Any bugs detected = "bug"
- No bugs detected = "clean"
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

# API endpoint (configure for local or Render deployment)
API_URL = "http://localhost:8000/api/analyze"
REQUEST_TIMEOUT = 120  # seconds


def load_test_sets(test_sets_dir):
    """Load all JSON test set files from the test_sets directory."""
    test_sets = []
    test_sets_path = Path(test_sets_dir)
    
    # Load test sets 1-10 in order
    for i in range(1, 11):
        json_file = test_sets_path / f"test_set_{i}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                test_set = json.load(f)
                test_sets.append(test_set)
                print(f"[OK] Loaded test_set_{i}.json ({len(test_set['test_cases'])} cases)")
        else:
            print(f"[SKIP] Missing test_set_{i}.json")
    
    return test_sets


def analyze_test_case_http(test_case):
    """
    Analyze a single test case via HTTP API.
    This simulates how the VSCode extension will work.
    
    Binary Classification:
    - If any bugs detected -> "bug"
    - If no bugs detected -> "clean"
    """
    try:
        # Prepare API request (same format as VSCode extension)
        payload = {
            "prompt": test_case['prompt'],
            "code": test_case['code']
        }
        
        # Send HTTP POST request
        response = requests.post(
            API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            return {
                "predicted": "error",
                "bugs_found": [],
                "bug_count": 0,
                "severity_score": 0,
                "error": f"HTTP {response.status_code}: {response.text[:100]}"
            }
        
        # Parse API response
        data = response.json()
        
        # Extract bug patterns from response
        bug_patterns = data.get('bug_patterns', [])
        has_bugs = data.get('has_bugs', False)
        overall_severity = data.get('overall_severity', 0)
        
        # Binary classification - FIXED: "No Bugs Detected" should be classified as "clean"
        # Check if there are real bugs (not just "No Bugs Detected" placeholder)
        real_bugs = [bug for bug in bug_patterns if bug.get('pattern_name') != 'No Bugs Detected']
        predicted = "bug" if (has_bugs or len(real_bugs) > 0 or overall_severity > 0) else "clean"
        
        return {
            "predicted": predicted,
            "bugs_found": bug_patterns,
            "bug_count": len(bug_patterns),
            "severity_score": overall_severity,
            "analysis_id": data.get('analysis_id'),
            "summary": data.get('summary', '')
        }
        
    except requests.exceptions.Timeout:
        return {
            "predicted": "error",
            "bugs_found": [],
            "bug_count": 0,
            "severity_score": 0,
            "error": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "predicted": "error",
            "bugs_found": [],
            "bug_count": 0,
            "severity_score": 0,
            "error": "Cannot connect to server. Is it running?"
        }
    except Exception as e:
        return {
            "predicted": "error",
            "bugs_found": [],
            "bug_count": 0,
            "severity_score": 0,
            "error": str(e)
        }


def run_test_set(test_set, results_dir):
    """Run all test cases in a test set via HTTP API and save results."""
    test_set_id = test_set['test_set_id']
    test_set_name = test_set['name']
    test_cases = test_set['test_cases']
    
    print(f"\n{'='*70}")
    print(f"Running Test Set {test_set_id}: {test_set_name}")
    print(f"{'='*70}")
    
    results = []
    correct = 0
    errors = 0
    total = len(test_cases)
    total_time = 0
    
    for i, test_case in enumerate(test_cases, 1):
        case_start = time.time()
        
        print(f"\n[{i}/{total}] {test_case['name']}")
        print(f"  Expected: {test_case['expected']}")
        
        # Analyze via HTTP API
        analysis = analyze_test_case_http(test_case)
        predicted = analysis['predicted']
        case_time = time.time() - case_start
        total_time += case_time
        
        # Check for errors
        if predicted == "error":
            errors += 1
            print(f"  [ERROR] {analysis.get('error', 'Unknown error')}")
            
            result = {
                "test_case_id": test_case['id'],
                "name": test_case['name'],
                "expected": test_case['expected'],
                "predicted": "error",
                "correct": False,
                "error": analysis.get('error'),
                "execution_time": case_time
            }
            results.append(result)
            continue
        
        # Check if prediction is correct
        is_correct = (predicted == test_case['expected'])
        if is_correct:
            correct += 1
        
        # Store result
        result = {
            "test_case_id": test_case['id'],
            "name": test_case['name'],
            "expected": test_case['expected'],
            "predicted": predicted,
            "correct": is_correct,
            "bug_count": analysis['bug_count'],
            "bugs_found": [
                {
                    "pattern_name": bug.get('pattern_name', 'unknown'),
                    "severity": bug.get('severity', 0),
                    "description": bug.get('description', '')[:100]
                } for bug in analysis['bugs_found']
            ],
            "severity_score": analysis['severity_score'],
            "expected_bug_type": test_case.get('bug_type'),
            "execution_time": case_time,
            "analysis_id": analysis.get('analysis_id')
        }
        results.append(result)
        
        # Print result
        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"  Predicted: {predicted} {status}")
        print(f"  Severity: {analysis['severity_score']}/10")
        print(f"  Execution time: {case_time:.2f}s")
    
    # Save results to JSON file
    results_file = results_dir / f"test_set_{test_set_id}_results.json"
    test_result_summary = {
        "test_set_id": test_set_id,
        "name": test_set_name,
        "total_cases": total,
        "correct": correct,
        "errors": errors,
        "accuracy": (correct / (total - errors) * 100) if (total - errors) > 0 else 0,
        "total_execution_time": total_time,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(results_file, 'w') as f:
        json.dump(test_result_summary, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Test Set {test_set_id} Complete")
    print(f"Correct: {correct}/{total - errors} ({test_result_summary['accuracy']:.2f}%)")
    print(f"Errors: {errors}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Results saved to: {results_file.name}")
    print(f"{'='*70}")
    
    return test_result_summary


def check_server_availability():
    """Check if backend server is running."""
    try:
        # Try to ping the root endpoint
        base_url = API_URL.rsplit('/', 1)[0]
        response = requests.get(base_url, timeout=5)
        return True
    except:
        return False
    
    print(f"\n{'='*70}")
    print(f"Running Test Set {test_set_id}: {test_set_name}")
    print(f"{'='*70}")
    
    results = []
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{total}: {test_case['name']}")
        print(f"  Expected: {test_case['expected']}")
        
        # Analyze the test case
        analysis = analyze_test_case(test_case)
        predicted = analysis['predicted']
        
        # Check if prediction is correct
        is_correct = (predicted == test_case['expected'])
        if is_correct:
            correct += 1
        
        # Store result
        result = {
            "test_case_id": test_case['id'],
            "name": test_case['name'],
            "expected": test_case['expected'],
            "predicted": predicted,
            "correct": is_correct,
            "bug_count": analysis['bug_count'],
            "bugs_found": analysis['bugs_found'],
            "severity_score": analysis['severity_score'],
            "expected_bug_type": test_case.get('bug_type'),
            "prompt": test_case['prompt']
        }
        results.append(result)
        
        # Print result
        status = "✓ CORRECT" if is_correct else "✗ WRONG"
        print(f"  Predicted: {predicted} - {status}")
        if analysis['bug_count'] > 0:
            print(f"  Bugs detected: {analysis['bug_count']}")
            for bug in analysis['bugs_found']:
                print(f"    - {bug.get('type', 'unknown')}: {bug.get('description', 'N/A')}")
    
    # Calculate accuracy for this test set
    accuracy = (correct / total) * 100
    print(f"\n{'-'*70}")
    print(f"Test Set {test_set_id} Results: {correct}/{total} correct ({accuracy:.2f}% accuracy)")
    print(f"{'-'*70}")
    
    # Save results to JSON
    results_data = {
        "test_set_id": test_set_id,
        "test_set_name": test_set_name,
        "total_cases": total,
        "correct": correct,
        "accuracy": accuracy,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    results_file = Path(results_dir) / f"test_set_{test_set_id}_results.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"Results saved to: {results_file}")
    
    return results_data


def main():
    """Main entry point to run all test sets via HTTP API."""
    # Setup paths
    script_dir = Path(__file__).parent
    test_sets_dir = script_dir / "test_sets"
    results_dir = script_dir / "results"
    
    # Create results directory if it doesn't exist
    results_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print(" HTTP API TEST RUNNER - PRODUCTION SIMULATION")
    print("="*70)
    print(f"API Endpoint: {API_URL}")
    print(f"Test sets directory: {test_sets_dir}")
    print(f"Results directory: {results_dir}")
    print()
    print("This test simulates how the VSCode extension will work:")
    print("  1. Extension sends HTTP POST to backend")
    print("  2. Backend runs 3-stage analysis (Static/Dynamic/Linguistic)")
    print("  3. Backend returns bug patterns and severity")
    print("="*70)
    
    # Check server availability
    print("\nChecking server availability...")
    if not check_server_availability():
        print("[ERROR] Backend server is not running!")
        print("")
        print("Please start the server first:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        print("")
        return
    
    print("[OK] Server is running")
    
    # Load all test sets
    test_sets = load_test_sets(test_sets_dir)
    
    if not test_sets:
        print("\n[ERROR] No test sets found!")
        return
    
    print(f"\nTotal test sets loaded: {len(test_sets)}")
    total_test_cases = sum(len(ts['test_cases']) for ts in test_sets)
    print(f"Total test cases: {total_test_cases}")
    print(f"Estimated time: {total_test_cases * 30 / 60:.1f} - {total_test_cases * 60 / 60:.1f} minutes")
    print("  (depends on LLM API speed: ~30-60s per test)")
    
    # Run all test sets
    all_results = []
    total_start_time = time.time()
    
    for test_set in test_sets:
        result = run_test_set(test_set, results_dir)
        all_results.append(result)
    
    total_elapsed = time.time() - total_start_time
    
    # Print summary
    print("\n" + "="*70)
    print(" OVERALL SUMMARY")
    print("="*70)
    
    total_correct = sum(r['correct'] for r in all_results)
    total_errors = sum(r.get('errors', 0) for r in all_results)
    valid_cases = total_test_cases - total_errors
    overall_accuracy = (total_correct / valid_cases * 100) if valid_cases > 0 else 0
    
    print(f"\nTest Results:")
    print(f"  Total Cases: {total_test_cases}")
    print(f"  Correct: {total_correct}")
    print(f"  Errors: {total_errors}")
    print(f"  Overall Accuracy: {overall_accuracy:.2f}%")
    print(f"  Total Time: {total_elapsed:.2f}s ({total_elapsed/60:.1f} minutes)")
    print(f"  Avg Time/Test: {total_elapsed/total_test_cases:.2f}s")
    
    print("\nPer Test Set Results:")
    for result in all_results:
        valid = result['total_cases'] - result.get('errors', 0)
        print(f"  Test Set {result['test_set_id']:2d}: {result['accuracy']:6.2f}% "
              f"({result['correct']}/{valid}) - {result['total_execution_time']:.1f}s")
    
    print("\n" + "="*70)
    print("All tests completed!")
    print(f"Results saved to: {results_dir}")
    print("")
    print("Next step: Run calculate_metrics.py for detailed analysis")
    print("="*70)


if __name__ == "__main__":
    main()
