# -*- coding: utf-8 -*-
"""简历路由模块

处理简历录入、提交、查看、编辑等请求。
"""

import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Resume

resume = Blueprint('resume', __name__)


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


@resume.route('/input', methods=['GET', 'POST'])
@login_required
def input_resume():
    """简历录入/编辑页面"""
    existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
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
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        if not skills:
            flash('个人技能不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        if not self_evaluation:
            flash('个人评价不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        education_list = [{'school': s.strip(), 'major': m.strip()} for s, m in zip(education_schools, education_majors) if s.strip() or m.strip()]
        internship_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(internship_companies, internship_positions, internship_contents) if c.strip() or p.strip() or ct.strip()]
        work_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(work_companies, work_positions, work_contents) if c.strip() or p.strip() or ct.strip()]
        project_list = [{'name': n.strip(), 'content': c.strip()} for n, c in zip(project_names, project_contents) if n.strip() or c.strip()]
        
        if existing_resume:
            existing_resume.education_school = parse_list_data(education_list)
            existing_resume.internship_company = parse_list_data(internship_list)
            existing_resume.work_company = parse_list_data(work_list)
            existing_resume.project_name = parse_list_data(project_list)
            existing_resume.skills = skills
            existing_resume.self_evaluation = self_evaluation
        else:
            new_resume = Resume(
                user_id=current_user.id,
                education_school=parse_list_data(education_list),
                internship_company=parse_list_data(internship_list),
                work_company=parse_list_data(work_list),
                project_name=parse_list_data(project_list),
                skills=skills,
                self_evaluation=self_evaluation
            )
            db.session.add(new_resume)
        
        db.session.commit()
        flash('简历保存成功', 'success')
        return redirect(url_for('resume.detail_resume'))
    
    resume_data = prepare_resume_data(existing_resume)
    return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)


@resume.route('/detail')
@login_required
def detail_resume():
    """简历查看页面"""
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    
    if not resume:
        flash('您还未填写简历，请先录入简历', 'info')
        return redirect(url_for('resume.input_resume'))
    
    education_list = get_list_data(resume.education_school)
    internship_list = get_list_data(resume.internship_company)
    work_list = get_list_data(resume.work_company)
    project_list = get_list_data(resume.project_name)
    
    return render_template('resume/resume_detail.html', 
                          resume=resume, 
                          education_list=education_list,
                          internship_list=internship_list,
                          work_list=work_list,
                          project_list=project_list)


@resume.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_resume():
    """简历编辑页面"""
    existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
    
    if not existing_resume:
        flash('您还未填写简历，请先录入简历', 'info')
        return redirect(url_for('resume.input_resume'))
    
    if request.method == 'POST':
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
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        if not skills:
            flash('个人技能不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        if not self_evaluation:
            flash('个人评价不能为空', 'danger')
            resume_data = {
                'education': [{'school': s, 'major': m} for s, m in zip(education_schools, education_majors)],
                'internship': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(internship_companies, internship_positions, internship_contents)],
                'work': [{'company': c, 'position': p, 'content': ct} for c, p, ct in zip(work_companies, work_positions, work_contents)],
                'project': [{'name': n, 'content': c} for n, c in zip(project_names, project_contents)]
            }
            return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
        
        education_list = [{'school': s.strip(), 'major': m.strip()} for s, m in zip(education_schools, education_majors) if s.strip() or m.strip()]
        internship_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(internship_companies, internship_positions, internship_contents) if c.strip() or p.strip() or ct.strip()]
        work_list = [{'company': c.strip(), 'position': p.strip(), 'content': ct.strip()} for c, p, ct in zip(work_companies, work_positions, work_contents) if c.strip() or p.strip() or ct.strip()]
        project_list = [{'name': n.strip(), 'content': c.strip()} for n, c in zip(project_names, project_contents) if n.strip() or c.strip()]
        
        existing_resume.education_school = parse_list_data(education_list)
        existing_resume.internship_company = parse_list_data(internship_list)
        existing_resume.work_company = parse_list_data(work_list)
        existing_resume.project_name = parse_list_data(project_list)
        existing_resume.skills = skills
        existing_resume.self_evaluation = self_evaluation
        
        db.session.commit()
        flash('简历更新成功', 'success')
        return redirect(url_for('resume.detail_resume'))
    
    resume_data = prepare_resume_data(existing_resume)
    return render_template('resume/resume_input.html', resume=existing_resume, resume_data=resume_data)
