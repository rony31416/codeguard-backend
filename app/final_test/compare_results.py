"""
compare_results.py
==================
Compares results/ (pre-fix baseline) vs result_astroid/ (post-fix, with
working Docker dynamic execution) and writes DYNAMIC_FIX_RESULTS.md.

Usage:
    python compare_results.py
"""

import json
from pathlib import Path
from datetime import datetime

SCRIPT_DIR   = Path(__file__).parent
BASELINE_DIR = SCRIPT_DIR / "results"          # pre-fix (pre-astroid baseline)
NEW_DIR      = SCRIPT_DIR / "result_astroid"   # post-fix (Docker dynamic fixed)
OUTPUT_MD    = SCRIPT_DIR / "DYNAMIC_FIX_RESULTS.md"

SET_NAMES = {
    1: "Basic Bug Patterns",
    2: "Advanced Bug Patterns",
    3: "Real-World Code Scenarios",
    4: "Data Structures & API Usage",
    5: "Complex & Real-World Scenarios",
    6: "Mixed Bugs & Complex Logic",
    7: "Security & Edge Cases",
    8: "OOP & Structural Bugs",
    9: "Regression & Stress Testing",
    10: "Production-Ready Code Patterns",
}


def load_set(folder: Path, set_id: int) -> dict | None:
    f = folder / f"test_set_{set_id}_results.json"
    if not f.exists():
        return None
    with open(f) as fh:
        return json.load(fh)


def load_metrics(folder: Path) -> dict | None:
    f = folder / "final_metrics_report.json"
    if not f.exists():
        return None
    with open(f) as fh:
        return json.load(fh)


def pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def delta_str(new_val: float, old_val: float, multiply=100) -> str:
    d = (new_val - old_val) * multiply
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.2f}%"


def arrow(new_val: float, old_val: float) -> str:
    if new_val > old_val + 0.001:
        return "↑"
    if new_val < old_val - 0.001:
        return "↓"
    return "="


