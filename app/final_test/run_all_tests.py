"""
Unified Test Runner for All Test Sets
======================================
Loads all JSON test sets, runs static analysis on each test case,
and saves results for metrics calculation.

Binary Classification:
- Any bugs detected = "bug"
- No bugs detected = "clean"
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'F:/Codeguard/backend')

from app.analyzers.static_analyzer import StaticAnalyzer


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
                print(f"✓ Loaded test_set_{i}.json ({len(test_set['test_cases'])} cases)")
        else:
            print(f"✗ Missing test_set_{i}.json")
    
    return test_sets


def analyze_test_case(test_case):
    """
    Analyze a single test case using static analyzer.
    
    Binary Classification:
    - If any bugs detected -> "bug"
    - If no bugs detected -> "clean"
    """
    # Run static analysis
    code = test_case['code']
    
    analyzer = StaticAnalyzer(code)
    result = analyzer.analyze()
    
    # Check if any bugs were found
    bugs_found = []
    for pattern, res in result.items():
        if res.get('found', False):
            bugs_found.append({
                "type": pattern,
                "description": res.get('message', 'Bug detected')
            })
    
    # Binary classification
    has_bugs = len(bugs_found) > 0
    predicted = "bug" if has_bugs else "clean"
    
    return {
        "predicted": predicted,
        "bugs_found": bugs_found,
        "bug_count": len(bugs_found),
        "severity_score": len(bugs_found)  # Simple severity: count of bugs
    }


def run_test_set(test_set, results_dir):
    """Run all test cases in a test set and save results."""
    test_set_id = test_set['test_set_id']
    test_set_name = test_set['name']
    test_cases = test_set['test_cases']
    
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
    """Main entry point to run all test sets."""
    # Setup paths
    script_dir = Path(__file__).parent
    test_sets_dir = script_dir / "test_sets"
    results_dir = script_dir / "results"
    
    # Create results directory if it doesn't exist
    results_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print(" UNIFIED TEST RUNNER - ALL TEST SETS")
    print("="*70)
    print(f"Test sets directory: {test_sets_dir}")
    print(f"Results directory: {results_dir}")
    print()
    
    # Load all test sets
    test_sets = load_test_sets(test_sets_dir)
    
    if not test_sets:
        print("ERROR: No test sets found!")
        return
    
    print(f"\nTotal test sets loaded: {len(test_sets)}")
    total_test_cases = sum(len(ts['test_cases']) for ts in test_sets)
    print(f"Total test cases: {total_test_cases}")
    
    # Run all test sets
    all_results = []
    for test_set in test_sets:
        result = run_test_set(test_set, results_dir)
        all_results.append(result)
    
    # Print summary
    print("\n" + "="*70)
    print(" OVERALL SUMMARY")
    print("="*70)
    
    total_correct = sum(r['correct'] for r in all_results)
    overall_accuracy = (total_correct / total_test_cases) * 100
    
    print(f"\nTotal Test Cases: {total_test_cases}")
    print(f"Correct Predictions: {total_correct}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    
    print("\nPer Test Set Accuracy:")
    for result in all_results:
        print(f"  Test Set {result['test_set_id']:2d}: {result['accuracy']:6.2f}% ({result['correct']}/{result['total_cases']})")
    
    print("\n" + "="*70)
    print("All tests completed! Run calculate_metrics.py to get detailed metrics.")
    print("="*70)


if __name__ == "__main__":
    main()
