# -*- coding: utf-8 -*-
"""简历路由模块

处理简历录入、提交、查看、编辑、切换、删除等请求。
支持用户管理最多3份独立简历。
"""

import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Resume

resume = Blueprint('resume', __name__)

MAX_RESUME_COUNT = 3


def parse_list_data(data_list):
    """将列表数据转换为JSON字符串存储"""
    if not data_list:
        return ''
    if isinstance(data_list, list):
        return json.dumps(data_list, ensure_ascii=False)
    return data_list


def get_list_data(json_str):
    """将JSON字符串转换为列表数据"""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except:
        return []


def prepare_resume_data(resume):
    """准备简历数据用于前端回显"""
    if not resume:
        return {}
    
    education_list = get_list_data(resume.education_school)
    internship_list = get_list_data(resume.internship_company)
    work_list = get_list_data(resume.work_company)
    project_list = get_list_data(resume.project_name)
    
    return {
        'education': education_list if education_list else [{'school': '', 'major': ''}],
        'internship': internship_list,
        'work': work_list,
        'project': project_list
    }


def get_current_resume_id():
    """获取当前选中的简历ID，如果没有则返回活跃简历ID"""
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


def set_current_resume(resume_id):
    """设置当前选中的简历"""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    if not resume:
        return False
    
    Resume.query.filter_by(user_id=current_user.id).update({'is_active': False})
    resume.is_active = True
    db.session.commit()
    
    session['current_resume_id'] = resume_id
    return True


@resume.route('/list')
@login_required
def list_resumes():
    """简历列表页面"""
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    current_resume_id = get_current_resume_id()
    
    return render_template('resume/resume_list.html', 
                          resumes=resumes, 
                          current_resume_id=current_resume_id,
                          max_count=MAX_RESUME_COUNT)


@resume.route('/input', methods=['GET', 'POST'])
@login_required
def input_resume():
    """简历录入页面 - 创建新简历"""
    resume_count = Resume.query.filter_by(user_id=current_user.id).count()
    if resume_count >= MAX_RESUME_COUNT:
        flash(f'最多只能创建 {MAX_RESUME_COUNT} 份简历', 'warning')
        return redirect(url_for('resume.list_resumes'))
    
    if request.method == 'POST':
        resume_name = request.form.get('resume_name', '').strip()
        if not resume_name:
            resume_name = f'简历 {resume_count + 1}'
        
        education_schools = request.form.getlist('education_school')
        education_majors = request.form.getlist('education_major')
        
        internship_companies = request.form.getlist('internship_company')
        internship_positions = request.form.getlist('internship_position')
        internship_contents = request.form.getlist('internship_content')
        
        work_companies = request.form.getlist('work_company')
        work_positions = request.form.getlist('work_position')
        work_contents = request.form.getlist('work_content')
        
        project_names = request.form.getlist('project_name')
        project_contents = request.form.getlist('project_content')
        
        skills = request.form.get('skills', '').strip()
        self_evaluation = request.form.get('self_evaluation', '').strip()
        
        has_education_error = False
        for school, major in zip(education_schools, education_majors):
            if not school.strip() or not major.strip():
                has_education_error = True
                break
        
        if has_education_error:
            flash('请填写完整的教育经历（学校名称和专业为必填项）', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=None, resume_data=resume_data, resume_name=resume_name)
        
        if not skills:
            flash('个人技能不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=None, resume_data=resume_data, resume_name=resume_name)
        
        if not self_evaluation:
            flash('个人评价不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=None, resume_data=resume_data, resume_name=resume_name)
        
        education_list = [{'school': s.strip(), 'major': m.strip()} for s, m in zip(education_schools, education_majors) if s.strip() or m.strip()]
        internship_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(internship_companies, internship_positions, internship_contents) if c.strip() or p.strip() or ct.strip()]
        work_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(work_companies, work_positions, work_contents) if c.strip() or p.strip() or ct.strip()]
        project_list = [{'name': n.strip(), 'content': c.strip()} for n, c in zip(project_names, project_contents) if n.strip() or c.strip()]
        
        is_first_resume = Resume.query.filter_by(user_id=current_user.id).count() == 0
        
        new_resume = Resume(
            user_id=current_user.id,
            resume_name=resume_name,
            is_active=is_first_resume,
            education_school=parse_list_data(education_list),
            internship_company=parse_list_data(internship_list),
            work_company=parse_list_data(work_list),
            project_name=parse_list_data(project_list),
            skills=skills,
            self_evaluation=self_evaluation
        )
        db.session.add(new_resume)
        db.session.commit()
        
        if is_first_resume:
            session['current_resume_id'] = new_resume.id
        
        flash('简历创建成功', 'success')
        return redirect(url_for('resume.list_resumes'))
    
    resume_data = prepare_resume_data(None)
    return render_template('resume/resume_input.html', resume=None, resume_data=resume_data, resume_name='')


