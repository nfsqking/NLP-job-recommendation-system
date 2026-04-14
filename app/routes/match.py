# -*- coding: utf-8 -*-
"""简历匹配路由模块

提供简历与岗位的语义相似度匹配功能。
支持多简历独立匹配，每份简历的匹配结果完全隔离。
"""

import json
import numpy as np
from flask import Blueprint, render_template, jsonify, request, session
from flask_login import login_required, current_user
from app import db, get_semantic_model
from app.models import Job, Resume, ResumeJobMatch

match = Blueprint('match', __name__)


def get_current_resume_id():
    """获取当前选中的简历ID"""
    resume_id = session.get('current_resume_id')
    if resume_id:
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if resume:
            return resume_id
    
    active_resume = Resume.query.filter_by(user_id=current_user.id, is_active=True).first()
    if active_resume:
        session['current_resume_id'] = active_resume.id
        return active_resume.id
    
    first_resume = Resume.query.filter_by(user_id=current_user.id).first()
    if first_resume:
        if Resume.query.filter_by(user_id=current_user.id, is_active=True).count() == 0:
            first_resume.is_active = True
            db.session.commit()
        session['current_resume_id'] = first_resume.id
        return first_resume.id
    
    return None


def get_current_resume():
    """获取当前选中的简历对象"""
    resume_id = get_current_resume_id()
    if resume_id:
        return Resume.query.get(resume_id)
    return None


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def calibrate_similarity_score(similarity):
    """
    校准相似度分数，使其更符合实际匹配程度
    
    原始余弦相似度通常在 0.3-0.8 之间，直接乘以100会导致分数偏低
    采用分段线性映射 + 幂函数混合策略进行校准
    
    映射规则：
    - 0.0-0.3: 低相关，映射到 30%-50%
    - 0.3-0.5: 中等相关，映射到 50%-70%
    - 0.5-0.7: 较高相关，映射到 70%-85%
    - 0.7-1.0: 高度相关，映射到 85%-98%
    
    Args:
        similarity: 原始余弦相似度 (0.0-1.0)
        
    Returns:
        校准后的分数 (0-100)
    """
    if similarity < 0:
        similarity = 0
    elif similarity > 1:
        similarity = 1
    
    if similarity < 0.3:
        calibrated = 30 + (similarity / 0.3) * 20
    elif similarity < 0.5:
        calibrated = 50 + ((similarity - 0.3) / 0.2) * 20
    elif similarity < 0.7:
        calibrated = 70 + ((similarity - 0.5) / 0.2) * 15
    else:
        calibrated = 85 + ((similarity - 0.7) / 0.3) * 13
    
    return min(calibrated, 98)


def build_resume_text(resume):
    """构建简历各维度的文本"""
    texts = {}
    
    education_str = ""
    if resume.education_school:
        try:
            edu_list = json.loads(resume.education_school) if resume.education_school.strip().startswith('[') else []
            if isinstance(edu_list, list):
                for edu in edu_list:
                    if isinstance(edu, dict):
                        school = edu.get('school', '')
                        major = edu.get('major', '')
                        if school or major:
                            education_str += f"学校：{school} 专业：{major}；"
            else:
                education_str = str(resume.education_school)
        except:
            education_str = str(resume.education_school)
    if resume.education_major and not education_str:
        try:
            major_list = json.loads(resume.education_major) if resume.education_major.strip().startswith('[') else []
            if isinstance(major_list, list):
                for major in major_list:
                    if isinstance(major, dict):
                        m = major.get('major', '')
                        if m:
                            education_str += f"专业：{m}；"
                    elif isinstance(major, str):
                        education_str += f"专业：{major}；"
        except:
            pass
    if education_str.strip():
        texts['education'] = education_str.strip()
    
    if resume.skills:
        texts['skills'] = str(resume.skills)
    
    if resume.self_evaluation:
        texts['self_evaluation'] = str(resume.self_evaluation)
    
    internship_str = ""
    if resume.internship_content:
        try:
            intern_list = json.loads(resume.internship_content) if resume.internship_content.strip().startswith('[') else []
            if isinstance(intern_list, list):
                for intern in intern_list:
                    if isinstance(intern, dict):
                        company = intern.get('company', '')
                        position = intern.get('position', '')
                        content = intern.get('content', '')
                        if company or position or content:
                            internship_str += f"公司：{company} 职位：{position} 内容：{content}；"
            else:
                internship_str = str(resume.internship_content)
        except:
            internship_str = str(resume.internship_content)
    if internship_str.strip():
        texts['internship'] = internship_str.strip()
    
    work_str = ""
    if resume.work_content:
        try:
            work_list = json.loads(resume.work_content) if resume.work_content.strip().startswith('[') else []
            if isinstance(work_list, list):
                for work in work_list:
                    if isinstance(work, dict):
                        company = work.get('company', '')
                        position = work.get('position', '')
                        content = work.get('content', '')
                        if company or position or content:
                            work_str += f"公司：{company} 职位：{position} 内容：{content}；"
            else:
                work_str = str(resume.work_content)
        except:
            work_str = str(resume.work_content)
    if work_str.strip():
        texts['work'] = work_str.strip()
    
    project_str = ""
    if resume.project_content:
        try:
            proj_list = json.loads(resume.project_content) if resume.project_content.strip().startswith('[') else []
            if isinstance(proj_list, list):
                for proj in proj_list:
                    if isinstance(proj, dict):
                        name = proj.get('name', '')
                        content = proj.get('content', '')
                        if name or content:
                            project_str += f"项目：{name} 内容：{content}；"
            else:
                project_str = str(resume.project_content)
        except:
            project_str = str(resume.project_content)
    if project_str.strip():
        texts['project'] = project_str.strip()
    
    return texts


