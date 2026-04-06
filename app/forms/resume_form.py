# -*- coding: utf-8 -*-
"""简历录入表单

使用 Flask-WTF 实现简历表单，包含验证规则。
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class ResumeForm(FlaskForm):
    """简历录入表单类"""
    
    education_school = StringField(
        '学校名称',
        validators=[
            DataRequired(message='学校名称不能为空'),
            Length(max=200, message='学校名称不能超过200个字符')
        ],
        render_kw={
            'placeholder': '请输入学校名称',
            'class': 'form-control',
            'maxlength': '200'
        }
    )
    
    education_major = StringField(
        '专业',
        validators=[
            DataRequired(message='专业不能为空'),
            Length(max=100, message='专业不能超过100个字符')
        ],
        render_kw={
            'placeholder': '请输入专业名称',
            'class': 'form-control',
            'maxlength': '100'
        }
    )
    
    internship_company = StringField(
        '公司名称',
        validators=[
            Optional(),
            Length(max=200, message='公司名称不能超过200个字符')
        ],
        render_kw={
            'placeholder': '请输入实习公司名称（选填）',
            'class': 'form-control',
            'maxlength': '200'
        }
    )
    
    internship_position = StringField(
        '职位',
        validators=[
            Optional(),
            Length(max=100, message='职位不能超过100个字符')
        ],
        render_kw={
            'placeholder': '请输入实习职位（选填）',
            'class': 'form-control',
            'maxlength': '100'
        }
    )
    
    internship_content = TextAreaField(
        '工作内容',
        validators=[
            Optional(),
            Length(max=1000, message='工作内容不能超过1000个字符')
        ],
        render_kw={
            'placeholder': '请描述实习工作内容（选填）',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '1000'
        }
    )
    
    work_company = StringField(
        '公司名称',
        validators=[
            Optional(),
            Length(max=200, message='公司名称不能超过200个字符')
        ],
        render_kw={
            'placeholder': '请输入工作公司名称（选填）',
            'class': 'form-control',
            'maxlength': '200'
        }
    )
    
    work_position = StringField(
        '职位',
        validators=[
            Optional(),
            Length(max=100, message='职位不能超过100个字符')
        ],
        render_kw={
            'placeholder': '请输入工作职位（选填）',
            'class': 'form-control',
            'maxlength': '100'
        }
    )
    
    work_content = TextAreaField(
        '工作内容',
        validators=[
            Optional(),
            Length(max=1000, message='工作内容不能超过1000个字符')
        ],
        render_kw={
            'placeholder': '请描述工作内容（选填）',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '1000'
        }
    )
    
    project_name = StringField(
        '项目名称',
        validators=[
            Optional(),
            Length(max=200, message='项目名称不能超过200个字符')
        ],
        render_kw={
            'placeholder': '请输入项目名称（选填）',
            'class': 'form-control',
            'maxlength': '200'
        }
    )
    
    project_content = TextAreaField(
        '项目内容',
        validators=[
            Optional(),
            Length(max=1000, message='项目内容不能超过1000个字符')
        ],
        render_kw={
            'placeholder': '请描述项目内容（选填）',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '1000'
        }
    )
    
    skills = TextAreaField(
        '个人技能',
        validators=[
            DataRequired(message='个人技能不能为空'),
            Length(max=500, message='个人技能不能超过500个字符')
        ],
        render_kw={
            'placeholder': '请输入个人技能，多项技能可用逗号或顿号分隔',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '500'
        }
    )
    
    self_evaluation = TextAreaField(
        '个人评价',
        validators=[
            DataRequired(message='个人评价不能为空'),
            Length(max=500, message='个人评价不能超过500个字符')
        ],
        render_kw={
            'placeholder': '请输入个人评价',
            'class': 'form-control',
            'rows': '4',
            'maxlength': '500'
        }
    )
