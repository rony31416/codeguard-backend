from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CodeAnalysisRequest(BaseModel):
    prompt: str
    code: str

class BugPatternSchema(BaseModel):
    pattern_name: str
    severity: int
    confidence: float
    description: str
    location: Optional[str] = None
    fix_suggestion: str
    bug_type: Optional[str] = None

    class Config:
        from_attributes = True

class ExecutionLogSchema(BaseModel):
    stage: str
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    execution_time: Optional[float] = None

    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    analysis_id: int
    bug_patterns: List[BugPatternSchema]
    execution_logs: List[ExecutionLogSchema]
    overall_severity: int
    has_bugs: bool
    summary: str
    created_at: datetime
    status: Optional[str] = None  # "processing" = linguistic pending, "complete" = done

    class Config:
        from_attributes = True

class FeedbackRequest(BaseModel):
    analysis_id: int
    rating: int  # 1-5 stars
    comment: Optional[str] = None
    is_helpful: bool
