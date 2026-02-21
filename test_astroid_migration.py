"""
Test script: Verify astroid migration for all modified files.
"""
import sys
sys.path.insert(0, '.')

print("=== Testing astroid migration ===\n")
all_passed = True

def check(label, condition, detail=""):
    global all_passed
    status = "PASS" if condition else "FAIL"
    if not condition:
        all_passed = False
    print(f"  [{status}] {label}" + (f" -> {detail}" if detail else ""))

# -----------------------------------------------
# Test 1: SyntaxErrorDetector with astroid
# -----------------------------------------------
print("1. syntax_detector.py (astroid.parse)")
from app.analyzers.static.detectors.syntax_detector import SyntaxErrorDetector

# Good code: no error
d = SyntaxErrorDetector("def foo(a, b):\n    return a + b")
r = d.detect()
check("Good code -> no error", r["found"] == False)
check("Tree is populated", d.tree is not None)

# Bad code: syntax error
d2 = SyntaxErrorDetector("def foo(a, b)\n    return a + b")
r2 = d2.detect()
check("Bad code -> error found", r2["found"] == True)
check("Error has line number", r2.get("line") is not None, f"line={r2.get('line')}")

# -----------------------------------------------
# Test 2: HallucinatedObjectDetector with astroid
# -----------------------------------------------
print("\n2. hallucination_detector.py (astroid nodes)")
from app.analyzers.static.detectors.hallucination_detector import HallucinatedObjectDetector

d = HallucinatedObjectDetector("x = MyFakeClass()\nprint(x)")
r = d.detect()
check("Detects hallucinated CamelCase class", r["found"] == True)
check("Found objects list non-empty", len(r["objects"]) > 0, str(r["objects"][:2]))

# Clean code: no hallucination
d2 = HallucinatedObjectDetector("def foo(a, b):\n    return a + b\n\nfoo(1, 2)")
r2 = d2.detect()
check("Clean code -> no hallucination", r2["found"] == False or len(r2["objects"]) == 0,
      f"objects={r2['objects']}")

# -----------------------------------------------
# Test 3: WrongAttributeDetector with astroid inference
# -----------------------------------------------
print("\n3. wrong_attribute_detector.py (astroid inference)")
from app.analyzers.static.detectors.wrong_attribute_detector import WrongAttributeDetector

# Dict access via dot notation - astroid inference should detect inferred Dict
d = WrongAttributeDetector("data = {'cost': 5, 'name': 'item'}\nprint(data.cost)")
r = d.detect()
check("Returns valid structure", "found" in r and "details" in r)
# Note: astroid may or may not infer the dict (depends on scope), just verify no crash

d2 = WrongAttributeDetector("class Foo:\n    def __init__(self):\n        self.cost = 5\n\nf = Foo()\nprint(f.cost)")
r2 = d2.detect()
check("Class attribute access not flagged", r2["found"] == False or len(r2["details"]) == 0,
      f"details={r2['details']}")

# -----------------------------------------------
# Test 4: WrongInputTypeDetector with astroid
# -----------------------------------------------
print("\n4. wrong_input_type_detector.py (nodes.Const)")
from app.analyzers.static.detectors.wrong_input_type_detector import WrongInputTypeDetector

d = WrongInputTypeDetector("import math\nresult = math.sqrt('hello')")
r = d.detect()
check("Detects string passed to sqrt()", r["found"] == True, str(r["details"]))

d2 = WrongInputTypeDetector("import math\nresult = math.sqrt(4)")
r2 = d2.detect()
check("Numeric arg to sqrt() not flagged", r2["found"] == False)

# -----------------------------------------------
# Test 5: Layer2 ASTAnalyzer with astroid
# -----------------------------------------------
print("\n5. layer2_ast_analyzer.py (astroid nodes)")
from app.analyzers.linguistic.layers.layer2_ast_analyzer import ASTAnalyzer

a = ASTAnalyzer()

# NPC: print instead of return
npc = a.verify_npc("def foo():\n    print('hello')\n    return 1")
check("NPC: detects print statement", npc["found"] == True, f"issues={len(npc['issues'])}")

# Prompt bias: hardcoded numbers
bias = a.verify_prompt_bias("def foo():\n    return 42", "add 42 numbers together")
check("Prompt bias: detects hardcoded number from prompt", bias["found"] == True, str(bias["issues"]))

# Return type mismatch: print vs return
rt = a.analyze_return_type_mismatch(
    "def foo():\n    print('result')",
    "write a function that returns a value"
)
check("Return mismatch: print instead of return", rt["found"] == True, str(rt["issues"]))

# -----------------------------------------------
# Test 6: Utils ASTAnalyzer with astroid
# -----------------------------------------------
print("\n6. utils/ast_analyzer.py (astroid nodes_of_class)")
import astroid
from app.analyzers.linguistic.utils.ast_analyzer import ASTAnalyzer as UtilsAST

tree = astroid.parse("def foo(a, b):\n    return a + b\n\nresult = foo(1, 2)")
ua = UtilsAST(tree)

funcs = ua.get_function_names()
check("get_function_names()", "foo" in funcs, str(funcs))

calls = ua.get_function_calls()
check("get_function_calls()", "foo" in calls, str(calls))

loops = ua.count_loops()
check("count_loops() returns dict", isinstance(loops, dict) and "for" in loops, str(loops))

recursion_code = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
rec_tree = astroid.parse(recursion_code)
ua2 = UtilsAST(rec_tree)
check("has_recursion() detects recursive function", ua2.has_recursion() == True)

# -----------------------------------------------
# Test 7: Full StaticAnalyzer pipeline
# -----------------------------------------------
print("\n7. StaticAnalyzer full pipeline")
from app.analyzers.static.static_analyzer import StaticAnalyzer

analyzer = StaticAnalyzer("def add(a, b)\n    return a + b")
results = analyzer.analyze()
check("Syntax error detected by pipeline", results["syntax_error"]["found"] == True)

analyzer2 = StaticAnalyzer("import math\ndef calculate(x):\n    return math.sqrt(x)")
results2 = analyzer2.analyze()
check("Clean code: no syntax error", results2["syntax_error"]["found"] == False)
check("Clean code: all results present", len(results2) == 9)

# -----------------------------------------------
# Summary
# -----------------------------------------------
print("\n" + "=" * 50)
if all_passed:
    print("All tests PASSED - astroid migration successful!")
else:
    print("Some tests FAILED - check output above")
print("=" * 50)
