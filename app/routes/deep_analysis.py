# -*- coding: utf-8 -*-
"""简历-岗位深度分析路由模块

提供深度分析功能，包含5个维度的评分：
- 表达专业性（10分）- 简历固有
- 技能匹配（20分）- 岗位相关
- 内容完整性（15分）- 简历固有
- 结构清晰度（15分）- 简历固有
- 项目经验（40分）- 岗位相关
"""

import json
from flask import Blueprint, render_template, jsonify, request, current_app, session
from flask_login import login_required, current_user
from app import db
from app.models import Job, Resume, ResumeScore, JobAnalysis
from zai import ZhipuAiClient

deep_analysis = Blueprint('deep_analysis', __name__)


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


def build_resume_text(resume):
    """构建简历完整文本"""
    parts = []
    
    if resume.education:
        try:
            edu_list = json.loads(resume.education) if resume.education.strip().startswith('[') else []
            if isinstance(edu_list, list) and edu_list:
                edu_text = "教育经历："
                for edu in edu_list:
                    if isinstance(edu, dict):
                        school = edu.get('school', '')
                        major = edu.get('major', '')
                        edu_text += f"{school} {major}；"
                parts.append(edu_text)
        except:
            pass
    
    if resume.skills:
        parts.append(f"个人技能：{resume.skills}")
    
    if resume.self_evaluation:
        parts.append(f"自我评价：{resume.self_evaluation}")
    
    if resume.internship:
        try:
            intern_list = json.loads(resume.internship) if resume.internship.strip().startswith('[') else []
            if isinstance(intern_list, list) and intern_list:
                intern_text = "实习经历："
                for intern in intern_list:
                    if isinstance(intern, dict):
                        company = intern.get('company', '')
                        position = intern.get('position', '')
                        content = intern.get('content', '')
                        intern_text += f"{company} {position} {content}；"
                parts.append(intern_text)
        except:
            pass
    
    if resume.work:
        try:
            work_list = json.loads(resume.work) if resume.work.strip().startswith('[') else []
            if isinstance(work_list, list) and work_list:
                work_text = "工作经历："
                for work in work_list:
                    if isinstance(work, dict):
                        company = work.get('company', '')
                        position = work.get('position', '')
                        content = work.get('content', '')
                        work_text += f"{company} {position} {content}；"
                parts.append(work_text)
        except:
            pass
    
    if resume.project:
        try:
            proj_list = json.loads(resume.project) if resume.project.strip().startswith('[') else []
            if isinstance(proj_list, list) and proj_list:
                proj_text = "项目经历："
                for proj in proj_list:
                    if isinstance(proj, dict):
                        name = proj.get('name', '')
                        content = proj.get('content', '')
                        proj_text += f"{name} {content}；"
                parts.append(proj_text)
        except:
            pass
    
    return "\n".join(parts)


def analyze_resume_intrinsic(resume_text, api_key):
    """分析简历固有三项维度（表达专业性、内容完整性、结构清晰度）"""
    
    prompt = f"""你是专业简历分析师，请对以下简历进行三个维度的评分分析。

评分维度及满分：
1. 表达专业性（满分10分）：评估简历的语言表达是否专业、准确、得体
2. 内容完整性（满分15分）：评估简历内容是否完整、信息是否全面
3. 结构清晰度（满分15分）：评估简历结构是否清晰、逻辑是否合理

=== 简历内容 ===
{resume_text}

请严格按照以下JSON格式输出，不要输出任何其他内容：
{{
    "expression_score": <1-10的整数>,
    "expression_comment": "<评价说明>",
    "completeness_score": <1-15的整数>,
    "completeness_comment": "<评价说明>",
    "structure_score": <1-15的整数>,
    "structure_comment": "<评价说明>"
}}
"""
    
    try:
        client = ZhipuAiClient(api_key=api_key)
        
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "user", "content": prompt}
            ],
            thinking={
                "type": "disabled",
            },
            max_tokens=2048,
            temperature=0.3
        )
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith('```'):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            result = json.loads(content)
            return {
                'success': True,
                'data': {
                    'expression_score': int(result.get('expression_score', 0)),
                    'expression_comment': result.get('expression_comment', ''),
                    'completeness_score': int(result.get('completeness_score', 0)),
                    'completeness_comment': result.get('completeness_comment', ''),
                    'structure_score': int(result.get('structure_score', 0)),
                    'structure_comment': result.get('structure_comment', '')
                }
            }
        else:
            return {'success': False, 'message': 'GLM返回格式异常'}
            
    except json.JSONDecodeError as e:
        return {'success': False, 'message': f'JSON解析失败: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': f'GLM调用失败: {str(e)}'}