def calculate_match_score(resume, job_description):
    """
    计算简历与岗位的匹配分数
    
    加权规则：
    - 教育经历: 0.20
    - 个人技能: 0.30
    - 个人评价: 0.20
    - 实习经历: 0.10
    - 工作经历: 0.10
    - 项目经历: 0.10
    """
    weights = {
        'education': 0.20,
        'skills': 0.30,
        'self_evaluation': 0.20,
        'internship': 0.10,
        'work': 0.10,
        'project': 0.10
    }
    
    resume_texts = build_resume_text(resume)
    
    if not resume_texts or not job_description:
        return 0.0
    
    model = get_semantic_model()
    if model is None:
        return 0.0
    
    active_weights = {k: v for k, v in weights.items() if k in resume_texts and resume_texts[k]}
    
    if not active_weights:
        return 0.0
    
    total_weight = sum(active_weights.values())
    if total_weight == 0:
        return 0.0
    
    normalized_weights = {k: v / total_weight for k, v in active_weights.items()}
    
    job_embedding = model.encode([job_description])[0]
    
    total_similarity = 0.0
    for key, weight in normalized_weights.items():
        resume_embedding = model.encode([resume_texts[key]])[0]
        similarity = cosine_similarity(resume_embedding, job_embedding)
        total_similarity += similarity * weight
    
    calibrated_score = calibrate_similarity_score(total_similarity)
    
    return float(calibrated_score)


@match.route('/match')
@login_required
def index():
    """简历匹配页面"""
    model = get_semantic_model()
    model_loaded = model is not None
    
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    
    if not resumes:
        return render_template('match.html', 
                             jobs=[],
                             matched_jobs=[],
                             matched_job_ids=[],
                             has_resume=False,
                             model_loaded=model_loaded,
                             current_resume=None,
                             resumes=[],
                             current_resume_id=None)
    
    current_resume = get_current_resume()
    has_resume = current_resume is not None
    current_resume_id = get_current_resume_id()
    
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    
    existing_matches = []
    matched_job_ids = []
    matched_jobs = []
    
    if current_resume_id:
        existing_matches = ResumeJobMatch.query.filter_by(resume_id=current_resume_id).all()
        matched_job_ids_dict = {m.job_id: m for m in existing_matches}
        
        for m in existing_matches:
            job = Job.query.get(m.job_id)
            if job:
                matched_jobs.append({
                    'match_id': m.id,
                    'job': job,
                    'score': round(m.match_score, 2),
                    'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''
                })
        
        matched_jobs.sort(key=lambda x: x['score'], reverse=True)
        matched_job_ids = list(matched_job_ids_dict.keys())
    
    return render_template('match.html', 
                         jobs=jobs,
                         matched_jobs=matched_jobs,
                         matched_job_ids=matched_job_ids,
                         has_resume=has_resume,
                         model_loaded=model_loaded,
                         current_resume=current_resume,
                         resumes=resumes,
                         current_resume_id=current_resume_id)


@match.route('/api/jobs')
@login_required
def get_jobs():
    """获取岗位列表API"""
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    
    query = Job.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Job.job_name.contains(keyword),
                Job.company_name.contains(keyword),
                Job.job_description.contains(keyword)
            )
        )
    
    if location:
        query = query.filter(Job.location.contains(location))
    
    jobs = query.order_by(Job.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'jobs': [job.to_dict() for job in jobs]
    })


