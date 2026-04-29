# -*- coding: utf-8 -*-
"""简历数据模型

定义简历表结构，与用户表建立一对多关联。
支持用户创建最多3份独立简历。
"""

from datetime import datetime
from app import db


class Resume(db.Model):
    """简历模型类 - 与用户一对多关联"""
    
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    resume_name = db.Column(db.String(100), nullable=False, default='默认简历')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    education = db.Column(db.Text, nullable=True)
    internship = db.Column(db.Text, nullable=True)
    work = db.Column(db.Text, nullable=True)
    project = db.Column(db.Text, nullable=True)
    
    skills = db.Column(db.Text, nullable=False)
    self_evaluation = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('resumes', lazy='dynamic', cascade='all, delete-orphan'))
    
    job_matches = db.relationship('ResumeJobMatch', backref='resume', lazy='dynamic', cascade='all, delete-orphan')
    skill_suggestions = db.relationship('SkillSuggestion', backref='resume', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resume_name': self.resume_name,
            'is_active': self.is_active,
            'education': self.education,
            'internship': self.internship,
            'work': self.work,
            'project': self.project,
            'skills': self.skills,
            'self_evaluation': self.self_evaluation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Resume id={self.id} user_id={self.user_id} name={self.resume_name}>'
