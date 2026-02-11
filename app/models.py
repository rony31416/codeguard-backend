from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Analysis(Base):
    __tablename__ = "analyses"
    
    analysis_id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(50), default='python')
    overall_severity = Column(Integer, nullable=False)
    has_bugs = Column(Boolean, nullable=False)
    summary = Column(Text)
    confidence_score = Column(Float)
    prompt_keywords = Column(Text)  # NEW: For linguistic analysis
    code_features = Column(Text)    # NEW: For linguistic analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bug_patterns = relationship("BugPattern", back_populates="analysis", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="analysis", cascade="all, delete-orphan")
    linguistic_analysis = relationship("LinguisticAnalysis", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class BugPattern(Base):
    __tablename__ = "bug_patterns"
    
    bug_pattern_id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.analysis_id'), nullable=False)
    pattern_name = Column(String(100), nullable=False)
    severity = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255))
    fix_suggestion = Column(Text, nullable=False)
    detection_stage = Column(String(50))  # 'static', 'dynamic', 'linguistic'
    
    # Relationship
    analysis = relationship("Analysis", back_populates="bug_patterns")


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.analysis_id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    is_helpful = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="feedbacks")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.analysis_id'), nullable=False)
    stage = Column(String(50), nullable=False)  # 'static', 'dynamic', 'linguistic', 'classification'
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    error_type = Column(String(100))
    traceback = Column(Text)
    execution_time = Column(Float)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="execution_logs")


class LinguisticAnalysis(Base):
    """NEW: Stores Stage 3 linguistic analysis results"""
    __tablename__ = "linguistic_analyses"
    
    linguistic_id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.analysis_id'), nullable=False)
    prompt_intent = Column(Text)
    code_intent = Column(Text)
    intent_match_score = Column(Float)
    unprompted_features = Column(Text)  # JSON list of NPC features
    missing_features = Column(Text)      # JSON list of missing features
    hardcoded_values = Column(Text)      # JSON list of prompt-biased values
    
    # Relationship
    analysis = relationship("Analysis", back_populates="linguistic_analysis")