def analyze_job_related(resume_text, job_description, api_key):
    """分析岗位相关两项维度（技能匹配、项目经验）"""
    
    prompt = f"""你是专业简历分析师，请根据简历内容和岗位描述，进行两个维度的评分分析。

评分维度及满分：
1. 技能匹配（满分20分）：评估简历中的技能与岗位要求的匹配程度
2. 项目经验（满分40分）：评估简历中的项目经验与岗位要求的契合程度

=== 简历内容 ===
{resume_text}

=== 岗位描述 ===
{job_description}

请严格按照以下JSON格式输出，不要输出任何其他内容：
{{
    "skill_match_score": <1-20的整数>,
    "skill_match_comment": "<评价说明>",
    "project_experience_score": <1-40的整数>,
    "project_experience_comment": "<评价说明>"
}}
"""
    
    try:
        client = ZhipuAiClient(api_key=api_key)
        
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "user", "content": prompt}
            ],
            thinking={
                "type": "disabled",
            },
            max_tokens=2048,
            temperature=0.3
        )
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith('```'):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            result = json.loads(content)
            return {
                'success': True,
                'data': {
                    'skill_match_score': int(result.get('skill_match_score', 0)),
                    'skill_match_comment': result.get('skill_match_comment', ''),
                    'project_experience_score': int(result.get('project_experience_score', 0)),
                    'project_experience_comment': result.get('project_experience_comment', '')
                }
            }
        else:
            return {'success': False, 'message': 'GLM返回格式异常'}
            
    except json.JSONDecodeError as e:
        return {'success': False, 'message': f'JSON解析失败: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': f'GLM调用失败: {str(e)}'}


@deep_analysis.route('/')
@login_required
def index():
    """深度分析结果列表页面"""
    resume = get_current_resume()
    if not resume:
        return render_template('deep_analysis.html', has_resume=False)
    
    analyses = JobAnalysis.query.filter_by(resume_id=resume.id).order_by(JobAnalysis.created_at.desc()).all()
    
    analysis_list = []
    for analysis in analyses:
        job = Job.query.get(analysis.job_id)
        if job:
            resume_score = ResumeScore.query.filter_by(resume_id=resume.id).first()
            analysis_list.append({
                'analysis': analysis,
                'job': job,
                'resume_score': resume_score
            })
    
    return render_template('deep_analysis.html', 
                          has_resume=True, 
                          resume=resume,
                          analysis_list=analysis_list)


@deep_analysis.route('/result/<int:job_id>')
@login_required
def result(job_id):
    """深度分析详情页面"""
    resume = get_current_resume()
    if not resume:
        return render_template('deep_analysis_result.html', has_resume=False)
    
    job = Job.query.get(job_id)
    if not job:
        return render_template('deep_analysis_result.html', has_resume=False, error='岗位不存在')
    
    analysis = JobAnalysis.query.filter_by(resume_id=resume.id, job_id=job_id).first()
    if not analysis:
        return render_template('deep_analysis_result.html', has_resume=False, error='未找到分析结果')
    
    resume_score = ResumeScore.query.filter_by(resume_id=resume.id).first()
    
    return render_template('deep_analysis_result.html',
                          has_resume=True,
                          resume=resume,
                          job=job,
                          analysis=analysis,
                          resume_score=resume_score)


