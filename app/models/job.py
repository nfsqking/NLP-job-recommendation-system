# -*- coding: utf-8 -*-
"""岗位数据模型

定义岗位信息表结构。
"""

from datetime import datetime
from app import db


class Job(db.Model):
    """岗位信息模型类"""
    
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    job_name = db.Column(db.String(200), nullable=False)
    job_salary = db.Column(db.String(50))
    location = db.Column(db.String(100))
    experience = db.Column(db.String(50))
    education = db.Column(db.String(50))
    job_description = db.Column(db.Text)
    company_name = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    company_type = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    detail_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'job_salary': self.job_salary,
            'location': self.location,
            'experience': self.experience,
            'education': self.education,
            'job_description': self.job_description,
            'company_name': self.company_name,
            'industry': self.industry,
            'company_type': self.company_type,
            'company_size': self.company_size,
            'detail_url': self.detail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Job {self.job_name} - {self.company_name}>'