@match.route('/api/match/analyze', methods=['POST'])
@login_required
def analyze_match():
    """执行匹配分析API"""
    model = get_semantic_model()
    if model is None:
        return jsonify({
            'success': False,
            'message': '语义模型未加载，请先下载模型到本地缓存'
        })
    
    current_resume = get_current_resume()
    if not current_resume:
        return jsonify({
            'success': False,
            'message': '请先选择或创建一份简历后再进行匹配'
        })
    
    current_resume_id = get_current_resume_id()
    
    data = request.get_json()
    job_ids = data.get('job_ids', [])
    
    if not job_ids:
        return jsonify({
            'success': False,
            'message': '请选择至少一个岗位进行分析'
        })
    
    results = []
    for job_id in job_ids:
        job = Job.query.get(job_id)
        if not job:
            continue
        
        existing_match = ResumeJobMatch.query.filter_by(
            resume_id=current_resume_id,
            job_id=job_id
        ).first()
        
        if existing_match:
            results.append({
                'job_id': int(job_id),
                'job_name': job.job_name,
                'company_name': job.company_name,
                'match_score': float(round(existing_match.match_score, 2)),
                'match_id': int(existing_match.id),
                'is_new': False
            })
        else:
            score = calculate_match_score(current_resume, job.job_description or '')
            score = float(score)
            
            new_match = ResumeJobMatch(
                user_id=current_user.id,
                resume_id=current_resume_id,
                job_id=job_id,
                match_score=score
            )
            db.session.add(new_match)
            db.session.commit()
            
            results.append({
                'job_id': int(job_id),
                'job_name': job.job_name,
                'company_name': job.company_name,
                'match_score': float(round(score, 2)),
                'match_id': int(new_match.id),
                'is_new': True
            })
    
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        'success': True,
        'message': f'成功分析 {len(results)} 个岗位',
        'results': results
    })


@match.route('/api/match/delete', methods=['POST'])
@login_required
def delete_matches():
    """删除匹配记录API"""
    current_resume_id = get_current_resume_id()
    if not current_resume_id:
        return jsonify({
            'success': False,
            'message': '请先选择简历'
        })
    
    data = request.get_json()
    match_ids = data.get('match_ids', [])
    
    if not match_ids:
        return jsonify({
            'success': False,
            'message': '请选择要删除的记录'
        })
    
    deleted_count = ResumeJobMatch.query.filter(
        ResumeJobMatch.id.in_(match_ids),
        ResumeJobMatch.resume_id == current_resume_id
    ).delete(synchronize_session='fetch')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'成功删除 {deleted_count} 条记录'
    })


@match.route('/api/match/clear', methods=['POST'])
@login_required
def clear_matches():
    """清空当前简历的所有匹配记录API"""
    current_resume_id = get_current_resume_id()
    if not current_resume_id:
        return jsonify({
            'success': False,
            'message': '请先选择简历'
        })
    
    deleted_count = ResumeJobMatch.query.filter_by(
        resume_id=current_resume_id
    ).delete()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'成功清空 {deleted_count} 条记录'
    })


@match.route('/api/match/list')
@login_required
def get_match_list():
    """获取当前简历的匹配结果列表API"""
    current_resume_id = get_current_resume_id()
    if not current_resume_id:
        return jsonify({
            'success': True,
            'matches': []
        })
    
    matches = ResumeJobMatch.query.filter_by(resume_id=current_resume_id).all()
    
    results = []
    for m in matches:
        job = Job.query.get(m.job_id)
        if job:
            results.append({
                'match_id': int(m.id),
                'job_id': int(m.job_id),
                'job_name': job.job_name,
                'company_name': job.company_name,
                'job_salary': job.job_salary,
                'location': job.location,
                'experience': job.experience,
                'education': job.education,
                'job_description': job.job_description,
                'match_score': float(round(m.match_score, 2)),
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''
            })
    
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        'success': True,
        'matches': results
    })


@match.route('/api/resume/switch', methods=['POST'])
@login_required
def switch_resume():
    """切换当前简历API"""
    data = request.get_json()
    resume_id = data.get('resume_id')
    
    if not resume_id:
        return jsonify({
            'success': False,
            'message': '请提供简历ID'
        })
    
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    if not resume:
        return jsonify({
            'success': False,
            'message': '简历不存在'
        })
    
    Resume.query.filter_by(user_id=current_user.id).update({'is_active': False})
    resume.is_active = True
    db.session.commit()
    
    session['current_resume_id'] = resume_id
    
    return jsonify({
        'success': True,
        'message': '已切换简历',
        'resume': resume.to_dict()
    })