def build_report(baseline_metrics, new_metrics, per_set_baseline, per_set_new) -> str:
    bm = baseline_metrics["metrics"]
    nm = new_metrics["metrics"]
    today = datetime.now().strftime("%Y-%m-%d")

    lines = []
    lines.append("# Dynamic Fix — Full Test Results & Comparison")
    lines.append("")
    lines.append(f"**Date:** {today}  ")
    lines.append("**What changed:** Docker dynamic execution was broken (user variables could collide with")
    lines.append("the wrapper's internal `result` dict, causing empty stdout and ParseError).")
    lines.append("Fixed by executing user code in an isolated namespace (`_cg_ns`) and renaming")
    lines.append("all wrapper variables with `_cg_` prefix.  Added `_parse_json_output()` helper")
    lines.append("to extract JSON from mixed container output.  Also hardened Windows path conversion.")
    lines.append("")
    lines.append("**Baseline (pre-fix):** `results/` — run 2026-02-20, stdlib `ast`, dynamic execution non-functional")
    lines.append("**New run (post-fix):** `result_astroid/` — run today, astroid + working Docker dynamic execution")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Overall Metrics Comparison")
    lines.append("")
    lines.append("| Metric | Baseline (pre-fix) | Post-Fix | Δ | |")
    lines.append("|---|---|---|---|---|")

    metrics_rows = [
        ("Total Cases",       bm["total_cases"],            nm["total_cases"],            False, ""),
        ("Correct",           bm["correct_predictions"],    nm["correct_predictions"],    False, ""),
        ("Accuracy",          bm["accuracy"],               nm["accuracy"],               True,  ""),
        ("Precision",         bm["precision"],              nm["precision"],              True,  ""),
        ("Recall",            bm["recall"],                 nm["recall"],                 True,  ""),
        ("F1 Score",          bm["f1_score"],               nm["f1_score"],               True,  ""),
        ("Specificity",       bm["specificity"],            nm["specificity"],            True,  ""),
        ("False Positive Rate", bm["false_positive_rate"], nm["false_positive_rate"],    True,  "(lower is better)"),
        ("False Negative Rate", bm["false_negative_rate"], nm["false_negative_rate"],    True,  "(lower is better)"),
    ]

    for label, base_v, new_v, is_pct, note in metrics_rows:
        if is_pct:
            b_str  = pct(base_v)
            n_str  = pct(new_v)
            d_str  = delta_str(new_v, base_v)
            arr    = arrow(new_v, base_v)
            # For FPR / FNR lower is better so flip arrow display
            if "Negative Rate" in label or "Positive Rate" in label:
                arr = arrow(base_v, new_v)  # flipped
            cell = f"{d_str} {arr}"
        else:
            b_str = str(int(base_v))
            n_str = str(int(new_v))
            d_str = str(int(new_v) - int(base_v))
            cell  = f"{'+' if int(new_v)>int(base_v) else ''}{d_str}"

        lines.append(f"| **{label}** | {b_str} | {n_str} | {cell} | {note} |")

    # Confusion matrix
    bcm = bm["confusion_matrix"]
    ncm = nm["confusion_matrix"]
    lines.append("")
    lines.append("### Confusion Matrix")
    lines.append("")
    lines.append("|  | Predicted Bug | Predicted Clean |")
    lines.append("|---|---|---|")
    lines.append(f"| **Actual Bug**   | TP: {bcm['TP']} → **{ncm['TP']}** | FN: {bcm['FN']} → **{ncm['FN']}** |")
    lines.append(f"| **Actual Clean** | FP: {bcm['FP']} → **{ncm['FP']}** | TN: {bcm['TN']} → **{ncm['TN']}** |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Per-Test-Set Breakdown")
    lines.append("")
    lines.append("| Set | Name | Baseline | Post-Fix | Δ | Notes |")
    lines.append("|---|---|---|---|---|---|")

    improvements = []
    regressions  = []
    unchanged    = []

    for sid in range(1, 11):
        base_set = per_set_baseline.get(sid)
        new_set  = per_set_new.get(sid)

        name = SET_NAMES.get(sid, f"Set {sid}")

        if base_set is None:
            lines.append(f"| {sid} | {name} | N/A | N/A | — | Missing baseline |")
            continue
        if new_set is None:
            lines.append(f"| {sid} | {name} | {base_set['accuracy']:.2f}% | N/A | — | Not yet run |")
            continue

        b_total  = base_set["total_cases"]
        b_corr   = base_set["correct"]
        b_err    = base_set.get("errors", 0)
        b_valid  = b_total - b_err
        b_acc    = base_set["accuracy"]

        n_total  = new_set["total_cases"]
        n_corr   = new_set["correct"]
        n_err    = new_set.get("errors", 0)
        n_valid  = n_total - n_err
        n_acc    = new_set["accuracy"]

        d        = n_acc - b_acc
        note     = ""
        if d > 0.5:
            note = "**Improved** ↑"
            improvements.append((sid, name, d))
        elif d < -0.5:
            note = "**Regressed** ↓"
            regressions.append((sid, name, d))
        else:
            note = "Unchanged ="
            unchanged.append(sid)

        if n_err > 0:
            note += f" ({n_err} API error{'s' if n_err>1 else ''})"

        d_str = f"{'+' if d>=0 else ''}{d:.2f}%"
        lines.append(f"| {sid} | {name} | {b_acc:.2f}% ({b_corr}/{b_valid}) | {n_acc:.2f}% ({n_corr}/{n_valid}) | {d_str} | {note} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Analysis")
    lines.append("")

    if improvements:
        lines.append("### 3.1 Improvements")
        lines.append("")
        for sid, name, d in improvements:
            lines.append(f"**Set {sid} (+{d:.2f}%) — {name}**  ")
            lines.append("The working Docker dynamic execution can now actually run user code and catch")
            lines.append("runtime errors (ZeroDivisionError, AttributeError, etc.) that the static layer alone")
            lines.append("was missing. This is the primary source of accuracy gains in this run.")
            lines.append("")

    if regressions:
        lines.append("### 3.2 Regressions")
        lines.append("")
        for sid, name, d in regressions:
            lines.append(f"**Set {sid} ({d:.2f}%) — {name}**  ")
            lines.append("Some regressions may stem from the dynamic layer now actively classifying code that")
            lines.append("was previously skipped (dynamic analysis returning False < now returning True), or")
            lines.append("the LLM verdict being influenced by new dynamic signals that change classification.")
            lines.append("")

    if unchanged:
        id_str = ", ".join(str(s) for s in unchanged)
        lines.append(f"### 3.3 Unchanged Sets")
        lines.append("")
        lines.append(f"Sets {id_str} showed no measurable change. These test cases are likely dominated")
        lines.append("by static analysis signals that were already working, or involve code patterns")
        lines.append("not triggered by the runtime sandbox (e.g., import errors, pure type mismatches).")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Key Fix Summary")
    lines.append("")
    lines.append("| Fix | Detail |")
    lines.append("|---|---|")
    lines.append("| **Isolated exec namespace** | `exec(code, _cg_ns)` — user's `result = ...` can no longer overwrite wrapper bookkeeping |")
    lines.append("| **`_cg_` variable prefix** | All wrapper-internal vars renamed to avoid any collision with user code |")
    lines.append("| **`_parse_json_output()`** | Scans container logs from last line upward for first valid JSON, handles mixed output |")
    lines.append("| **Windows path conversion** | `C:\\path` → `/c/path` uses `temp_dir[0].lower() + temp_dir[2:]` — no split(':') edge cases |")
    lines.append("| **`remove=False` + finally** | Container kept alive until logs are read, then force-removed |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Result File Locations")
    lines.append("")
    lines.append("| Location | Contents |")
    lines.append("|---|---|")
    lines.append("| `app/final_test/results/` | Baseline pre-fix results (stdlb ast, dynamic broken) |")
    lines.append("| `app/final_test/result_astroid/` | Post-fix results (astroid + working Docker dynamic) |")
    lines.append("| `app/final_test/compare_results.py` | This comparison script |")
    lines.append("| `app/final_test/DYNAMIC_FIX_RESULTS.md` | Generated comparison report |")

    return "\n".join(lines) + "\n"


