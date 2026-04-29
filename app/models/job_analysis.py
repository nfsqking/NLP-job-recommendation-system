# -*- coding: utf-8 -*-
"""岗位深度分析模型

存储岗位相关的评分维度（每个岗位单独分析）：
- 技能匹配（20分）
- 项目经验（40分）
- 总分（100分）
"""

from datetime import datetime
from app import db


class JobAnalysis(db.Model):
    """岗位深度分析模型"""
    
    __tablename__ = 'job_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    
    skill_match_score = db.Column(db.Integer, nullable=False, default=0)
    skill_match_comment = db.Column(db.Text, nullable=True)
    
    project_experience_score = db.Column(db.Integer, nullable=False, default=0)
    project_experience_comment = db.Column(db.Text, nullable=True)
    
    total_score = db.Column(db.Integer, nullable=False, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    resume = db.relationship('Resume', backref=db.backref('job_analyses', lazy='dynamic', cascade='all, delete-orphan'))
    job = db.relationship('Job', backref=db.backref('analyses', lazy='dynamic', cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.UniqueConstraint('resume_id', 'job_id', name='unique_resume_job_analysis'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'job_id': self.job_id,
            'skill_match_score': self.skill_match_score,
            'skill_match_comment': self.skill_match_comment,
            'project_experience_score': self.project_experience_score,
            'project_experience_comment': self.project_experience_comment,
            'total_score': self.total_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<JobAnalysis resume_id={self.resume_id} job_id={self.job_id}>'
