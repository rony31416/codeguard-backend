"""
Layer Aggregator
================
Intelligently combines results from all 3 layers using weighted voting and consensus.
Makes UI and automation decisions more reliable.
"""

from typing import Dict, List, Any, Optional


class LayerAggregator:
    """
    Aggregates results from Rule Engine, AST Analyzer, and LLM Reasoner.
    
    Uses:
    - MAX confidence (highest confidence wins)
    - WEIGHTED severity (Layer 3 > Layer 2 > Layer 1)
    - CONSENSUS detection (all_agree > majority_agree > conflicting)
    """
    
    # Weights for severity calculation
    LAYER_WEIGHTS = {
        'layer1': 0.3,  # Rule Engine - 30% weight (fast but less accurate)
        'layer2': 0.3,  # AST Analyzer - 30% weight (structural verification)
        'layer3': 0.4,  # LLM Reasoner - 40% weight (most reliable semantic understanding)
    }
    
    def aggregate_findings(
        self, 
        layer1_result: Dict[str, Any], 
        layer2_result: Optional[Dict[str, Any]] = None,
        layer3_result: Optional[Dict[str, Any]] = None,
        finding_type: str = 'issues'
    ) -> Dict[str, Any]:
        """
        Aggregate results from all layers into a unified result.
        
        Args:
            layer1_result: Results from Rule Engine (always present)
            layer2_result: Results from AST Analyzer (optional)
            layer3_result: Results from LLM Reasoner (optional)
            finding_type: Type of findings ('issues', 'features', 'values', etc.)
        
        Returns:
            Aggregated result with:
            - overall_confidence: Max confidence from all layers
            - overall_severity: Weighted severity score
            - consensus: Agreement level between layers
            - findings: Combined findings from all layers
            - layers_detail: Individual layer results
        """
        layers = {
            'layer1': layer1_result,
            'layer2': layer2_result,
            'layer3': layer3_result
        }
        
        # Remove None layers
        active_layers = {k: v for k, v in layers.items() if v is not None}
        
        # Extract confidences
        confidences = []
        for layer_name, layer_data in active_layers.items():
            conf = layer_data.get('confidence', 0)
            if conf > 0:
                confidences.append(conf)
        
        # Overall confidence = MAX confidence (highest certainty wins)
        overall_confidence = max(confidences) if confidences else 0.0
        
        # Calculate weighted severity
        overall_severity = self._calculate_weighted_severity(active_layers)
        
        # Determine consensus
        consensus = self._determine_consensus(active_layers)
        
        # Aggregate findings from all layers
        all_findings = []
        for layer_name, layer_data in active_layers.items():
            issues = layer_data.get('issues', [])
            if issues:
                # Extract message from each issue
                for issue in issues:
                    if isinstance(issue, dict):
                        message = issue.get('message', str(issue))
                    else:
                        message = str(issue)
                    
                    if message and message not in all_findings:
                        all_findings.append(message)
        
        # Determine primary detection layer (highest confidence)
        primary_layer = self._get_primary_layer(active_layers)
        
        # Determine if found based on consensus
        found = self._determine_found_status(active_layers, consensus)
        
        return {
            'found': found,
            'findings': all_findings,
            'count': len(all_findings),
            'confidence': round(overall_confidence, 2),
            'severity': round(overall_severity, 2) if overall_severity > 0 else None,
            'consensus': consensus,
            'primary_detection': primary_layer,
            'layers_used': list(active_layers.keys()),
            'layers_detail': {
                k: {
                    'found': v.get('found', False),
                    'confidence': v.get('confidence', 0),
                    'issues_count': len(v.get('issues', []))
                }
                for k, v in active_layers.items()
            }
        }
    
    def _calculate_weighted_severity(self, layers: Dict[str, Dict]) -> float:
        """
        Calculate weighted severity across all layers.
        
        Uses configured weights:
        - Layer 1 (Rule Engine): 30%
        - Layer 2 (AST Analyzer): 30%
        - Layer 3 (LLM Reasoner): 40%
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        for layer_name, layer_data in layers.items():
            if layer_data.get('found', False):
                # Get severity (default to issue count if not specified)
                severity = layer_data.get('severity', len(layer_data.get('issues', [])))
                
                # Apply weight
                weight = self.LAYER_WEIGHTS.get(layer_name, 0.3)
                weighted_sum += severity * weight
                total_weight += weight
        
        # Return weighted average (or 0 if no layers found anything)
        return weighted_sum if total_weight > 0 else 0.0
    
    def _determine_consensus(self, layers: Dict[str, Dict]) -> str:
        """
        Determine consensus level between layers.
        
        Returns:
        - 'all_agree': All layers found the issue
        - 'majority_agree': 2/3 layers found the issue
        - 'single_layer': Only 1 layer found the issue
        - 'no_issues': No layers found any issues
        """
        found_count = sum(1 for layer in layers.values() if layer.get('found', False))
        total_layers = len(layers)
        
        if found_count == 0:
            return 'no_issues'
        elif found_count == total_layers:
            return 'all_agree'
        elif found_count >= 2:
            return 'majority_agree'
        else:
            return 'single_layer'
    
    def _get_primary_layer(self, layers: Dict[str, Dict]) -> str:
        """
        Determine which layer provided the primary detection.
        Returns layer with highest confidence.
        """
        max_confidence = 0.0
        primary_layer = 'layer1'
        
        for layer_name, layer_data in layers.items():
            confidence = layer_data.get('confidence', 0)
            if confidence > max_confidence:
                max_confidence = confidence
                primary_layer = layer_name
        
        return primary_layer
    
    def _determine_found_status(self, layers: Dict[str, Dict], consensus: str) -> bool:
        """
        Determine overall 'found' status based on consensus.
        
        Logic:
        - all_agree: True (high confidence)
        - majority_agree: True (medium confidence)
        - single_layer: True if it's Layer 3 (LLM), else check confidence
        - no_issues: False
        """
        if consensus in ['all_agree', 'majority_agree']:
            return True
        
        if consensus == 'single_layer':
            # If only Layer 3 found it, trust it (highest accuracy)
            if layers.get('layer3', {}).get('found', False):
                return True
            
            # Otherwise, check if confidence is high enough
            for layer_data in layers.values():
                if layer_data.get('found', False) and layer_data.get('confidence', 0) >= 0.9:
                    return True
        
        return False
    
    def calculate_reliability_score(self, consensus: str, confidence: float) -> str:
        """
        Calculate reliability score for UI display.
        
        Returns: 'very_high' | 'high' | 'medium' | 'low'
        """
        if consensus == 'all_agree' and confidence >= 0.95:
            return 'very_high'
        elif consensus in ['all_agree', 'majority_agree'] and confidence >= 0.85:
            return 'high'
        elif confidence >= 0.75:
            return 'medium'
        else:
            return 'low'
    
    def should_auto_fix(self, consensus: str, confidence: float, severity: float) -> bool:
        """
        Determine if issue is suitable for automatic fixing.
        
        Only auto-fix when:
        - High consensus (majority_agree or all_agree)
        - High confidence (>= 0.9)
        - Severity is significant (>= 5)
        """
        return (
            consensus in ['all_agree', 'majority_agree'] and
            confidence >= 0.9 and
            severity >= 5
        )
