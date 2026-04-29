# -*- coding: utf-8 -*-
"""简历固有三项分数模型

存储简历的固有评分维度（只需分析一次）：
- 表达专业性（10分）
- 内容完整性（15分）
- 结构清晰度（15分）
"""

from datetime import datetime
from app import db


class ResumeScore(db.Model):
    """简历固有三项分数模型"""
    
    __tablename__ = 'resume_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False, unique=True, index=True)
    
    expression_score = db.Column(db.Integer, nullable=False, default=0)
    expression_comment = db.Column(db.Text, nullable=True)
    
    completeness_score = db.Column(db.Integer, nullable=False, default=0)
    completeness_comment = db.Column(db.Text, nullable=True)
    
    structure_score = db.Column(db.Integer, nullable=False, default=0)
    structure_comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    resume = db.relationship('Resume', backref=db.backref('score', uselist=False, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'expression_score': self.expression_score,
            'expression_comment': self.expression_comment,
            'completeness_score': self.completeness_score,
            'completeness_comment': self.completeness_comment,
            'structure_score': self.structure_score,
            'structure_comment': self.structure_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ResumeScore resume_id={self.resume_id}>'
