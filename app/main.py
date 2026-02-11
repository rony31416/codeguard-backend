from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import time
import json
from pydantic import BaseModel

from .database import engine, get_db, Base
from .schemas import CodeAnalysisRequest, AnalysisResponse, FeedbackRequest, BugPatternSchema, ExecutionLogSchema
from .models import Analysis, BugPattern, Feedback, ExecutionLog, LinguisticAnalysis
from .analyzers.static_analyzer import StaticAnalyzer
from .analyzers.dynamic_analyzer import DynamicAnalyzer
from .analyzers.classifier import TaxonomyClassifier
from .analyzers.explainer import ExplainabilityLayer

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CodeGuard API",
    version="2.0.0",
    description="LLM Bug Taxonomy Classifier & Analyzer with Three-Stage Hybrid Detection"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """API health check endpoint"""
    return {
        "message": "CodeGuard API is running",
        "version": "2.0.0",
        "stages": ["static", "dynamic", "linguistic"],
        "bug_patterns": 10
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_code(request: CodeAnalysisRequest, db: Session = Depends(get_db)):
    """
    Main analysis endpoint: Three-Stage Hybrid Detection
    
    Stage 1: Static Analysis (AST, Pylint)
    Stage 2: Dynamic Analysis (Docker Sandbox)
    Stage 3: Linguistic Analysis (Prompt-Code Comparison)
    
    Returns: Classified bug patterns from 10 LLM-specific categories
    """
    execution_logs = []
    linguistic_analyzer = None
    
    try:
        print(f"Starting analysis - Prompt: {request.prompt[:50]}..., Code length: {len(request.code)}")
        
        # ===== STAGE 1: Static Analysis =====
        print("Stage 1: Running static analysis...")
        static_start = time.time()
        try:
            static_analyzer = StaticAnalyzer(request.code)
            static_results = static_analyzer.analyze()
            static_time = time.time() - static_start
            
            execution_logs.append({
                "stage": "static",
                "success": True,
                "execution_time": round(static_time, 3),
                "error_message": None,
                "error_type": None
            })
            print(f"✓ Static analysis completed in {static_time:.3f}s")
        except Exception as e:
            static_results = {}
            static_time = time.time() - static_start
            execution_logs.append({
                "stage": "static",
                "success": False,
                "execution_time": round(static_time, 3),
                "error_message": str(e),
                "error_type": type(e).__name__
            })
            print(f"✗ Static analysis failed: {str(e)}")
        
        # ===== STAGE 2: Dynamic Analysis =====
        print("Stage 2: Running dynamic analysis (Docker sandbox)...")
        dynamic_start = time.time()
        try:
            dynamic_analyzer = DynamicAnalyzer(request.code)
            dynamic_results = dynamic_analyzer.analyze()
            dynamic_time = time.time() - dynamic_start
            
            execution_logs.append({
                "stage": "dynamic",
                "success": not dynamic_results.get("execution_error", False),
                "execution_time": round(dynamic_time, 3),
                "error_message": dynamic_results.get("error_message") if dynamic_results.get("execution_error") else None,
                "error_type": None
            })
            print(f"✓ Dynamic analysis completed in {dynamic_time:.3f}s")
        except Exception as e:
            dynamic_results = {
                "execution_success": False,
                "wrong_attribute": {"found": False},
                "wrong_input_type": {"found": False},
                "name_error": {"found": False},
                "other_error": {"found": False}
            }
            dynamic_time = time.time() - dynamic_start
            execution_logs.append({
                "stage": "dynamic",
                "success": False,
                "execution_time": round(dynamic_time, 3),
                "error_message": str(e),
                "error_type": type(e).__name__
            })
            print(f"✗ Dynamic analysis failed: {str(e)}")
        
        # ===== STAGE 3: Linguistic Analysis =====
        print("Stage 3: Running linguistic analysis (prompt-code comparison)...")
        linguistic_start = time.time()
        linguistic_results = {}
        try:
            from .analyzers.linguistic_analyzer import LinguisticAnalyzer
            linguistic_analyzer = LinguisticAnalyzer(request.prompt, request.code)
            linguistic_results = linguistic_analyzer.analyze()
            linguistic_time = time.time() - linguistic_start
            
            execution_logs.append({
                "stage": "linguistic",
                "success": True,
                "execution_time": round(linguistic_time, 3),
                "error_message": None,
                "error_type": None
            })
            print(f"✓ Linguistic analysis completed in {linguistic_time:.3f}s")
        except ImportError:
            # Linguistic analyzer not implemented yet
            linguistic_results = {
                "npc": {"found": False, "features": []},
                "prompt_biased": {"found": False, "values": []},
                "missing_features": {"found": False, "features": []},
                "misinterpretation": {"found": False, "score": 0.0, "reasons": []},
                "intent_match_score": 0.0
            }
            linguistic_time = time.time() - linguistic_start
            execution_logs.append({
                "stage": "linguistic",
                "success": False,
                "execution_time": round(linguistic_time, 3),
                "error_message": "Linguistic analyzer not implemented yet",
                "error_type": "NotImplementedError"
            })
            print("⚠ Linguistic analysis not implemented - using fallback")
        except Exception as e:
            linguistic_results = {
                "npc": {"found": False, "features": []},
                "prompt_biased": {"found": False, "values": []},
                "missing_features": {"found": False, "features": []},
                "misinterpretation": {"found": False, "score": 0.0, "reasons": []},
                "intent_match_score": 0.0
            }
            linguistic_time = time.time() - linguistic_start
            execution_logs.append({
                "stage": "linguistic",
                "success": False,
                "execution_time": round(linguistic_time, 3),
                "error_message": str(e),
                "error_type": type(e).__name__
            })
            print(f"✗ Linguistic analysis failed: {str(e)}")
        
        # ===== STAGE 4: Classification =====
        print("Stage 4: Classifying bug patterns...")
        classifier_start = time.time()
        try:
            classifier = TaxonomyClassifier(static_results, dynamic_results, linguistic_results)
            bug_patterns_list = classifier.classify()
            classifier_time = time.time() - classifier_start
            
            execution_logs.append({
                "stage": "classification",
                "success": True,
                "execution_time": round(classifier_time, 3),
                "error_message": None,
                "error_type": None
            })
            print(f"✓ Classification completed: {len(bug_patterns_list)} patterns detected")
        except Exception as e:
            classifier_time = time.time() - classifier_start
            execution_logs.append({
                "stage": "classification",
                "success": False,
                "execution_time": round(classifier_time, 3),
                "error_message": str(e),
                "error_type": type(e).__name__
            })
            raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
        
        # ===== STAGE 5: Explainability =====
        explainer = ExplainabilityLayer()
        summary = explainer.generate_summary(bug_patterns_list)
        overall_severity = classifier.get_overall_severity()
        has_bugs = classifier.has_bugs()
        
        print(f"Overall severity: {overall_severity}/10, Has bugs: {has_bugs}")
        
        # ===== Save to Database =====
        print("Saving analysis to database...")
        analysis = Analysis(
            prompt=request.prompt,
            code=request.code,
            language='python',
            overall_severity=overall_severity,
            has_bugs=has_bugs,
            summary=summary,
            confidence_score=sum(p.confidence for p in bug_patterns_list) / len(bug_patterns_list) if bug_patterns_list else 0.0,
            prompt_keywords=json.dumps(list(linguistic_analyzer.prompt_keywords)) if linguistic_analyzer else None,
            code_features=json.dumps(list(linguistic_analyzer.code_features)) if linguistic_analyzer else None
        )
        db.add(analysis)
        db.flush()  # Get analysis_id before adding related records
        
        # Save bug patterns
        for bug_pattern in bug_patterns_list:
            # Determine detection stage
            detection_stage = None
            if bug_pattern.pattern_name in ['Syntax Error', 'Hallucinated Object', 'Incomplete Generation', 'Silly Mistake']:
                detection_stage = 'static'
            elif bug_pattern.pattern_name in ['Wrong Attribute', 'Wrong Input Type']:
                detection_stage = 'dynamic'
            else:
                detection_stage = 'linguistic'
            
            db_bug = BugPattern(
                analysis_id=analysis.analysis_id,
                pattern_name=bug_pattern.pattern_name,
                severity=bug_pattern.severity,
                confidence=bug_pattern.confidence,
                description=bug_pattern.description,
                location=bug_pattern.location,
                fix_suggestion=bug_pattern.fix_suggestion,
                detection_stage=detection_stage
            )
            db.add(db_bug)
        
        # Save execution logs
        for log in execution_logs:
            db_log = ExecutionLog(
                analysis_id=analysis.analysis_id,
                stage=log["stage"],
                success=log["success"],
                error_message=log.get("error_message"),
                error_type=log.get("error_type"),
                traceback=None,
                execution_time=log.get("execution_time")
            )
            db.add(db_log)
        
        # Save linguistic analysis details
        if linguistic_results and linguistic_analyzer:
            ling_analysis = LinguisticAnalysis(
                analysis_id=analysis.analysis_id,
                prompt_intent=json.dumps(linguistic_results.get('missing_features', {})),
                code_intent=json.dumps(linguistic_results.get('npc', {})),
                intent_match_score=linguistic_results.get('intent_match_score', 0.0),
                unprompted_features=json.dumps(linguistic_results.get('npc', {}).get('features', [])),
                missing_features=json.dumps(linguistic_results.get('missing_features', {}).get('features', [])),
                hardcoded_values=json.dumps(linguistic_results.get('prompt_biased', {}).get('values', []))
            )
            db.add(ling_analysis)
        
        db.commit()
        db.refresh(analysis)
        
        print(f"✓ Analysis saved with ID: {analysis.analysis_id}")
        
        # ===== Prepare Response =====
        return AnalysisResponse(
            analysis_id=analysis.analysis_id,
            bug_patterns=[BugPatternSchema.from_orm(bp) for bp in analysis.bug_patterns],
            execution_logs=[ExecutionLogSchema.from_orm(el) for el in analysis.execution_logs],
            overall_severity=overall_severity,
            has_bugs=has_bugs,
            summary=summary,
            created_at=analysis.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/feedback", response_model=FeedbackRequest)
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback for an analysis"""
    # Check if analysis exists
    analysis = db.query(Analysis).filter(Analysis.analysis_id == feedback.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Create feedback
    db_feedback = Feedback(
        analysis_id=feedback.analysis_id,
        rating=feedback.rating,
        comment=feedback.comment,
        is_helpful=feedback.is_helpful
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@app.get("/api/history")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get analysis history
    
    Useful for:
    - Viewing past analyses in VS Code extension
    - Tracking analysis trends
    - Research data collection
    """
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
    return {
        "total": len(analyses),
        "analyses": [
            {
                "analysis_id": a.analysis_id,
                "prompt": a.prompt[:100] + "..." if len(a.prompt) > 100 else a.prompt,
                "severity": a.overall_severity,
                "has_bugs": a.has_bugs,
                "bug_count": len(a.bug_patterns),
                "created_at": a.created_at.isoformat(),
                "feedback": a.feedback.feedback_type if a.feedback else None
            }
            for a in analyses
        ]
    }


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get specific analysis details
    
    Returns complete analysis including:
    - Bug patterns
    - Execution logs
    - Linguistic analysis results
    - User feedback
    """
    analysis = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": analysis.analysis_id,
        "prompt": analysis.prompt,
        "code": analysis.code,
        "language": analysis.language,
        "bug_patterns": [BugPatternSchema.from_orm(bp).dict() for bp in analysis.bug_patterns],
        "execution_logs": [ExecutionLogSchema.from_orm(el).dict() for el in analysis.execution_logs],
        "overall_severity": analysis.overall_severity,
        "has_bugs": analysis.has_bugs,
        "summary": analysis.summary,
        "confidence_score": analysis.confidence_score,
        "created_at": analysis.created_at.isoformat(),
        "linguistic_analysis": {
            "intent_match_score": analysis.linguistic_analysis.intent_match_score,
            "unprompted_features": json.loads(analysis.linguistic_analysis.unprompted_features),
            "missing_features": json.loads(analysis.linguistic_analysis.missing_features),
            "hardcoded_values": json.loads(analysis.linguistic_analysis.hardcoded_values)
        } if analysis.linguistic_analysis else None,
        "feedback": {
            "type": analysis.feedback.feedback_type,
            "comment": analysis.feedback.comment,
            "submitted_at": analysis.feedback.submitted_at.isoformat()
        } if analysis.feedback else None
    }


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get statistics for research analysis
    
    Provides:
    - Total analyses performed
    - Bug pattern frequency distribution
    - Average severity by pattern
    - Detection stage effectiveness
    - User feedback accuracy metrics
    """
    from sqlalchemy import func
    
    # Basic counts
    total_analyses = db.query(Analysis).count()
    total_bugs = db.query(BugPattern).count()
    analyses_with_bugs = db.query(Analysis).filter(Analysis.has_bugs == True).count()
    
    # Bug pattern frequency
    pattern_frequency = db.query(
        BugPattern.pattern_name,
        func.count(BugPattern.bug_pattern_id).label('count')
    ).group_by(BugPattern.pattern_name).order_by(func.count(BugPattern.bug_pattern_id).desc()).all()
    
    # Average severity by pattern
    avg_severity = db.query(
        BugPattern.pattern_name,
        func.avg(BugPattern.severity).label('avg_severity'),
        func.avg(BugPattern.confidence).label('avg_confidence')
    ).group_by(BugPattern.pattern_name).all()
    
    # Detection stage distribution
    stage_distribution = db.query(
        BugPattern.detection_stage,
        func.count(BugPattern.bug_pattern_id).label('count')
    ).group_by(BugPattern.detection_stage).all()
    
    # Feedback statistics
    feedback_stats = db.query(
        Feedback.feedback_type,
        func.count(Feedback.feedback_id).label('count')
    ).group_by(Feedback.feedback_type).all()
    
    # Execution stage success rates
    stage_success = db.query(
        ExecutionLog.stage,
        func.avg(func.cast(ExecutionLog.success, Integer)).label('success_rate'),
        func.avg(ExecutionLog.execution_time).label('avg_time')
    ).group_by(ExecutionLog.stage).all()
    
    return {
        "overview": {
            "total_analyses": total_analyses,
            "total_bugs_detected": total_bugs,
            "analyses_with_bugs": analyses_with_bugs,
            "bug_detection_rate": round(analyses_with_bugs / total_analyses * 100, 2) if total_analyses > 0 else 0
        },
        "pattern_frequency": [
            {
                "pattern": p[0],
                "count": p[1],
                "percentage": round(p[1] / total_bugs * 100, 2) if total_bugs > 0 else 0
            }
            for p in pattern_frequency
        ],
        "average_metrics": [
            {
                "pattern": p[0],
                "avg_severity": round(float(p[1]), 2),
                "avg_confidence": round(float(p[2]), 2)
            }
            for p in avg_severity
        ],
        "detection_stages": [
            {
                "stage": s[0] if s[0] else "unknown",
                "count": s[1]
            }
            for s in stage_distribution
        ],
        "feedback": [
            {
                "type": f[0],
                "count": f[1]
            }
            for f in feedback_stats
        ],
        "stage_performance": [
            {
                "stage": s[0],
                "success_rate": round(float(s[1]) * 100, 2),
                "avg_execution_time": round(float(s[2]), 3) if s[2] else 0
            }
            for s in stage_success
        ]
    }


@app.delete("/api/analysis/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific analysis
    
    Useful for cleaning up test data
    """
    analysis = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    return {"message": "Analysis deleted successfully", "analysis_id": analysis_id}


@app.get("/api/patterns")
def get_bug_patterns():
    """
    Get information about all 10 bug patterns in the taxonomy
    
    Useful for documentation and extension UI
    """
    patterns = [
        {
            "name": "Syntax Error",
            "stage": "static",
            "severity_range": "8-10",
            "description": "Code cannot be parsed due to syntax violations",
            "example": "Missing colons, unmatched parentheses"
        },
        {
            "name": "Hallucinated Object",
            "stage": "static",
            "severity_range": "7-9",
            "description": "Code references non-existent functions, classes, or variables",
            "example": "PriceCalculator() when class doesn't exist"
        },
        {
            "name": "Incomplete Generation",
            "stage": "static",
            "severity_range": "6-8",
            "description": "Code generation was cut off before completion",
            "example": "Functions with only 'pass' or incomplete assignments"
        },
        {
            "name": "Silly Mistake",
            "stage": "static",
            "severity_range": "5-7",
            "description": "Non-human coding patterns like reversed operands",
            "example": "discount - price instead of price - discount"
        },
        {
            "name": "Wrong Attribute",
            "stage": "dynamic",
            "severity_range": "6-8",
            "description": "Attempting to access non-existent object attributes",
            "example": "dict.key instead of dict['key']"
        },
        {
            "name": "Wrong Input Type",
            "stage": "dynamic",
            "severity_range": "5-7",
            "description": "Function called with inappropriate data type",
            "example": "String concatenation with numeric value"
        },
        {
            "name": "Non-Prompted Consideration (NPC)",
            "stage": "linguistic",
            "severity_range": "4-6",
            "description": "Code includes features not requested in prompt",
            "example": "Adding security checks or sorting not asked for"
        },
        {
            "name": "Prompt-Biased Code",
            "stage": "linguistic",
            "severity_range": "5-7",
            "description": "Hardcoded logic based on prompt examples",
            "example": "if item == 'Example_Item_A'"
        },
        {
            "name": "Missing Corner Case",
            "stage": "linguistic",
            "severity_range": "4-6",
            "description": "Code doesn't handle edge cases properly",
            "example": "No None checks, zero division not handled"
        },
        {
            "name": "Misinterpretation",
            "stage": "linguistic",
            "severity_range": "6-9",
            "description": "Code fundamentally misunderstands the task",
            "example": "Returning string when list was requested"
        }
    ]
    
    return {
        "total_patterns": len(patterns),
        "patterns": patterns
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "api_version": "2.0.0",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
