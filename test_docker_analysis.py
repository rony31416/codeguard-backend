"""
Comprehensive Docker + DynamicAnalyzer test suite.

Covers:
  - Clean code variants (no user variable should collide with wrapper internals)
  - ZeroDivisionError  (missing corner case)
  - AttributeError     (wrong attribute access)
  - NameError          (hallucinated / undefined name)
  - TypeError          (wrong input type)
  - IndexError         (out-of-bounds list access)
  - KeyError           (missing dict key)
  - Timeout safety     (infinite loop must not hang the suite)
  - Multi-function code (realistic snippet)
  - Variable name shadowing (user code reuses `result`, `_cg_result`, etc.)
"""

import sys, os, json, time

sys.path.insert(0, os.path.dirname(__file__))
from app.analyzers.dynamic_analyzer import DynamicAnalyzer

SEP  = "=" * 64
SEP2 = "-" * 64

PASS = 0
FAIL = 0
RESULTS = []


def run(label, code, call_code="") -> dict:
    full_code = code + ("\n" + call_code if call_code else "")
    d = DynamicAnalyzer(full_code, timeout=6)
    t0 = time.time()
    result = d.analyze()
    elapsed = time.time() - t0
    backend = "Docker" if d.client else "subprocess"
    return result, elapsed, backend


def check(label, code, call_code="", **assertions):
    """Run a test case and validate assertions.

    Assertion kwargs map a dot-path to an expected value, e.g.:
        execution_success=True
        missing_corner_case__found=True   (__ = nested key)
    """
    global PASS, FAIL
    result, elapsed, backend = run(label, code, call_code)

    errors = []
    for key, expected in assertions.items():
        # Support nested keys via double-underscore: a__b -> result["a"]["b"]
        parts = key.split("__")
        val = result
        try:
            for p in parts:
                val = val[p]
        except (KeyError, TypeError):
            val = None
        if val != expected:
            errors.append(f"  {'.'.join(parts)} = {val!r}  (expected {expected!r})")

    status = "PASS" if not errors else "FAIL"
    if not errors:
        PASS += 1
    else:
        FAIL += 1

    print(f"\n{SEP2}")
    print(f"[{status}]  {label}  [{backend}, {elapsed:.2f}s]")
    if errors:
        for e in errors:
            print(e)
    RESULTS.append({"label": label, "status": status, "result": result})
    return result


# ──────────────────────────────────────────────────────────────────────
# 1. Clean code — no bugs
# ──────────────────────────────────────────────────────────────────────
check(
    "Clean: simple arithmetic",
    "x = 2 + 2\nassert x == 4",
    execution_success=True,
)

check(
    "Clean: function call stores result in 'result'",
    "def add(a, b):\n    return a + b",
    "result = add(3, 7)\nassert result == 10",
    execution_success=True,
)

check(
    "Clean: variables named result / _cg_result / _cg_ns",
    (
        "result = 42\n"
        "_cg_result = 'shadow'\n"
        "_cg_ns = [1, 2, 3]\n"
        "assert result == 42"
    ),
    execution_success=True,
)

check(
    "Clean: list comprehension",
    "squares = [x**2 for x in range(5)]\nassert squares == [0,1,4,9,16]",
    execution_success=True,
)

check(
    "Clean: realistic multi-function snippet",
    (
        "def factorial(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    return n * factorial(n - 1)\n"
        "\n"
        "def is_even(n):\n"
        "    return n % 2 == 0\n"
    ),
    "result = factorial(5)\nassert result == 120\nassert is_even(result) == True",
    execution_success=True,
)

# ──────────────────────────────────────────────────────────────────────
# 2. ZeroDivisionError  →  missing_corner_case
# ──────────────────────────────────────────────────────────────────────
check(
    "ZeroDivisionError: plain division",
    "def divide(a, b):\n    return a / b",
    "print(divide(10, 0))",
    execution_success=False,
    missing_corner_case__found=True,
)

check(
    "ZeroDivisionError: integer floor division",
    "def idiv(a, b):\n    return a // b",
    "print(idiv(7, 0))",
    execution_success=False,
    missing_corner_case__found=True,
)

check(
    "ZeroDivisionError: modulo by zero",
    "def mod(a, b):\n    return a % b",
    "print(mod(5, 0))",
    execution_success=False,
    missing_corner_case__found=True,
)

# ──────────────────────────────────────────────────────────────────────
# 3. AttributeError  →  wrong_attribute
# ──────────────────────────────────────────────────────────────────────
check(
    "AttributeError: dict dot-access",
    'user = {"name": "Alice"}\nprint(user.name)',
    execution_success=False,
    wrong_attribute__found=True,
)

check(
    "AttributeError: int has no .upper()",
    "x = 42\nprint(x.upper())",
    execution_success=False,
    wrong_attribute__found=True,
)

check(
    "AttributeError: None has no attribute",
    "val = None\nprint(val.strip())",
    execution_success=False,
    wrong_attribute__found=True,
)

# ──────────────────────────────────────────────────────────────────────
# 4. NameError  →  name_error
# ──────────────────────────────────────────────────────────────────────
check(
    "NameError: hallucinated object",
    "result = calculator.compute(5)",
    execution_success=False,
    name_error__found=True,
)

check(
    "NameError: undefined function",
    "output = transform_data([1, 2, 3])",
    execution_success=False,
    name_error__found=True,
)

# ──────────────────────────────────────────────────────────────────────
# 5. TypeError  →  wrong_input_type
# ──────────────────────────────────────────────────────────────────────
check(
    "TypeError: str + int",
    'result = "hello" + 5',
    execution_success=False,
    wrong_input_type__found=True,
)

check(
    "TypeError: unsupported operand",
    "result = [1, 2] + 3",
    execution_success=False,
    wrong_input_type__found=True,
)

check(
    "TypeError: non-iterable in for loop",
    "for x in 42:\n    print(x)",
    execution_success=False,
    wrong_input_type__found=True,
)

# ──────────────────────────────────────────────────────────────────────
# 6. Other runtime errors  →  other_error
# ──────────────────────────────────────────────────────────────────────
check(
    "IndexError: list out of range",
    "lst = [1, 2, 3]\nprint(lst[10])",
    execution_success=False,
    other_error__found=True,
)

check(
    "KeyError: missing dict key",
    'd = {"a": 1}\nprint(d["z"])',
    execution_success=False,
    other_error__found=True,
)

check(
    "ValueError: int() on bad string",
    'x = int("not_a_number")',
    execution_success=False,
    other_error__found=True,
)

# ──────────────────────────────────────────────────────────────────────
# 7. Timeout (infinite loop) — must not exceed ~10 s
# ──────────────────────────────────────────────────────────────────────
check(
    "Timeout: infinite loop",
    "while True:\n    pass",
    execution_success=False,
    # May be classified as TimeoutError or some other_error — just must not pass
)
# Override: we only care that execution_success is False AND it finished quickly
# (elapsed is already printed above)

# ──────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{SEP}")
print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
print(SEP)

if FAIL > 0:
    print("\nFailed tests:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"  - {r['label']}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