def main():
    print("Loading baseline results from results/...")
    base_metrics = load_metrics(BASELINE_DIR)
    if not base_metrics:
        print("[ERROR] results/final_metrics_report.json not found")
        return

    print("Loading new results from result_astroid/...")
    new_metrics = load_metrics(NEW_DIR)
    if not new_metrics:
        print("[ERROR] result_astroid/final_metrics_report.json not found — has the test run completed?")
        return

    per_set_baseline = {}
    per_set_new      = {}

    for sid in range(1, 11):
        bs = load_set(BASELINE_DIR, sid)
        if bs:
            per_set_baseline[sid] = bs

        ns = load_set(NEW_DIR, sid)
        if ns:
            per_set_new[sid] = ns

    print(f"  Baseline sets loaded: {len(per_set_baseline)}")
    print(f"  New sets loaded:      {len(per_set_new)}")

    report = build_report(base_metrics, new_metrics, per_set_baseline, per_set_new)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport written to: {OUTPUT_MD}")

    # Print summary to console
    bm = base_metrics["metrics"]
    nm = new_metrics["metrics"]
    print("\n" + "=" * 60)
    print("  COMPARISON SUMMARY")
    print("=" * 60)
    print(f"  Baseline accuracy : {bm['accuracy'] * 100:.2f}%  ({bm['correct_predictions']}/{bm['total_cases']})")
    print(f"  New accuracy      : {nm['accuracy'] * 100:.2f}%  ({nm['correct_predictions']}/{nm['total_cases']})")
    delta = (nm['accuracy'] - bm['accuracy']) * 100
    print(f"  Delta             : {'+' if delta >= 0 else ''}{delta:.2f}%")
    print(f"  F1 Score          : {bm['f1_score'] * 100:.2f}% → {nm['f1_score'] * 100:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
