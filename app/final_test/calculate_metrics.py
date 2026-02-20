"""
Metrics Calculator for Final Test Results
==========================================
Calculates Accuracy, Precision, Recall, F1 Score, and other metrics
from the test results saved by run_all_tests.py
"""

import json
import os
from pathlib import Path
from datetime import datetime


def load_results(results_dir="F:/Codeguard/backend/app/final_test/results"):
    """Load all test results from JSON files (test_set_1 through test_set_10)."""
    results = []
    
    for i in range(1, 11):
        filename = f'test_set_{i}_results.json'
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                results.append(data)
                print(f"  [OK] Loaded {filename}")
        else:
            print(f"  [WARNING] {filepath} not found")
    
    return results


def calculate_metrics(all_results):
    """Calculate comprehensive metrics from test results."""
    # Aggregate confusion matrix
    total_tp = 0
    total_tn = 0
    total_fp = 0
    total_fn = 0
    total_cases = 0
    total_correct = 0
    
    # Process each test set's results
    for result_set in all_results:
        # Calculate confusion matrix from individual results
        for test_result in result_set['results']:
            expected = test_result['expected']
            predicted = test_result['predicted']
            
            if expected == "bug" and predicted == "bug":
                total_tp += 1
            elif expected == "clean" and predicted == "clean":
                total_tn += 1
            elif expected == "clean" and predicted == "bug":
                total_fp += 1
            elif expected == "bug" and predicted == "clean":
                total_fn += 1
        
        total_cases += result_set['total_cases']
        total_correct += result_set['correct']
    
    # Calculate metrics
    accuracy = total_correct / total_cases if total_cases > 0 else 0
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    specificity = total_tn / (total_tn + total_fp) if (total_tn + total_fp) > 0 else 0
    
    # False Positive Rate
    fpr = total_fp / (total_fp + total_tn) if (total_fp + total_tn) > 0 else 0
    
    # False Negative Rate
    fnr = total_fn / (total_fn + total_tp) if (total_fn + total_tp) > 0 else 0
    
    metrics = {
        "confusion_matrix": {
            "TP": total_tp,
            "TN": total_tn,
            "FP": total_fp,
            "FN": total_fn
        },
        "total_cases": total_cases,
        "correct_predictions": total_correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "specificity": specificity,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "timestamp": datetime.now().isoformat()
    }
    
    return metrics


def print_metrics_report(metrics, all_results):
    """Print a comprehensive metrics report."""
    print("\n" + "=" * 80)
    print("  FINAL TEST METRICS REPORT")
    print("=" * 80)
    
    print(f"\nOVERALL RESULTS:")
    print(f"  Total Test Cases: {metrics['total_cases']}")
    print(f"  Correct Predictions: {metrics['correct_predictions']}")
    
    print(f"\nCONFUSION MATRIX:")
    print(f"  ┌─────────────────┬─────────────┬─────────────┐")
    print(f"  │                 │  Predicted  │  Predicted  │")
    print(f"  │                 │     Bug     │    Clean    │")
    print(f"  ├─────────────────┼─────────────┼─────────────┤")
    print(f"  │  Actual Bug     │  TP: {metrics['confusion_matrix']['TP']:5d}  │  FN: {metrics['confusion_matrix']['FN']:5d}  │")
    print(f"  │  Actual Clean   │  FP: {metrics['confusion_matrix']['FP']:5d}  │  TN: {metrics['confusion_matrix']['TN']:5d}  │")
    print(f"  └─────────────────┴─────────────┴─────────────┘")
    
    print(f"\nPERFORMANCE METRICS:")
    print(f"  Accuracy:           {metrics['accuracy']:.2%}  (Correct predictions / Total)")
    print(f"  Precision:          {metrics['precision']:.2%}  (TP / (TP + FP))")
    print(f"  Recall (Sensitivity): {metrics['recall']:.2%}  (TP / (TP + FN))")
    print(f"  F1 Score:           {metrics['f1_score']:.2%}  (Harmonic mean of Precision & Recall)")
    print(f"  Specificity:        {metrics['specificity']:.2%}  (TN / (TN + FP))")
    
    print(f"\n  ERROR RATES:")
    print(f"  False Positive Rate: {metrics['false_positive_rate']:.2%}  (FP / (FP + TN))")
    print(f"  False Negative Rate: {metrics['false_negative_rate']:.2%}  (FN / (FN + TP))")
    
    print(f"\n TEST SET BREAKDOWN:")
    for result_set in all_results:
        test_set_id = result_set['test_set_id']
        test_set_name = result_set.get('name', result_set.get('test_set_name', 'Unknown'))
        print(f"\n  Test Set {test_set_id} ({test_set_name}):")
        print(f"    Cases: {result_set['total_cases']}")
        print(f"    Accuracy: {result_set['accuracy']:.2f}%")
        print(f"    Correct: {result_set['correct']}/{result_set['total_cases']}")
    
    print(f"\n INTERPRETATION:")
    
    if metrics['accuracy'] >= 0.90:
        print(f"   Excellent accuracy ({metrics['accuracy']:.2%})! System performs very well.")
    elif metrics['accuracy'] >= 0.75:
        print(f"    Good accuracy ({metrics['accuracy']:.2%}), but room for improvement.")
    else:
        print(f"   Low accuracy ({metrics['accuracy']:.2%}). System needs significant improvement.")
    
    if metrics['precision'] >= 0.85:
        print(f"   High precision ({metrics['precision']:.2%}) - Few false positives.")
    else:
        print(f"    Precision {metrics['precision']:.2%} - Consider reducing false positives.")
    
    if metrics['recall'] >= 0.85:
        print(f"   High recall ({metrics['recall']:.2%}) - Catching most bugs.")
    else:
        print(f"    Recall {metrics['recall']:.2%} - Missing some bugs.")
    
    if metrics['f1_score'] >= 0.85:
        print(f"   Excellent F1 Score ({metrics['f1_score']:.2%}) - Balanced performance.")
    else:
        print(f"    F1 Score {metrics['f1_score']:.2%} - Precision/Recall tradeoff needed.")
    
    print("\n" + "=" * 80)


def save_metrics_report(metrics, all_results, output_dir="F:/Codeguard/backend/app/final_test/results"):
    """Save metrics report to JSON file."""
    # Create test set summaries
    test_set_summaries = []
    for result in all_results:
        summary = {
            "test_set_id": result['test_set_id'],
            "test_set_name": result.get('name', result.get('test_set_name', 'Unknown')),
            "total_cases": result['total_cases'],
            "correct": result['correct'],
            "accuracy": result['accuracy']
        }
        test_set_summaries.append(summary)
    
    report = {
        "metrics": metrics,
        "test_sets": test_set_summaries
    }
    
    output_file = os.path.join(output_dir, "final_metrics_report.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n Metrics report saved to: {output_file}")
    
    return output_file


def main():
    """Main function to calculate and display metrics."""
    print("=" * 80)
    print("  LOADING TEST RESULTS")
    print("=" * 80)
    
    results_dir = "F:/Codeguard/backend/app/final_test/results"
    all_results = load_results(results_dir)
    
    if not all_results:
        print("\n No test results found!")
        print("   Please run run_all_tests.py first.")
        return
    
    print(f"\n Loaded {len(all_results)} test result file(s)")
    
    # Calculate metrics
    metrics = calculate_metrics(all_results)
    
    # Print report
    print_metrics_report(metrics, all_results)
    
    # Save report
    save_metrics_report(metrics, all_results, results_dir)
    
    return metrics


if __name__ == "__main__":
    main()
