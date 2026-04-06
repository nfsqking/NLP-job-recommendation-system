# -*- coding: utf-8 -*-
"""简历数据模型

定义简历表结构，与用户表建立一对一关联。
"""

from datetime import datetime
from app import db


class Resume(db.Model):
    """简历模型类 - 与用户一对一关联"""
    
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    education_school = db.Column(db.Text, nullable=True)
    education_major = db.Column(db.Text, nullable=True)
    
    internship_company = db.Column(db.Text, nullable=True)
    internship_position = db.Column(db.Text, nullable=True)
    internship_content = db.Column(db.Text, nullable=True)
    
    work_company = db.Column(db.Text, nullable=True)
    work_position = db.Column(db.Text, nullable=True)
    work_content = db.Column(db.Text, nullable=True)
    
    project_name = db.Column(db.Text, nullable=True)
    project_content = db.Column(db.Text, nullable=True)
    
    skills = db.Column(db.Text, nullable=False)
    self_evaluation = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('resume', uselist=False, lazy=True))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'education_school': self.education_school,
            'education_major': self.education_major,
            'internship_company': self.internship_company,
            'internship_position': self.internship_position,
            'internship_content': self.internship_content,
            'work_company': self.work_company,
            'work_position': self.work_position,
            'work_content': self.work_content,
            'project_name': self.project_name,
            'project_content': self.project_content,
            'skills': self.skills,
            'self_evaluation': self.self_evaluation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Resume user_id={self.user_id}>'
