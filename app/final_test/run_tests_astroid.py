"""
Astroid Migration - Full Test Runner (Render HTTP API)
======================================================
Runs all 10 test sets against the Render-deployed backend
and saves results to result_astroid/ folder.

Mirrors run_all_tests.py but:
  - Targets the Render production URL
  - Saves to result_astroid/ instead of results/
  - Calculates metrics inline and saves final_metrics_report.json
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# ---- CONFIGURATION --------------------------------------------------------
API_URL = "https://codeguard-backend-g7ka.onrender.com/api/analyze"
REQUEST_TIMEOUT = 120  # seconds (Render free tier can be slow to wake)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
TEST_SETS_DIR = SCRIPT_DIR / "test_sets"
RESULTS_DIR = SCRIPT_DIR / "result_astroid"


# ===========================================================================
# HTTP Analysis
# ===========================================================================

def analyze_test_case_http(test_case):
    """Send one test case to the Render backend and return prediction."""
    try:
        payload = {
            "prompt": test_case["prompt"],
            "code": test_case["code"],
        }
        response = requests.post(
            API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            return {
                "predicted": "error",
                "bugs_found": [],
                "bug_count": 0,
                "severity_score": 0,
                "error": f"HTTP {response.status_code}: {response.text[:120]}",
            }

        data = response.json()
        bug_patterns = data.get("bug_patterns", [])
        has_bugs = data.get("has_bugs", False)
        overall_severity = data.get("overall_severity", 0)

        real_bugs = [b for b in bug_patterns if b.get("pattern_name") != "No Bugs Detected"]
        predicted = "bug" if (has_bugs or len(real_bugs) > 0 or overall_severity > 0) else "clean"

        return {
            "predicted": predicted,
            "bugs_found": bug_patterns,
            "bug_count": len(bug_patterns),
            "severity_score": overall_severity,
            "analysis_id": data.get("analysis_id"),
            "summary": data.get("summary", ""),
        }

    except requests.exceptions.Timeout:
        return {"predicted": "error", "bugs_found": [], "bug_count": 0, "severity_score": 0, "error": "Request timeout"}
    except requests.exceptions.ConnectionError as exc:
        return {"predicted": "error", "bugs_found": [], "bug_count": 0, "severity_score": 0, "error": f"Connection error: {exc}"}
    except Exception as exc:
        return {"predicted": "error", "bugs_found": [], "bug_count": 0, "severity_score": 0, "error": str(exc)}


# ===========================================================================
# Test set runner
# ===========================================================================

def run_test_set(test_set, results_dir: Path):
    ts_id = test_set["test_set_id"]
    ts_name = test_set["name"]
    test_cases = test_set["test_cases"]
    total = len(test_cases)

    print(f"\n{'='*70}")
    print(f"Test Set {ts_id}: {ts_name}")
    print(f"{'='*70}")

    results = []
    correct = 0
    errors = 0
    total_time = 0.0

    for i, tc in enumerate(test_cases, 1):
        t0 = time.time()
        print(f"\n  [{i}/{total}] {tc['name']}")
        print(f"    Expected: {tc['expected']}")

        analysis = analyze_test_case_http(tc)
        predicted = analysis["predicted"]
        elapsed = time.time() - t0
        total_time += elapsed

        if predicted == "error":
            errors += 1
            print(f"    [ERROR] {analysis.get('error', '')}")
            results.append({
                "test_case_id": tc["id"],
                "name": tc["name"],
                "expected": tc["expected"],
                "predicted": "error",
                "correct": False,
                "error": analysis.get("error"),
                "execution_time": elapsed,
            })
            continue

        is_correct = predicted == tc["expected"]
        if is_correct:
            correct += 1

        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"    Predicted: {predicted} {status}  |  severity={analysis['severity_score']}  |  {elapsed:.1f}s")

        results.append({
            "test_case_id": tc["id"],
            "name": tc["name"],
            "expected": tc["expected"],
            "predicted": predicted,
            "correct": is_correct,
            "bug_count": analysis["bug_count"],
            "bugs_found": [
                {
                    "pattern_name": b.get("pattern_name", "unknown"),
                    "severity": b.get("severity", 0),
                    "description": b.get("description", "")[:100],
                }
                for b in analysis["bugs_found"]
            ],
            "severity_score": analysis["severity_score"],
            "expected_bug_type": tc.get("bug_type"),
            "execution_time": elapsed,
            "analysis_id": analysis.get("analysis_id"),
        })

    valid = total - errors
    accuracy = (correct / valid * 100) if valid > 0 else 0.0

    summary = {
        "test_set_id": ts_id,
        "name": ts_name,
        "total_cases": total,
        "correct": correct,
        "errors": errors,
        "accuracy": accuracy,
        "total_execution_time": total_time,
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }

    out_file = results_dir / f"test_set_{ts_id}_results.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Accuracy: {correct}/{valid} = {accuracy:.2f}%  |  errors={errors}  |  time={total_time:.1f}s")
    print(f"  Saved -> {out_file.name}")
    return summary


# ===========================================================================
# Metrics calculation (inline copy of calculate_metrics.py logic)
# ===========================================================================

def calculate_metrics(all_results):
    tp = tn = fp = fn = 0
    total_cases = 0
    total_correct = 0

    for rs in all_results:
        for r in rs["results"]:
            exp = r["expected"]
            pred = r["predicted"]
            if exp == "bug" and pred == "bug":
                tp += 1
            elif exp == "clean" and pred == "clean":
                tn += 1
            elif exp == "clean" and pred == "bug":
                fp += 1
            elif exp == "bug" and pred == "clean":
                fn += 1

        total_cases += rs["total_cases"]
        total_correct += rs["correct"]

    accuracy  = total_correct / total_cases if total_cases else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    specificity = tn / (tn + fp) if (tn + fp) else 0
    fpr       = fp / (fp + tn) if (fp + tn) else 0
    fnr       = fn / (fn + tp) if (fn + tp) else 0

    return {
        "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
        "total_cases": total_cases,
        "correct_predictions": total_correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "specificity": specificity,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "timestamp": datetime.now().isoformat(),
    }


def save_final_report(metrics, all_results, results_dir: Path):
    report = {
        "metrics": metrics,
        "test_sets": [
            {
                "test_set_id": rs["test_set_id"],
                "test_set_name": rs.get("name", "Unknown"),
                "total_cases": rs["total_cases"],
                "correct": rs["correct"],
                "accuracy": rs["accuracy"],
            }
            for rs in all_results
        ],
    }
    out = results_dir / "final_metrics_report.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Metrics report saved -> {out}")
    return report


def print_metrics(metrics):
    cm = metrics["confusion_matrix"]
    print("\n" + "="*70)
    print("  METRICS SUMMARY (astroid migration)")
    print("="*70)
    print(f"\n  Confusion Matrix:")
    print(f"    TP={cm['TP']}  FP={cm['FP']}  TN={cm['TN']}  FN={cm['FN']}")
    print(f"\n  Accuracy:    {metrics['accuracy']:.2%}")
    print(f"  Precision:   {metrics['precision']:.2%}")
    print(f"  Recall:      {metrics['recall']:.2%}")
    print(f"  F1 Score:    {metrics['f1_score']:.2%}")
    print(f"  Specificity: {metrics['specificity']:.2%}")
    print(f"  FPR:         {metrics['false_positive_rate']:.2%}")
    print(f"  FNR:         {metrics['false_negative_rate']:.2%}")
    print("="*70)


# ===========================================================================
# Main
# ===========================================================================

def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("="*70)
    print("  ASTROID MIGRATION - FULL TEST RUN (Render API)")
    print("="*70)
    print(f"  API_URL   : {API_URL}")
    print(f"  Test sets : {TEST_SETS_DIR}")
    print(f"  Output    : {RESULTS_DIR}")
    print("="*70)

    # Ping server
    print("\nChecking server availability...")
    try:
        base_url = API_URL.rsplit("/", 2)[0]  # strip /api/analyze -> hostname
        resp = requests.get(base_url, timeout=30)
        print(f"  [OK] Server responded with status {resp.status_code}")
    except Exception as exc:
        print(f"  [WARN] Ping failed ({exc}) — will attempt tests anyway.")

    # Load test sets
    test_sets = []
    for i in range(1, 11):
        f = TEST_SETS_DIR / f"test_set_{i}.json"
        if f.exists():
            with open(f) as fh:
                ts = json.load(fh)
                test_sets.append(ts)
                print(f"  [OK] Loaded test_set_{i}.json ({len(ts['test_cases'])} cases)")
        else:
            print(f"  [SKIP] Missing test_set_{i}.json")

    if not test_sets:
        print("\n[ERROR] No test sets found!")
        return

    total_cases = sum(len(ts["test_cases"]) for ts in test_sets)
    print(f"\n  Total test sets: {len(test_sets)}")
    print(f"  Total test cases: {total_cases}")
    est_min_lo = total_cases * 10 / 60
    est_min_hi = total_cases * 30 / 60
    print(f"  Estimated time: {est_min_lo:.0f}–{est_min_hi:.0f} minutes\n")

    # Run all test sets
    all_results = []
    wall_t0 = time.time()

    for ts in test_sets:
        result = run_test_set(ts, RESULTS_DIR)
        all_results.append(result)

    wall_elapsed = time.time() - wall_t0

    # Aggregate summary
    total_correct = sum(r["correct"] for r in all_results)
    total_errors  = sum(r.get("errors", 0) for r in all_results)
    valid_cases   = total_cases - total_errors
    overall_acc   = total_correct / valid_cases * 100 if valid_cases else 0

    print("\n" + "="*70)
    print("  OVERALL SUMMARY")
    print("="*70)
    print(f"  Total Cases : {total_cases}")
    print(f"  Correct     : {total_correct}")
    print(f"  Errors      : {total_errors}")
    print(f"  Accuracy    : {overall_acc:.2f}%")
    print(f"  Wall time   : {wall_elapsed:.1f}s ({wall_elapsed/60:.1f} min)")
    print()
    for r in all_results:
        valid = r["total_cases"] - r.get("errors", 0)
        print(f"  Set {r['test_set_id']:2d}: {r['accuracy']:6.2f}%  ({r['correct']}/{valid})  — {r['name']}")

    # Metrics
    metrics = calculate_metrics(all_results)
    print_metrics(metrics)
    save_final_report(metrics, all_results, RESULTS_DIR)

    print("\nDone! Results in:", RESULTS_DIR)


if __name__ == "__main__":
    main()
