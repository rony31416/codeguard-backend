from typing import List, Dict, Any
from ..schemas import BugPatternSchema

class TaxonomyClassifier:
    def __init__(self, static_results: Dict, dynamic_results: Dict, linguistic_results: Dict = None):
        self.static = static_results
        self.dynamic = dynamic_results
        self.linguistic = linguistic_results or {}  # NEW: Stage 3 results
        self.bug_patterns = []
    
    def classify(self) -> List[BugPatternSchema]:
        """Map analysis results to bug taxonomy patterns"""
        
        # Stage I: Static Analysis Patterns
        if self.static.get("syntax_error", {}).get("found"):
            self._add_syntax_error()
        
        if self.static.get("hallucinated_objects", {}).get("found"):
            self._add_hallucinated_object()
        
        if self.static.get("incomplete_generation", {}).get("found"):
            self._add_incomplete_generation()
        
        if self.static.get("silly_mistakes", {}).get("found"):
            self._add_silly_mistake()
        
        # Stage II: Dynamic Analysis Patterns
        if self.dynamic.get("wrong_attribute", {}).get("found"):
            self._add_wrong_attribute()
        
        if self.dynamic.get("wrong_input_type", {}).get("found"):
            self._add_wrong_input_type()
        
        # Also check static detection of wrong attributes
        if self.static.get("wrong_attribute", {}).get("found"):
            self._add_wrong_attribute_static()
        
        # Also check static detection of wrong input types
        if self.static.get("wrong_input_type", {}).get("found"):
            if not any(p.pattern_name == "Wrong Input Type" for p in self.bug_patterns):
                self._add_wrong_input_type_static()
        
        # Confirm hallucinated object with NameError
        if self.dynamic.get("name_error", {}).get("found"):
            if not any(p.pattern_name == "Hallucinated Object" for p in self.bug_patterns):
                self._add_hallucinated_object_from_runtime()
        
        # Stage III: Logic and Linguistic Patterns
        if self.linguistic.get("npc", {}).get("found"):
            self._add_npc()
        
        if self.linguistic.get("prompt_biased", {}).get("found"):
            self._add_prompt_biased()
        
        if self.linguistic.get("missing_features", {}).get("found"):
            self._add_missing_features()
        
        if self.static.get("missing_corner_case", {}).get("found"):
            self._add_missing_corner_case()
        
        # Check for misinterpretation (if code has logic issues but no clear category)
        if len(self.bug_patterns) > 3:
            self._add_misinterpretation()
        
        # If no bugs found
        if len(self.bug_patterns) == 0:
            self._add_no_bugs_detected()
        
        return self.bug_patterns
    
    def _add_syntax_error(self):
        error_info = self.static["syntax_error"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Syntax Error",
            severity=9,
            confidence=1.0,
            description=f"The code contains a syntax error at line {error_info.get('line')}: {error_info.get('error')}",
            location=f"Line {error_info.get('line')}, Column {error_info.get('offset')}",
            fix_suggestion="Review the syntax at the indicated location. Common issues include missing colons, unmatched parentheses, or incorrect indentation."
        ))
    
    def _add_hallucinated_object(self):
        objects = self.static["hallucinated_objects"]["objects"]
        object_names = [obj['name'] if isinstance(obj, dict) else obj for obj in objects]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Hallucinated Object",
            severity=8,
            confidence=0.85,
            description=f"The code references undefined objects that may not exist: {', '.join(object_names)}. LLMs sometimes invent functions, classes or variables that aren't available.",
            location=f"Objects: {', '.join(object_names)}",
            fix_suggestion=f"Verify that {', '.join(object_names)} exist in the imported modules or define them before use. Check official documentation for correct API usage."
        ))
    
    def _add_hallucinated_object_from_runtime(self):
        error_info = self.dynamic["name_error"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Hallucinated Object",
            severity=8,
            confidence=0.95,
            description=f"Runtime NameError confirms undefined object: {error_info.get('error')}. The LLM generated code referencing non-existent functions or variables.",
            location="See traceback",
            fix_suggestion="Define the missing object or import it from the correct module. Double-check the API documentation."
        ))
    
    def _add_incomplete_generation(self):
        details = self.static["incomplete_generation"]["details"]
        descriptions = [d['description'] for d in details]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Incomplete Generation",
            severity=7,
            confidence=0.90,
            description=f"Code generation appears incomplete. Issues: {'; '.join(descriptions)}. The LLM may have been cut off or reached token limits.",
            location=f"{len(details)} incomplete section(s) detected",
            fix_suggestion="Complete the missing logic based on the function's intended purpose."
        ))
    
    def _add_silly_mistake(self):
        details = self.static["silly_mistakes"]["details"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Silly Mistake",
            severity=6,
            confidence=0.80,
            description=f"Non-human coding patterns detected. Found {len(details)} issue(s) including: {details[0]['description']}. LLMs sometimes generate logically redundant or reversed operations.",
            location=f"Line {details[0]['line']}",
            fix_suggestion="Review the logic flow. Common issues: reversed operands, wrong data type operations, or redundant conditions."
        ))
    
    def _add_wrong_attribute(self):
        error_info = self.dynamic["wrong_attribute"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Wrong Attribute",
            severity=7,
            confidence=0.90,
            description=f"AttributeError occurred: {error_info.get('error')}. The LLM attempted to access an attribute or method that doesn't exist on the object.",
            location="See traceback",
            fix_suggestion="Check the object's available attributes using dir() or consult the API documentation. Ensure you're using the correct method name."
        ))
    
    def _add_wrong_attribute_static(self):
        details = self.static["wrong_attribute"]["details"]
        attrs = [f"{d['variable']}.{d['attribute']}" for d in details]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Wrong Attribute",
            severity=7,
            confidence=0.75,
            description=f"Detected incorrect attribute access patterns: {', '.join(attrs)}. Likely treating dictionary keys as object attributes (e.g., dict.key instead of dict['key']).",
            location=f"Found {len(details)} occurrence(s)",
            fix_suggestion=f"Use dictionary access syntax: item['key'] instead of item.key for dictionaries."
        ))
    
    def _add_wrong_input_type(self):
        error_info = self.dynamic["wrong_input_type"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Wrong Input Type",
            severity=6,
            confidence=0.85,
            description=f"TypeError occurred: {error_info.get('error')}. The function was called with an inappropriate data type or wrong operation on incompatible types.",
            location="See traceback",
            fix_suggestion="Verify the expected input types for the function. Add type conversion or validation before operations. Check for string concatenation with numeric values."
        ))
    
    def _add_wrong_input_type_static(self):
        details = self.static["wrong_input_type"]["details"]
        issues = [f"{d['function']}({d['value']})" for d in details[:3]]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Wrong Input Type",
            severity=6,
            confidence=0.80,
            description=f"Detected wrong input types: {', '.join(issues)}. Passing string literals to numeric functions or vice versa.",
            location=f"Line {details[0]['line']}",
            fix_suggestion=f"Convert types appropriately: use {details[0]['expected_type']} instead of {details[0]['actual_type']}. Remove quotes from numeric values."
        ))
    
    def _add_npc(self):
        npc_data = self.linguistic["npc"]
        features = npc_data.get("features", [])
        count = npc_data.get("count", 0)
        confidence = npc_data.get("confidence", 0.70)
        
        # Format features list for display
        if features:
            features_list = ', '.join(features[:3])  # Show first 3
            if len(features) > 3:
                features_list += f" (+{len(features)-3} more)"
        else:
            features_list = "unrequested code additions"
        
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Non-Prompted Consideration (NPC)",
            severity=5,
            confidence=confidence,
            description=f"The code includes features that weren't requested. Detected {count} unrequested addition(s): {features_list}. LLMs sometimes add security checks, validations, or features beyond the prompt scope.",
            location=f"Multiple locations ({count} issues)",
            fix_suggestion="Remove the unrequested features unless they are actually needed for your use case."
        ))
    
    def _add_prompt_biased(self):
        biased_data = self.linguistic["prompt_biased"]
        values = biased_data.get("values", [])
        count = biased_data.get("count", 0)
        confidence = biased_data.get("confidence", 0.75)
        
        # Format values list for display
        if values:
            values_list = ', '.join(str(v) for v in values[:3])  # Show first 3
            if len(values) > 3:
                values_list += f" (+{len(values)-3} more)"
        else:
            values_list = "hardcoded example values"
        
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Prompt-Biased Code",
            severity=6,
            confidence=confidence,
            description=f"The code contains hardcoded logic based on specific examples from the prompt rather than general solutions. Found {count} instance(s) of example-specific code: {values_list}.",
            location=f"Multiple locations ({count} issues)",
            fix_suggestion="Replace hardcoded values and example-specific logic with general-purpose code that works for all inputs."
        ))
    
    def _add_missing_features(self):
        missing_data = self.linguistic["missing_features"]
        features = missing_data.get("features", [])
        count = missing_data.get("count", 0)
        confidence = missing_data.get("confidence", 0.65)
        
        # Format features list for display
        if features:
            features_list = ', '.join(features[:3])  # Show first 3
            if len(features) > 3:
                features_list += f" (+{len(features)-3} more)"
        else:
            features_list = "requested features"
        
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Missing Features",
            severity=6,
            confidence=confidence,
            description=f"The code is missing features that were requested in the prompt. Detected {count} missing feature(s): {features_list}. The LLM may have overlooked or misunderstood some requirements.",
            location=f"Multiple locations ({count} missing)",
            fix_suggestion="Add the missing features mentioned in the prompt. Review the prompt carefully to ensure all requirements are implemented."
        ))
    
    def _add_missing_corner_case(self):
        details = self.static["missing_corner_case"]["details"]
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Missing Corner Case",
            severity=5,
            confidence=0.65,
            description=f"The code doesn't handle edge cases properly. Detected {len(details)} missing check(s): {details[0]['description']}. Common issues include missing None checks, zero division, or empty input handling.",
            location=f"Multiple locations ({len(details)} issues)",
            fix_suggestion="Add validation for edge cases: check for None inputs, empty lists, zero values in division, and boundary conditions."
        ))
    
    def _add_misinterpretation(self):
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="Misinterpretation",
            severity=7,
            confidence=0.60,
            description="The code has multiple issues suggesting the LLM may have misunderstood the task requirements. This is the most common and difficult-to-diagnose bug pattern.",
            location="Multiple issues across the code",
            fix_suggestion="Review the prompt and compare with the generated code logic. The fundamental approach may need to be rewritten."
        ))
    
    def _add_no_bugs_detected(self):
        self.bug_patterns.append(BugPatternSchema(
            pattern_name="No Bugs Detected",
            severity=0,
            confidence=0.70,
            description="Static and dynamic analysis did not detect any obvious bugs. However, logic errors or missing corner cases may still exist and require test case validation.",
            location="N/A",
            fix_suggestion="Consider writing comprehensive test cases to validate correctness, especially for edge cases."
        ))
    
    def get_overall_severity(self) -> int:
        """Calculate overall severity score"""
        if not self.bug_patterns:
            return 0
        return max(p.severity for p in self.bug_patterns)
    
    def has_bugs(self) -> bool:
        """Check if any actual bugs were found"""
        return any(p.pattern_name != "No Bugs Detected" for p in self.bug_patterns)
