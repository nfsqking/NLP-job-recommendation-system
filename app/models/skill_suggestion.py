# -*- coding: utf-8 -*-
"""技能提升建议数据模型

保存用户个性化技能提升建议。
通过 resume_id 与具体简历关联，支持多简历独立建议。
"""

from datetime import datetime
from app import db


class SkillSuggestion(db.Model):
    """技能提升建议模型"""
    
    __tablename__ = 'skill_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    resume_snapshot = db.Column(db.Text, nullable=True)
    job_snapshot = db.Column(db.Text, nullable=True)
    suggestion = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('skill_suggestions', lazy='dynamic'))
    job = db.relationship('Job', backref=db.backref('skill_suggestions', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('resume_id', 'job_id', name='unique_resume_job_suggestion'),
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resume_id': self.resume_id,
            'job_id': self.job_id,
            'resume_snapshot': self.resume_snapshot,
            'job_snapshot': self.job_snapshot,
            'suggestion': self.suggestion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<SkillSuggestion resume={self.resume_id} job={self.job_id}>'
