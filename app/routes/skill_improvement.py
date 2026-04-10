# -*- coding: utf-8 -*-
"""个性化技能提升路由模块

提供技能提升建议生成和展示功能。
"""

import json
from flask import Blueprint, render_template, jsonify, request, current_app, Response, stream_with_context
from flask_login import login_required, current_user
from app import db
from app.models import Job, Resume, ResumeJobMatch, SkillSuggestion
from zai import ZhipuAiClient

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
    """调用GLM-4.7 API生成技能提升建议"""
    
    prompt = f"""你是职业技能规划师，请根据以下用户简历与目标岗位描述，分析能力差距，生成具体、可执行、分阶段的个性化技能提升建议，包含：
1. 核心差距技能（3-5项）
2. 每项技能的提升路径（学习资源、练习方法、时间规划）
3. 优先级与落地建议

=== 用户简历 ===
{resume_summary}

=== 目标岗位描述 ===
{job_description}
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
            max_tokens=65536,
            temperature=1.0
        )
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            print(f"GLM-4.7 API返回格式异常: {response}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        print(f"GLM-4.7 API调用失败: {error_msg}")
        
        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
            print("API_KEY错误或无效")
        elif "timeout" in error_msg.lower():
            print("请求超时")
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            print("网络连接错误")
        else:
            print(f"其他错误: {error_msg}")
        
        return None


def stream_glm4_api(api_key, resume_summary, job_description):
    """流式调用GLM-4.7 API生成技能提升建议"""
    
    prompt = f"""你是职业技能规划师，请根据以下用户简历与目标岗位描述，分析能力差距，生成具体、可执行、分阶段的个性化技能提升建议，包含：
1. 核心差距技能（3-5项）
2. 每项技能的提升路径（学习资源、练习方法、时间规划）
3. 优先级与落地建议

=== 用户简历 ===
{resume_summary}

=== 目标岗位描述 ===
{job_description}
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
            max_tokens=65536,
            temperature=1.0,
            stream=True
        )
        
        for chunk in response:
            if chunk and hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0]
                if hasattr(delta, 'delta') and hasattr(delta.delta, 'content'):
                    content = delta.delta.content
                    if content:
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"
            
    except Exception as e:
        error_msg = str(e)
        print(f"GLM-4.7 API流式调用失败: {error_msg}")
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"


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
    
    if not job_id:
        return jsonify({
            'success': False,
            'message': '请选择岗位'
        })
    
    api_key = current_app.config.get('ZHIPU_API_KEY', '')
    if not api_key:
        return jsonify({
            'success': False,
            'message': '系统未配置API_KEY，请联系管理员'
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


@skill_improvement.route('/api/suggestion/stream', methods=['POST'])
@login_required
def stream_suggestion():
    """流式生成技能提升建议API"""
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    if not resume:
        return jsonify({
            'success': False,
            'message': '请先录入简历'
        })
    
    data = request.get_json()
    job_id = data.get('job_id')
    
    if not job_id:
        return jsonify({
            'success': False,
            'message': '请选择岗位'
        })
    
    api_key = current_app.config.get('ZHIPU_API_KEY', '')
    if not api_key:
        return jsonify({
            'success': False,
            'message': '系统未配置API_KEY，请联系管理员'
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
        def return_existing():
            yield f"data: {json.dumps({'existing': True, 'suggestion': existing_suggestion.suggestion}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return Response(stream_with_context(return_existing()), 
                       mimetype='text/event-stream',
                       headers={
                           'Cache-Control': 'no-cache',
                           'X-Accel-Buffering': 'no'
                       })
    
    resume_summary = build_resume_summary(resume)
    job_description = job.job_description or f"{job.job_name} {job.experience} {job.education}"
    
    full_content = []
    
    def generate():
        nonlocal full_content
        try:
            for chunk in stream_glm4_api(api_key, resume_summary, job_description):
                if chunk.startswith("data: [DONE]"):
                    if full_content:
                        suggestion_text = ''.join(full_content)
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
                    yield chunk
                elif chunk.startswith("data: "):
                    try:
                        data_str = chunk[6:].strip()
                        if data_str and data_str != '[DONE]':
                            data_json = json.loads(data_str)
                            if 'content' in data_json:
                                full_content.append(data_json['content'])
                    except:
                        pass
                    yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(stream_with_context(generate()), 
                   mimetype='text/event-stream',
                   headers={
                       'Cache-Control': 'no-cache',
                       'X-Accel-Buffering': 'no'
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
