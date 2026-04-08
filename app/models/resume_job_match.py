# -*- coding: utf-8 -*-
"""简历-岗位匹配结果模型

存储用户简历与岗位的匹配分析结果。
"""

from datetime import datetime
from app import db


class ResumeJobMatch(db.Model):
    """简历-岗位匹配结果模型"""
    
    __tablename__ = 'resume_job_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    match_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('job_matches', lazy='dynamic'))
    job = db.relationship('Job', backref=db.backref('matches', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='unique_user_job_match'),
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'match_score': self.match_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ResumeJobMatch user_id={self.user_id} job_id={self.job_id} score={self.match_score}>'
