# -*- coding: utf-8 -*-
"""个性化技能提升路由模块

提供技能提升建议生成和展示功能。
"""

import json
import requests
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Job, Resume, ResumeJobMatch, SkillSuggestion

skill_improvement = Blueprint('skill_improvement', __name__)


def build_resume_summary(resume):
    """构建简历摘要文本"""
    summary_parts = []
    
    if resume.education_school:
        try:
            edu_list = json.loads(resume.education_school) if resume.education_school.strip().startswith('[') else []
            if isinstance(edu_list, list) and edu_list:
                edu_text = "教育经历："
                for edu in edu_list:
                    if isinstance(edu, dict):
                        school = edu.get('school', '')
                        major = edu.get('major', '')
                        edu_text += f"{school} {major}；"
                summary_parts.append(edu_text)
        except:
            pass
    
    if resume.skills:
        summary_parts.append(f"个人技能：{resume.skills}")
    
    if resume.self_evaluation:
        summary_parts.append(f"自我评价：{resume.self_evaluation}")
    
    if resume.internship_content:
        try:
            intern_list = json.loads(resume.internship_content) if resume.internship_content.strip().startswith('[') else []
            if isinstance(intern_list, list) and intern_list:
                intern_text = "实习经历："
                for intern in intern_list:
                    if isinstance(intern, dict):
                        company = intern.get('company', '')
                        position = intern.get('position', '')
                        content = intern.get('content', '')
                        intern_text += f"{company} {position} {content}；"
                summary_parts.append(intern_text)
        except:
            pass
    
    if resume.work_content:
        try:
            work_list = json.loads(resume.work_content) if resume.work_content.strip().startswith('[') else []
            if isinstance(work_list, list) and work_list:
                work_text = "工作经历："
                for work in work_list:
                    if isinstance(work, dict):
                        company = work.get('company', '')
                        position = work.get('position', '')
                        content = work.get('content', '')
                        work_text += f"{company} {position} {content}；"
                summary_parts.append(work_text)
        except:
            pass
    
    if resume.project_content:
        try:
            proj_list = json.loads(resume.project_content) if resume.project_content.strip().startswith('[') else []
            if isinstance(proj_list, list) and proj_list:
                proj_text = "项目经历："
                for proj in proj_list:
                    if isinstance(proj, dict):
                        name = proj.get('name', '')
                        content = proj.get('content', '')
                        proj_text += f"{name} {content}；"
                summary_parts.append(proj_text)
        except:
            pass
    
    return "\n".join(summary_parts)


