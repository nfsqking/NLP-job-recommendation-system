# -*- coding: utf-8 -*-
"""仪表盘路由模块

处理首页、岗位查找等主页面请求。
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Job
from app import db

dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/')
@login_required
def index():
    """仪表盘首页 - 岗位查找页面"""
    return render_template('dashboard.html', user=current_user)


@dashboard.route('/jobs')
@login_required
def job_list():
    """岗位列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    
    query = Job.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Job.job_name.contains(keyword),
                Job.company_name.contains(keyword)
            )
        )
    
    if location:
        query = query.filter(Job.location.contains(location))
    
    pagination = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    jobs = [job.to_dict() for job in pagination.items]
    
    return jsonify({
        'success': True,
        'data': {
            'jobs': jobs,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@dashboard.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    """岗位详情"""
    job = Job.query.get_or_404(job_id)
    return jsonify({
        'success': True,
        'data': job.to_dict()
    })