@resume.route('/edit/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def edit_resume(resume_id):
    """简历编辑页面"""
    existing_resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    
    if not existing_resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resume.list_resumes'))
    
    if request.method == 'POST':
        resume_name = request.form.get('resume_name', '').strip()
        if not resume_name:
            resume_name = existing_resume.resume_name
        
        education_schools = request.form.getlist('education_school')
        education_majors = request.form.getlist('education_major')
        
        internship_companies = request.form.getlist('internship_company')
        internship_positions = request.form.getlist('internship_position')
        internship_contents = request.form.getlist('internship_content')
        
        work_companies = request.form.getlist('work_company')
        work_positions = request.form.getlist('work_position')
        work_contents = request.form.getlist('work_content')
        
        project_names = request.form.getlist('project_name')
        project_contents = request.form.getlist('project_content')
        
        skills = request.form.get('skills', '').strip()
        self_evaluation = request.form.get('self_evaluation', '').strip()
        
        has_education_error = False
        for school, major in zip(education_schools, education_majors):
            if not school.strip() or not major.strip():
                has_education_error = True
                break
        
        if has_education_error:
            flash('请填写完整的教育经历（学校名称和专业为必填项）', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data, resume_name=resume_name)
        
        if not skills:
            flash('个人技能不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data, resume_name=resume_name)
        
        if not self_evaluation:
            flash('个人评价不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data, resume_name=resume_name)
        
        education_list = [{'school': s.strip(), 'major': m.strip()} for s, m in zip(education_schools, education_majors) if s.strip() or m.strip()]
        internship_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(internship_companies, internship_positions, internship_contents) if c.strip() or p.strip() or ct.strip()]
        work_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(work_companies, work_positions, work_contents) if c.strip() or p.strip() or ct.strip()]
        project_list = [{'name': n.strip(), 'content': c.strip()} for n, c in zip(project_names, project_contents) if n.strip() or c.strip()]
        
        existing_resume.resume_name = resume_name
        existing_resume.education_school = parse_list_data(education_list)
        existing_resume.internship_company = parse_list_data(internship_list)
        existing_resume.work_company = parse_list_data(work_list)
        existing_resume.project_name = parse_list_data(project_list)
        existing_resume.skills = skills
        existing_resume.self_evaluation = self_evaluation
        
        db.session.commit()
        flash('简历更新成功', 'success')
        return redirect(url_for('resume.list_resumes'))
    
    resume_data = prepare_resume_data(existing_resume)
    return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data, resume_name=existing_resume.resume_name)


@resume.route('/detail/<int:resume_id>')
@login_required
def detail_resume(resume_id):
    """简历查看页面"""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resume.list_resumes'))
    
    education_list = get_list_data(resume.education_school)
    internship_list = get_list_data(resume.internship_company)
    work_list = get_list_data(resume.work_company)
    project_list = get_list_data(resume.project_name)
    
    current_resume_id = get_current_resume_id()
    
    return render_template('resume/resume_detail.html', 
                          resume=resume, 
                          education_list=education_list,
                          internship_list=internship_list,
                          work_list=work_list,
                          project_list=project_list,
                          current_resume_id=current_resume_id)


@resume.route('/switch/<int:resume_id>')
@login_required
def switch_resume(resume_id):
    """切换当前使用的简历"""
    if set_current_resume(resume_id):
        flash('已切换到选中的简历', 'success')
    else:
        flash('切换失败，简历不存在', 'danger')
    return redirect(url_for('resume.list_resumes'))


@resume.route('/delete/<int:resume_id>')
@login_required
def delete_resume(resume_id):
    """删除简历"""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resume.list_resumes'))
    
    was_active = resume.is_active
    db.session.delete(resume)
    db.session.commit()
    
    if was_active:
        remaining = Resume.query.filter_by(user_id=current_user.id).first()
        if remaining:
            remaining.is_active = True
            session['current_resume_id'] = remaining.id
            db.session.commit()
        else:
            session.pop('current_resume_id', None)
    
    flash('简历已删除', 'success')
    return redirect(url_for('resume.list_resumes'))


@resume.route('/api/current')
@login_required
def api_get_current_resume():
    """获取当前简历信息API"""
    resume = get_current_resume()
    if not resume:
        return jsonify({
            'success': False,
            'message': '暂无简历'
        })
    
    return jsonify({
        'success': True,
        'resume': resume.to_dict()
    })


@resume.route('/api/list')
@login_required
def api_list_resumes():
    """获取简历列表API"""
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    current_resume_id = get_current_resume_id()
    
    return jsonify({
        'success': True,
        'resumes': [r.to_dict() for r in resumes],
        'current_resume_id': current_resume_id
    })