def call_glm4_api(api_key, resume_summary, job_description):
    """调用GLM-4 API生成技能提升建议"""
    url = "https://open.bigmodel.cn/api/v1/agents"
    
    prompt = f"""你是一位专业的职业发展顾问。请根据以下简历信息和目标岗位描述，为求职者提供具体、可行、有针对性的技能提升建议。

【求职者简历信息】
{resume_summary}

【目标岗位描述】
{job_description}

请从以下几个方面给出详细的技能提升建议：
1. 技能差距分析：分析求职者当前技能与岗位要求的差距
2. 学习路径建议：给出具体的学习步骤和资源推荐
3. 项目实践建议：推荐可以提升相关技能的实际项目
4. 证书/认证建议：推荐相关的职业资格证书
5. 时间规划建议：给出合理的学习时间安排

请用清晰的格式输出，每个部分用标题分隔。"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "agent_id": "general_agent",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "custom_variables": {}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        elif 'data' in result and 'choices' in result['data'] and len(result['data']['choices']) > 0:
            return result['data']['choices'][0]['message']['content']
        else:
            print(f"GLM-4 API返回格式异常: {result}")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"GLM-4 API HTTP错误: {e}")
        try:
            error_detail = e.response.json()
            print(f"错误详情: {error_detail}")
        except:
            pass
        return None
    except Exception as e:
        print(f"GLM-4 API调用失败: {e}")
        return None


@skill_improvement.route('/skill_improvement')
@login_required
def index():
    """个性化技能提升页面"""
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    has_resume = resume is not None
    
    matches = ResumeJobMatch.query.filter_by(user_id=current_user.id).all()
    matched_jobs = []
    
    for m in matches:
        job = Job.query.get(m.job_id)
        if job:
            existing_suggestion = SkillSuggestion.query.filter_by(
                user_id=current_user.id,
                job_id=job.id
            ).first()
            
            matched_jobs.append({
                'match_id': m.id,
                'job': job,
                'match_score': round(m.match_score, 2),
                'has_suggestion': existing_suggestion is not None,
                'suggestion_id': existing_suggestion.id if existing_suggestion else None
            })
    
    matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    return render_template('skill_improvement.html',
                         matched_jobs=matched_jobs,
                         has_resume=has_resume)


@skill_improvement.route('/api/suggestion/generate', methods=['POST'])
@login_required
def generate_suggestion():
    """生成技能提升建议API"""
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    if not resume:
        return jsonify({
            'success': False,
            'message': '请先录入简历'
        })
    
    data = request.get_json()
    job_id = data.get('job_id')
    api_key = data.get('api_key', '').strip()
    
    if not job_id:
        return jsonify({
            'success': False,
            'message': '请选择岗位'
        })
    
    if not api_key:
        return jsonify({
            'success': False,
            'message': '请输入API_KEY'
        })
    
    job = Job.query.get(job_id)
    if not job:
        return jsonify({
            'success': False,
            'message': '岗位不存在'
        })
    
    existing_suggestion = SkillSuggestion.query.filter_by(
        user_id=current_user.id,
        job_id=job_id
    ).first()
    
    if existing_suggestion:
        return jsonify({
            'success': True,
            'message': '该岗位已有提升建议',
            'suggestion_id': existing_suggestion.id,
            'suggestion': existing_suggestion.suggestion,
            'is_new': False
        })
    
    resume_summary = build_resume_summary(resume)
    job_description = job.job_description or f"{job.job_name} {job.experience} {job.education}"
    
    suggestion_text = call_glm4_api(api_key, resume_summary, job_description)
    
    if not suggestion_text:
        return jsonify({
            'success': False,
            'message': 'GLM-4 API调用失败，请检查API_KEY是否正确'
        })
    
    resume_snapshot = json.dumps({
        'education_school': resume.education_school,
        'skills': resume.skills,
        'self_evaluation': resume.self_evaluation,
        'internship_content': resume.internship_content,
        'work_content': resume.work_content,
        'project_content': resume.project_content
    }, ensure_ascii=False)
    
    job_snapshot = json.dumps({
        'job_name': job.job_name,
        'company_name': job.company_name,
        'job_description': job.job_description,
        'experience': job.experience,
        'education': job.education
    }, ensure_ascii=False)
    
    new_suggestion = SkillSuggestion(
        user_id=current_user.id,
        job_id=job_id,
        resume_snapshot=resume_snapshot,
        job_snapshot=job_snapshot,
        suggestion=suggestion_text
    )
    
    db.session.add(new_suggestion)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '技能提升建议生成成功',
        'suggestion_id': new_suggestion.id,
        'suggestion': suggestion_text,
        'is_new': True
    })


@skill_improvement.route('/api/suggestion/get')
@login_required
def get_suggestion():
    """获取技能提升建议API"""
    job_id = request.args.get('job_id', type=int)
    
    if not job_id:
        return jsonify({
            'success': False,
            'message': '请提供岗位ID'
        })
    
    suggestion = SkillSuggestion.query.filter_by(
        user_id=current_user.id,
        job_id=job_id
    ).first()
    
    if not suggestion:
        return jsonify({
            'success': False,
            'message': '未找到该岗位的提升建议'
        })
    
    job = Job.query.get(job_id)
    
    return jsonify({
        'success': True,
        'suggestion': {
            'id': suggestion.id,
            'suggestion_text': suggestion.suggestion,
            'job_name': job.job_name if job else '',
            'company_name': job.company_name if job else '',
            'created_at': suggestion.created_at.strftime('%Y-%m-%d %H:%M') if suggestion.created_at else ''
        }
    })


@skill_improvement.route('/api/suggestion/list')
@login_required
def list_suggestions():
    """获取所有技能提升建议列表API"""
    suggestions = SkillSuggestion.query.filter_by(user_id=current_user.id).all()
    
    result = []
    for s in suggestions:
        job = Job.query.get(s.job_id)
        if job:
            result.append({
                'id': s.id,
                'job_id': s.job_id,
                'job_name': job.job_name,
                'company_name': job.company_name,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else ''
            })
    
    return jsonify({
        'success': True,
        'suggestions': result
    })