@deep_analysis.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    """执行深度分析API"""
    resume = get_current_resume()
    if not resume:
        return jsonify({'success': False, 'message': '请先创建简历'})
    
    data = request.get_json()
    job_id = data.get('job_id')
    
    if not job_id:
        return jsonify({'success': False, 'message': '缺少岗位ID'})
    
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'success': False, 'message': '岗位不存在'})
    
    existing_analysis = JobAnalysis.query.filter_by(resume_id=resume.id, job_id=job_id).first()
    if existing_analysis:
        resume_score = ResumeScore.query.filter_by(resume_id=resume.id).first()
        return jsonify({
            'success': True,
            'message': '该岗位已分析过',
            'data': {
                'analysis': existing_analysis.to_dict(),
                'resume_score': resume_score.to_dict() if resume_score else None
            }
        })
    
    api_key = current_app.config.get('ZHIPU_API_KEY')
    if not api_key:
        return jsonify({'success': False, 'message': '未配置GLM API Key'})
    
    resume_text = build_resume_text(resume)
    job_description = job.job_description or f"{job.job_name} - {job.company_name}"
    
    resume_score = ResumeScore.query.filter_by(resume_id=resume.id).first()
    if not resume_score:
        intrinsic_result = analyze_resume_intrinsic(resume_text, api_key)
        if not intrinsic_result['success']:
            return jsonify({'success': False, 'message': f"简历分析失败: {intrinsic_result['message']}"})
        
        score_data = intrinsic_result['data']
        resume_score = ResumeScore(
            resume_id=resume.id,
            expression_score=score_data['expression_score'],
            expression_comment=score_data['expression_comment'],
            completeness_score=score_data['completeness_score'],
            completeness_comment=score_data['completeness_comment'],
            structure_score=score_data['structure_score'],
            structure_comment=score_data['structure_comment']
        )
        db.session.add(resume_score)
        db.session.commit()
    
    job_result = analyze_job_related(resume_text, job_description, api_key)
    if not job_result['success']:
        return jsonify({'success': False, 'message': f"岗位分析失败: {job_result['message']}"})
    
    job_data = job_result['data']
    total_score = (resume_score.expression_score + 
                   resume_score.completeness_score + 
                   resume_score.structure_score +
                   job_data['skill_match_score'] + 
                   job_data['project_experience_score'])
    
    job_analysis = JobAnalysis(
        resume_id=resume.id,
        job_id=job_id,
        skill_match_score=job_data['skill_match_score'],
        skill_match_comment=job_data['skill_match_comment'],
        project_experience_score=job_data['project_experience_score'],
        project_experience_comment=job_data['project_experience_comment'],
        total_score=total_score
    )
    db.session.add(job_analysis)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '分析完成',
        'data': {
            'analysis': job_analysis.to_dict(),
            'resume_score': resume_score.to_dict()
        }
    })


@deep_analysis.route('/api/check/<int:job_id>')
@login_required
def api_check(job_id):
    """检查岗位是否已分析"""
    resume = get_current_resume()
    if not resume:
        return jsonify({'success': False, 'analyzed': False})
    
    analysis = JobAnalysis.query.filter_by(resume_id=resume.id, job_id=job_id).first()
    
    return jsonify({
        'success': True,
        'analyzed': analysis is not None,
        'analysis_id': analysis.id if analysis else None
    })


@deep_analysis.route('/api/list')
@login_required
def api_list():
    """获取已分析的岗位列表"""
    resume = get_current_resume()
    if not resume:
        return jsonify({'success': False, 'analyses': []})
    
    analyses = JobAnalysis.query.filter_by(resume_id=resume.id).order_by(JobAnalysis.created_at.desc()).all()
    
    result = []
    for analysis in analyses:
        job = Job.query.get(analysis.job_id)
        if job:
            result.append({
                'analysis_id': analysis.id,
                'job_id': job.id,
                'job_name': job.job_name,
                'company_name': job.company_name,
                'total_score': analysis.total_score,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M') if analysis.created_at else ''
            })
    
    return jsonify({'success': True, 'analyses': result})
