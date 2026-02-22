"""
Docker + DynamicAnalyzer end-to-end test
"""
from app.analyzers.dynamic_analyzer import DynamicAnalyzer
import json

SEP = "=" * 60

def run(label, code, call_code=""):
    full_code = code + "\n" + call_code if call_code else code
    d = DynamicAnalyzer(full_code)
    result = d.analyze()
    print(f"\n{SEP}")
    print(f"TEST: {label}")
    print(f"Docker: {'YES' if d.client else 'NO (subprocess fallback)'}")
    print(f"Result: {json.dumps(result, indent=2)}")
    return result

# ── Test 1: Clean code ───────────────────────────────────────────────
r1 = run(
    "Clean code (no errors)",
    "def add(a, b):\n    return a + b",
    "result = add(1, 2)"
)
assert r1.get("execution_success") == True, "FAIL: expected success"
print("PASS: clean code executes successfully")

# ── Test 2: ZeroDivisionError ────────────────────────────────────────
r2 = run(
    "ZeroDivisionError at runtime",
    "def divide(a, b):\n    return a / b",
    "print(divide(10, 0))"
)
assert r2.get("missing_corner_case", {}).get("found") == True, "FAIL: ZeroDivisionError not detected"
print("PASS: ZeroDivisionError detected as missing_corner_case")

# ── Test 3: AttributeError (dict.key) ───────────────────────────────
r3 = run(
    "AttributeError (dict dot access)",
    'user = {"name": "Alice"}\nprint(user.name)'
)
assert r3.get("wrong_attribute", {}).get("found") == True, "FAIL: AttributeError not detected"
print("PASS: AttributeError detected as wrong_attribute")

# ── Test 4: NameError (hallucinated object) ──────────────────────────
r4 = run(
    "NameError (undefined variable)",
    "result = calculator.compute(5)"
)
assert r4.get("name_error", {}).get("found") == True, "FAIL: NameError not detected"
print("PASS: NameError detected")

# ── Test 5: TypeError ────────────────────────────────────────────────
r5 = run(
    "TypeError (string + int)",
    'result = "hello" + 5'
)
assert r5.get("wrong_input_type", {}).get("found") == True, "FAIL: TypeError not detected"
print("PASS: TypeError detected as wrong_input_type")

print(f"\n{SEP}")
print("ALL DOCKER DYNAMIC ANALYZER TESTS PASSED")
print(SEP)
