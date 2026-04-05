# -*- coding: utf-8 -*-
"""岗位爬虫路由模块

提供爬虫启动、状态查询等 API 接口。
"""

import threading
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Job
from jiuyewang import JobOnlineSpider, JobInfo, DatabaseManager

job_crawler = Blueprint('job_crawler', __name__)

_crawler_status = {
    'is_running': False,
    'keyword': None,
    'progress': 0,
    'total': 0,
    'message': ''
}


class FlaskDatabaseManager:
    """Flask 数据库适配器，将爬虫数据存入 Flask 应用数据库"""
    
    def __init__(self):
        pass
    
    def save_job(self, job: JobInfo) -> None:
        """保存岗位信息到 Flask 数据库"""
        existing_job = Job.query.filter_by(job_id=job.job_id).first()
        
        if existing_job:
            existing_job.job_name = job.job_name
            existing_job.job_salary = job.job_salary
            existing_job.location = job.location
            existing_job.experience = job.experience
            existing_job.education = job.education
            existing_job.job_description = job.job_description
            existing_job.company_name = job.company_name
            existing_job.industry = job.industry
            existing_job.company_type = job.company_type
            existing_job.company_size = job.company_size
        else:
            new_job = Job(
                job_id=job.job_id,
                job_name=job.job_name,
                job_salary=job.job_salary,
                location=job.location,
                experience=job.experience,
                education=job.education,
                job_description=job.job_description,
                company_name=job.company_name,
                industry=job.industry,
                company_type=job.company_type,
                company_size=job.company_size
            )
            db.session.add(new_job)
        
        db.session.commit()


def run_crawler(keyword: str, max_jobs: int, app):
    """在后台线程中运行爬虫"""
    global _crawler_status
    
    with app.app_context():
        try:
            _crawler_status['is_running'] = True
            _crawler_status['keyword'] = keyword
            _crawler_status['progress'] = 0
            _crawler_status['total'] = max_jobs
            _crawler_status['message'] = '正在初始化浏览器...'
            
            spider = JobOnlineSpider(keyword, max_jobs)
            spider._init_browser()
            
            flask_db = FlaskDatabaseManager()
            spider.db = type('DB', (), {'save_job': flask_db.save_job})()
            
            _crawler_status['message'] = '正在搜索岗位...'
            
            search_url = spider.CONFIG['SEARCH_URL'].format(keyword=keyword)
            spider.browser.get(search_url)
            
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            WebDriverWait(spider.browser, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, spider.SELECTORS['job_list'])
                )
            )
            time.sleep(1)
            
            job_ids = spider._get_all_job_ids()
            _crawler_status['total'] = len(job_ids)
            
            for idx, job_id in enumerate(job_ids, 1):
                if not _crawler_status['is_running']:
                    break
                    
                _crawler_status['progress'] = idx
                _crawler_status['message'] = f'正在爬取第 {idx}/{len(job_ids)} 个岗位...'
                
                job = spider._parse_job_detail(job_id)
                flask_db.save_job(job)
            
            _crawler_status['message'] = f'爬取完成，共保存 {len(job_ids)} 条岗位信息'
            
        except Exception as e:
            _crawler_status['message'] = f'爬取出错: {str(e)}'
        finally:
            _crawler_status['is_running'] = False
            if spider.browser:
                spider.browser.quit()


@job_crawler.route('/crawler/start', methods=['POST'])
@login_required
def start_crawler():
    """启动爬虫"""
    global _crawler_status
    
    if _crawler_status['is_running']:
        return jsonify({
            'success': False,
            'message': '爬虫正在运行中，请等待完成'
        })
    
    data = request.get_json() or {}
    keyword = data.get('keyword', '').strip()
    max_jobs = data.get('max_jobs', 20)
    
    if not keyword:
        return jsonify({
            'success': False,
            'message': '请输入搜索关键词'
        })
    
    try:
        max_jobs = int(max_jobs)
        if max_jobs <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({
            'success': False,
            'message': '爬取数量必须为正整数'
        })
    
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_crawler,
        args=(keyword, max_jobs, app),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '爬虫已启动'
    })


@job_crawler.route('/crawler/status')
@login_required
def crawler_status():
    """获取爬虫状态"""
    return jsonify({
        'success': True,
        'data': _crawler_status
    })


@job_crawler.route('/crawler/stop', methods=['POST'])
@login_required
def stop_crawler():
    """停止爬虫"""
    global _crawler_status
    
    if _crawler_status['is_running']:
        _crawler_status['is_running'] = False
        _crawler_status['message'] = '正在停止爬虫...'
    
    return jsonify({
        'success': True,
        'message': '已发送停止信号'
    })


@job_crawler.route('/jobs/search')
@login_required
def search_jobs():
    """搜索岗位"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    experience = request.args.get('experience', '').strip()
    education = request.args.get('education', '').strip()
    
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
    
    if experience:
        query = query.filter(Job.experience.contains(experience))
    
    if education:
        query = query.filter(Job.education.contains(education))
    
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
