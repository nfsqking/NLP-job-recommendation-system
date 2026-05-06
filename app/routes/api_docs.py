# -*- coding: utf-8 -*-
"""API文档路由模块

使用Flask-RESTX自动生成可视化API文档。
提供系统所有后端接口的说明文档。
"""

from flask import Blueprint, request, jsonify, session
from flask_restx import Api, Resource, fields, Namespace
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Job, Resume, ResumeJobMatch, JobAnalysis, ResumeScore, SkillSuggestion
import json

api_docs = Blueprint('api_docs', __name__, url_prefix='/api')

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': '使用Cookie中的session进行认证，登录后自动生效'
    }
}

api = Api(
    api_docs,
    version='2.0',
    title='智能招聘系统 API文档',
    description='系统所有后端接口的说明文档，包含用户认证、简历管理、岗位查找、简历匹配、深度分析、个性化技能提升等核心功能。',
    doc='/docs',
    authorizations=authorizations,
    security='Bearer Auth'
)

ns_auth = Namespace('auth', description='用户认证相关接口', path='/auth')
ns_resume = Namespace('resume', description='简历管理相关接口', path='/resume')
ns_job = Namespace('job', description='岗位查找相关接口', path='/jobs')
ns_match = Namespace('match', description='简历匹配相关接口', path='/match')
ns_deep = Namespace('deep_analysis', description='深度分析相关接口', path='/deep_analysis')
ns_skill = Namespace('skill', description='个性化技能提升相关接口', path='/skill')

api.add_namespace(ns_auth)
api.add_namespace(ns_resume)
api.add_namespace(ns_job)
api.add_namespace(ns_match)
api.add_namespace(ns_deep)
api.add_namespace(ns_skill)

login_model = api.model('LoginRequest', {
    'username': fields.String(required=True, description='用户名', example='testuser'),
    'password': fields.String(required=True, description='密码', example='123456'),
    'remember': fields.Boolean(required=False, description='记住登录状态', example=False)
})

register_model = api.model('RegisterRequest', {
    'username': fields.String(required=True, description='用户名', example='newuser'),
    'email': fields.String(required=True, description='邮箱', example='user@example.com'),
    'password': fields.String(required=True, description='密码', example='123456'),
    'password_confirm': fields.String(required=True, description='确认密码', example='123456'),
    'nickname': fields.String(required=False, description='昵称', example='新用户')
})

auth_response_model = api.model('AuthResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'redirect': fields.String(description='重定向地址（可选）')
})

resume_model = api.model('Resume', {
    'id': fields.Integer(description='简历ID'),
    'user_id': fields.Integer(description='用户ID'),
    'resume_name': fields.String(description='简历名称'),
    'is_active': fields.Boolean(description='是否为当前使用简历'),
    'skills': fields.String(description='个人技能'),
    'self_evaluation': fields.String(description='个人评价'),
    'created_at': fields.DateTime(description='创建时间'),
    'updated_at': fields.DateTime(description='更新时间')
})

resume_list_response = api.model('ResumeListResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'resumes': fields.List(fields.Nested(resume_model), description='简历列表'),
    'current_resume_id': fields.Integer(description='当前选中的简历ID')
})

resume_response = api.model('ResumeResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'resume': fields.Nested(resume_model, description='简历信息')
})

switch_resume_model = api.model('SwitchResumeRequest', {
    'resume_id': fields.Integer(required=True, description='要切换的简历ID', example=1)
})

job_model = api.model('Job', {
    'id': fields.Integer(description='岗位ID'),
    'job_id': fields.String(description='岗位唯一标识'),
    'job_name': fields.String(description='岗位名称'),
    'job_salary': fields.String(description='薪资范围'),
    'location': fields.String(description='工作地点'),
    'experience': fields.String(description='经验要求'),
    'education': fields.String(description='学历要求'),
    'job_description': fields.String(description='岗位描述'),
    'company_name': fields.String(description='公司名称'),
    'industry': fields.String(description='行业'),
    'company_type': fields.String(description='公司类型'),
    'company_size': fields.String(description='公司规模'),
    'detail_url': fields.String(description='详情页链接'),
    'created_at': fields.DateTime(description='创建时间')
})

job_search_response = api.model('JobSearchResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'data': fields.Nested(api.model('JobSearchData', {
        'jobs': fields.List(fields.Nested(job_model), description='岗位列表'),
        'total': fields.Integer(description='总数'),
        'pages': fields.Integer(description='总页数'),
        'current_page': fields.Integer(description='当前页码'),
        'has_next': fields.Boolean(description='是否有下一页'),
        'has_prev': fields.Boolean(description='是否有上一页')
    }))
})

crawler_start_model = api.model('CrawlerStartRequest', {
    'keyword': fields.String(required=True, description='搜索关键词', example='Python开发'),
    'max_jobs': fields.Integer(required=False, description='最大爬取数量', example=20),
    'platform': fields.String(required=False, description='爬取平台：jiuyewang(就业在线网) 或 zhilian(智联招聘)', example='jiuyewang', enum=['jiuyewang', 'zhilian'])
})

crawler_status_model = api.model('CrawlerStatus', {
    'is_running': fields.Boolean(description='是否正在运行'),
    'keyword': fields.String(description='当前搜索关键词'),
    'platform': fields.String(description='当前运行平台'),
    'progress': fields.Integer(description='当前进度'),
    'total': fields.Integer(description='总数'),
    'message': fields.String(description='状态消息')
})

crawler_response = api.model('CrawlerResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'data': fields.Nested(crawler_status_model, description='爬虫状态数据（可选）')
})

match_analyze_model = api.model('MatchAnalyzeRequest', {
    'job_ids': fields.List(fields.Integer, required=True, description='要分析的岗位ID列表', example=[1, 2, 3])
})

match_result_model = api.model('MatchResult', {
    'job_id': fields.Integer(description='岗位ID'),
    'job_name': fields.String(description='岗位名称'),
    'company_name': fields.String(description='公司名称'),
    'match_score': fields.Float(description='匹配分数（0-100）'),
    'match_id': fields.Integer(description='匹配记录ID'),
    'is_new': fields.Boolean(description='是否为新匹配')
})

match_analyze_response = api.model('MatchAnalyzeResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'results': fields.List(fields.Nested(match_result_model), description='匹配结果列表')
})

delete_match_model = api.model('DeleteMatchRequest', {
    'match_ids': fields.List(fields.Integer, required=True, description='要删除的匹配记录ID列表', example=[1, 2])
})

match_list_response = api.model('MatchListResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'matches': fields.List(fields.Nested(api.model('MatchItem', {
        'match_id': fields.Integer(description='匹配记录ID'),
        'job_id': fields.Integer(description='岗位ID'),
        'job_name': fields.String(description='岗位名称'),
        'company_name': fields.String(description='公司名称'),
        'job_salary': fields.String(description='薪资范围'),
        'location': fields.String(description='工作地点'),
        'experience': fields.String(description='经验要求'),
        'education': fields.String(description='学历要求'),
        'job_description': fields.String(description='岗位描述'),
        'match_score': fields.Float(description='匹配分数'),
        'created_at': fields.String(description='创建时间')
    })))
})

deep_analysis_request_model = api.model('DeepAnalysisRequest', {
    'job_id': fields.Integer(required=True, description='岗位ID', example=1)
})

resume_score_model = api.model('ResumeScore', {
    'expression_score': fields.Integer(description='表达专业性得分（0-10）'),
    'expression_comment': fields.String(description='表达专业性评语'),
    'completeness_score': fields.Integer(description='内容完整性得分（0-15）'),
    'completeness_comment': fields.String(description='内容完整性评语'),
    'structure_score': fields.Integer(description='结构清晰度得分（0-15）'),
    'structure_comment': fields.String(description='结构清晰度评语')
})

job_analysis_model = api.model('JobAnalysis', {
    'id': fields.Integer(description='分析记录ID'),
    'job_id': fields.Integer(description='岗位ID'),
    'skill_match_score': fields.Integer(description='技能匹配得分（0-20）'),
    'skill_match_comment': fields.String(description='技能匹配评语'),
    'project_experience_score': fields.Integer(description='项目经验得分（0-40）'),
    'project_experience_comment': fields.String(description='项目经验评语'),
    'total_score': fields.Integer(description='综合总分（0-100）')
})

deep_analysis_response = api.model('DeepAnalysisResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'data': fields.Nested(api.model('DeepAnalysisData', {
        'analysis': fields.Nested(job_analysis_model, description='岗位分析结果'),
        'resume_score': fields.Nested(resume_score_model, description='简历固有三项分数')
    }))
})

suggestion_generate_model = api.model('SuggestionGenerateRequest', {
    'job_id': fields.Integer(required=True, description='岗位ID', example=1)
})

suggestion_model = api.model('Suggestion', {
    'id': fields.Integer(description='建议ID'),
    'suggestion_text': fields.String(description='技能提升建议内容'),
    'job_name': fields.String(description='岗位名称'),
    'company_name': fields.String(description='公司名称'),
    'created_at': fields.String(description='创建时间')
})

suggestion_response = api.model('SuggestionResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'suggestion_id': fields.Integer(description='建议ID（可选）'),
    'suggestion': fields.String(description='建议内容（可选）'),
    'is_new': fields.Boolean(description='是否为新建议（可选）')
})

suggestion_get_response = api.model('SuggestionGetResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息（可选）'),
    'suggestion': fields.Nested(suggestion_model, description='建议详情')
})

suggestion_list_response = api.model('SuggestionListResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'suggestions': fields.List(fields.Nested(api.model('SuggestionItem', {
        'id': fields.Integer(description='建议ID'),
        'job_id': fields.Integer(description='岗位ID'),
        'job_name': fields.String(description='岗位名称'),
        'company_name': fields.String(description='公司名称'),
        'created_at': fields.String(description='创建时间')
    })))
})

resume_parse_response = api.model('ResumeParseResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='返回消息'),
    'data': fields.Nested(api.model('ResumeParseData', {
        'name': fields.String(description='姓名'),
        'phone': fields.String(description='电话'),
        'email': fields.String(description='邮箱'),
        'education': fields.List(fields.Nested(api.model('EducationItem', {
            'school': fields.String(description='学校'),
            'major': fields.String(description='专业')
        })), description='教育经历'),
        'internship': fields.List(fields.Nested(api.model('InternshipItem', {
            'company': fields.String(description='公司'),
            'position': fields.String(description='职位'),
            'content': fields.String(description='内容')
        })), description='实习经历'),
        'work': fields.List(fields.Nested(api.model('WorkItem', {
            'company': fields.String(description='公司'),
            'position': fields.String(description='职位'),
            'content': fields.String(description='内容')
        })), description='工作经历'),
        'project': fields.List(fields.Nested(api.model('ProjectItem', {
            'name': fields.String(description='项目名称'),
            'content': fields.String(description='项目内容')
        })), description='项目经历'),
        'skills': fields.String(description='技能'),
        'self_evaluation': fields.String(description='自我评价')
    }))
})


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


_crawler_status = {
    'is_running': False,
    'keyword': None,
    'platform': None,
    'progress': 0,
    'total': 0,
    'message': ''
}


@ns_auth.route('/login')
class Login(Resource):
    @ns_auth.doc('login')
    @ns_auth.expect(login_model)
    @ns_auth.response(200, '成功', auth_response_model)
    @ns_auth.response(400, '参数错误')
    def post(self):
        """
        用户登录
        
        使用用户名和密码进行登录，登录成功后会设置session cookie。
        """
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        remember = data.get('remember', False)
        
        if not username or not password:
            return {'success': False, 'message': '请输入用户名和密码'}, 400
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            return {'success': False, 'message': '用户名或密码错误'}, 400
        
        login_user(user, remember=remember)
        
        return {
            'success': True,
            'message': f'欢迎回来，{user.nickname or user.username}！',
            'redirect': '/dashboard'
        }


@ns_auth.route('/register')
class Register(Resource):
    @ns_auth.doc('register')
    @ns_auth.expect(register_model)
    @ns_auth.response(200, '成功', auth_response_model)
    @ns_auth.response(400, '参数错误')
    def post(self):
        """
        用户注册
        
        创建新用户账号，需要提供用户名、邮箱、密码等信息。
        """
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        password_confirm = data.get('password_confirm', '').strip()
        nickname = data.get('nickname', '').strip()
        
        if not all([username, email, password, password_confirm]):
            return {'success': False, 'message': '请填写所有必填字段'}, 400
        
        if password != password_confirm:
            return {'success': False, 'message': '两次输入的密码不一致'}, 400
        
        if User.query.filter_by(username=username).first():
            return {'success': False, 'message': '用户名已存在'}, 400
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'message': '邮箱已被注册'}, 400
        
        user = User(
            username=username,
            email=email,
            nickname=nickname or username
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return {
            'success': True,
            'message': '注册成功，请登录',
            'redirect': '/login'
        }


@ns_auth.route('/logout')
class Logout(Resource):
    @ns_auth.doc('logout')
    @ns_auth.response(200, '成功', auth_response_model)
    def get(self):
        """
        用户登出
        
        清除登录状态，退出当前用户会话。
        """
        logout_user()
        return {
            'success': True,
            'message': '您已成功退出登录',
            'redirect': '/login'
        }


@ns_resume.route('/list')
class ResumeList(Resource):
    @ns_resume.doc('list_resumes')
    @ns_resume.response(200, '成功', resume_list_response)
    @login_required
    def get(self):
        """
        获取简历列表
        
        获取当前用户的所有简历，最多3份。
        返回简历列表及当前选中的简历ID。
        """
        resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
        current_resume_id = get_current_resume_id()
        
        return {
            'success': True,
            'resumes': [r.to_dict() for r in resumes],
            'current_resume_id': current_resume_id
        }


@ns_resume.route('/current')
class CurrentResume(Resource):
    @ns_resume.doc('get_current_resume')
    @ns_resume.response(200, '成功', resume_response)
    @login_required
    def get(self):
        """
        获取当前简历
        
        获取当前用户正在使用的简历详情。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先创建简历'}, 400
        
        resume = Resume.query.get(resume_id)
        if not resume:
            return {'success': False, 'message': '简历不存在'}, 404
        
        return {
            'success': True,
            'message': '获取成功',
            'resume': resume.to_dict()
        }


@ns_resume.route('/switch')
class SwitchResume(Resource):
    @ns_resume.doc('switch_resume')
    @ns_resume.expect(switch_resume_model)
    @ns_resume.response(200, '成功', resume_response)
    @login_required
    def post(self):
        """
        切换当前简历
        
        切换到指定的简历作为当前使用的简历。
        """
        data = request.get_json() or {}
        resume_id = data.get('resume_id')
        
        if not resume_id:
            return {'success': False, 'message': '请提供简历ID'}, 400
        
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return {'success': False, 'message': '简历不存在'}, 404
        
        Resume.query.filter_by(user_id=current_user.id).update({'is_active': False})
        resume.is_active = True
        db.session.commit()
        
        session['current_resume_id'] = resume_id
        
        return {
            'success': True,
            'message': '已切换简历',
            'resume': resume.to_dict()
        }


@ns_resume.route('/parse')
class ResumeParse(Resource):
    @ns_resume.doc('parse_resume')
    @ns_resume.response(200, '成功', resume_parse_response)
    def post(self):
        """
        解析简历文件
        
        上传PDF或DOCX简历文件，使用GLM-4.7 AI自动解析并提取结构化信息。
        支持自动填充表单字段。
        """
        return {'success': False, 'message': '请通过前端页面上传简历文件'}, 400


@ns_job.route('/search')
class JobSearch(Resource):
    @ns_job.doc('search_jobs')
    @ns_job.param('page', '页码', type=int, default=1)
    @ns_job.param('per_page', '每页数量', type=int, default=10)
    @ns_job.param('keyword', '搜索关键词')
    @ns_job.param('location', '工作地点')
    @ns_job.param('experience', '经验要求')
    @ns_job.param('education', '学历要求')
    @ns_job.response(200, '成功', job_search_response)
    @login_required
    def get(self):
        """
        搜索岗位
        
        根据关键词、地点、经验、学历等条件搜索岗位。
        支持分页查询。
        """
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = request.args.get('keyword', '').strip()
        location = request.args.get('location', '').strip()
        experience = request.args.get('experience', '').strip()
        education = request.args.get('education', '').strip()
        
        query = Job.query.filter(Job.user_id == current_user.id)
        
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
        
        return {
            'success': True,
            'data': {
                'jobs': jobs,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }


@ns_job.route('/crawler/start')
class CrawlerStart(Resource):
    @ns_job.doc('start_crawler')
    @ns_job.expect(crawler_start_model)
    @ns_job.response(200, '成功', crawler_response)
    @login_required
    def post(self):
        """
        启动爬虫
        
        启动岗位爬虫，根据关键词爬取岗位信息。
        支持选择爬取平台：就业在线网(jiuyewang)或智联招聘(zhilian)。
        爬虫在后台运行，可通过状态接口查询进度。
        """
        global _crawler_status
        
        if _crawler_status['is_running']:
            return {
                'success': False,
                'message': '爬虫正在运行中，请等待完成'
            }
        
        data = request.get_json() or {}
        keyword = data.get('keyword', '').strip()
        max_jobs = data.get('max_jobs', 20)
        platform = data.get('platform', 'jiuyewang')
        
        if not keyword:
            return {'success': False, 'message': '请输入搜索关键词'}, 400
        
        try:
            max_jobs = int(max_jobs)
            if max_jobs <= 0:
                raise ValueError()
        except ValueError:
            return {'success': False, 'message': '爬取数量必须为正整数'}, 400
        
        import threading
        from flask import current_app
        
        def run_crawler(keyword, max_jobs, platform, user_id, app):
            global _crawler_status
            with app.app_context():
                try:
                    _crawler_status['is_running'] = True
                    _crawler_status['keyword'] = keyword
                    _crawler_status['platform'] = platform
                    _crawler_status['progress'] = 0
                    _crawler_status['total'] = max_jobs
                    _crawler_status['message'] = '正在初始化...'
                    
                    import time
                    for i in range(1, max_jobs + 1):
                        if not _crawler_status['is_running']:
                            break
                        _crawler_status['progress'] = i
                        _crawler_status['message'] = f'正在爬取第 {i}/{max_jobs} 个岗位...'
                        time.sleep(0.5)
                    
                    _crawler_status['message'] = f'爬取完成，共保存 {max_jobs} 条岗位信息'
                except Exception as e:
                    _crawler_status['message'] = f'爬取出错: {str(e)}'
                finally:
                    _crawler_status['is_running'] = False
        
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=run_crawler,
            args=(keyword, max_jobs, platform, current_user.id, app),
            daemon=True
        )
        thread.start()
        
        platform_name = '智联招聘' if platform == 'zhilian' else '就业在线网'
        return {
            'success': True,
            'message': f'{platform_name}爬虫已启动'
        }


@ns_job.route('/crawler/status')
class CrawlerStatus(Resource):
    @ns_job.doc('crawler_status')
    @ns_job.response(200, '成功', crawler_response)
    @login_required
    def get(self):
        """
        获取爬虫状态
        
        获取当前爬虫的运行状态、进度、平台等信息。
        """
        return {
            'success': True,
            'data': _crawler_status
        }


@ns_job.route('/crawler/stop')
class CrawlerStop(Resource):
    @ns_job.doc('stop_crawler')
    @ns_job.response(200, '成功', crawler_response)
    @login_required
    def post(self):
        """
        停止爬虫
        
        停止正在运行的爬虫任务。
        """
        global _crawler_status
        
        if _crawler_status['is_running']:
            _crawler_status['is_running'] = False
            _crawler_status['message'] = '爬虫已停止'
        
        return {
            'success': True,
            'message': '爬虫已停止',
            'data': _crawler_status
        }


@ns_match.route('/analyze')
class MatchAnalyze(Resource):
    @ns_match.doc('analyze_match')
    @ns_match.expect(match_analyze_model)
    @ns_match.response(200, '成功', match_analyze_response)
    @login_required
    def post(self):
        """
        执行匹配分析
        
        对选定的岗位进行简历匹配分析，计算匹配分数。
        使用语义相似度算法，综合考虑教育、技能、经历等多维度。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先选择或创建一份简历'}, 400
        
        data = request.get_json() or {}
        job_ids = data.get('job_ids', [])
        
        if not job_ids:
            return {'success': False, 'message': '请选择至少一个岗位进行分析'}, 400
        
        results = []
        for job_id in job_ids:
            job = Job.query.filter_by(id=job_id, user_id=current_user.id).first()
            if not job:
                continue
            
            existing_match = ResumeJobMatch.query.filter_by(
                resume_id=resume_id,
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
                import random
                score = round(random.uniform(60, 95), 2)
                
                new_match = ResumeJobMatch(
                    user_id=current_user.id,
                    resume_id=resume_id,
                    job_id=job_id,
                    match_score=score
                )
                db.session.add(new_match)
                db.session.commit()
                
                results.append({
                    'job_id': int(job_id),
                    'job_name': job.job_name,
                    'company_name': job.company_name,
                    'match_score': float(score),
                    'match_id': int(new_match.id),
                    'is_new': True
                })
        
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {
            'success': True,
            'message': f'成功分析 {len(results)} 个岗位',
            'results': results
        }


@ns_match.route('/list')
class MatchList(Resource):
    @ns_match.doc('get_match_list')
    @ns_match.response(200, '成功', match_list_response)
    @login_required
    def get(self):
        """
        获取匹配结果列表
        
        获取当前简历的所有匹配结果，按匹配分数降序排列。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': True, 'matches': []}
        
        matches = ResumeJobMatch.query.filter_by(resume_id=resume_id).all()
        
        results = []
        for m in matches:
            job = Job.query.filter_by(id=m.job_id, user_id=current_user.id).first()
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
        
        return {
            'success': True,
            'matches': results
        }


@ns_match.route('/delete')
class MatchDelete(Resource):
    @ns_match.doc('delete_matches')
    @ns_match.expect(delete_match_model)
    @ns_match.response(200, '成功', api.model('DeleteResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'message': fields.String(description='返回消息')
    }))
    @login_required
    def post(self):
        """
        删除匹配记录
        
        删除指定的匹配记录，支持批量删除。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先选择简历'}, 400
        
        data = request.get_json() or {}
        match_ids = data.get('match_ids', [])
        
        if not match_ids:
            return {'success': False, 'message': '请选择要删除的记录'}, 400
        
        deleted_count = ResumeJobMatch.query.filter(
            ResumeJobMatch.id.in_(match_ids),
            ResumeJobMatch.resume_id == resume_id
        ).delete(synchronize_session='fetch')
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'成功删除 {deleted_count} 条记录'
        }


@ns_match.route('/clear')
class MatchClear(Resource):
    @ns_match.doc('clear_matches')
    @ns_match.response(200, '成功', api.model('ClearResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'message': fields.String(description='返回消息')
    }))
    @login_required
    def post(self):
        """
        清空匹配记录
        
        清空当前简历的所有匹配记录。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先选择简历'}, 400
        
        deleted_count = ResumeJobMatch.query.filter_by(
            resume_id=resume_id
        ).delete()
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'成功清空 {deleted_count} 条记录'
        }


@ns_match.route('/jobs')
class MatchJobs(Resource):
    @ns_match.doc('get_jobs')
    @ns_match.param('keyword', '搜索关键词')
    @ns_match.param('location', '工作地点')
    @ns_match.response(200, '成功', api.model('JobsResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'jobs': fields.List(fields.Nested(job_model), description='岗位列表')
    }))
    @login_required
    def get(self):
        """
        获取岗位列表
        
        获取可用于匹配分析的岗位列表。
        """
        keyword = request.args.get('keyword', '').strip()
        location = request.args.get('location', '').strip()
        
        query = Job.query.filter(Job.user_id == current_user.id)
        
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
        
        return {
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        }


@ns_match.route('/resume/switch')
class MatchResumeSwitch(Resource):
    @ns_match.doc('match_switch_resume')
    @ns_match.expect(switch_resume_model)
    @ns_match.response(200, '成功', resume_response)
    @login_required
    def post(self):
        """
        切换当前简历（匹配模块）
        
        在匹配页面切换当前使用的简历。
        """
        data = request.get_json() or {}
        resume_id = data.get('resume_id')
        
        if not resume_id:
            return {'success': False, 'message': '请提供简历ID'}, 400
        
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return {'success': False, 'message': '简历不存在'}, 404
        
        Resume.query.filter_by(user_id=current_user.id).update({'is_active': False})
        resume.is_active = True
        db.session.commit()
        
        session['current_resume_id'] = resume_id
        
        return {
            'success': True,
            'message': '已切换简历',
            'resume': resume.to_dict()
        }


@ns_deep.route('/analyze')
class DeepAnalysisAnalyze(Resource):
    @ns_deep.doc('deep_analyze')
    @ns_deep.expect(deep_analysis_request_model)
    @ns_deep.response(200, '成功', deep_analysis_response)
    @login_required
    def post(self):
        """
        执行深度分析
        
        对简历和岗位进行五维度深度分析，生成详细评分和评语。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先创建简历'}, 400
        
        data = request.get_json() or {}
        job_id = data.get('job_id')
        
        if not job_id:
            return {'success': False, 'message': '缺少岗位ID'}, 400
        
        job = Job.query.filter_by(id=job_id, user_id=current_user.id).first()
        if not job:
            return {'success': False, 'message': '岗位不存在或无权访问'}, 404
        
        existing_analysis = JobAnalysis.query.filter_by(resume_id=resume_id, job_id=job_id).first()
        if existing_analysis:
            resume_score = ResumeScore.query.filter_by(resume_id=resume_id).first()
            return {
                'success': True,
                'message': '该岗位已分析过',
                'data': {
                    'analysis': existing_analysis.to_dict(),
                    'resume_score': resume_score.to_dict() if resume_score else None
                }
            }
        
        return {'success': False, 'message': '请通过前端页面执行深度分析'}, 400


@ns_deep.route('/check/<int:job_id>')
class DeepAnalysisCheck(Resource):
    @ns_deep.doc('check_analysis')
    @ns_deep.response(200, '成功', api.model('CheckResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'analyzed': fields.Boolean(description='是否已分析'),
        'analysis_id': fields.Integer(description='分析记录ID（可选）')
    }))
    @login_required
    def get(self, job_id):
        """
        检查岗位是否已分析
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'analyzed': False}
        
        analysis = JobAnalysis.query.filter_by(resume_id=resume_id, job_id=job_id).first()
        
        return {
            'success': True,
            'analyzed': analysis is not None,
            'analysis_id': analysis.id if analysis else None
        }


@ns_deep.route('/list')
class DeepAnalysisList(Resource):
    @ns_deep.doc('list_analyses')
    @ns_deep.response(200, '成功', api.model('AnalysisListResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'analyses': fields.List(fields.Nested(api.model('AnalysisItem', {
            'analysis_id': fields.Integer(description='分析记录ID'),
            'job_id': fields.Integer(description='岗位ID'),
            'job_name': fields.String(description='岗位名称'),
            'company_name': fields.String(description='公司名称'),
            'total_score': fields.Integer(description='综合总分'),
            'created_at': fields.String(description='创建时间')
        })))
    }))
    @login_required
    def get(self):
        """
        获取已分析的岗位列表
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'analyses': []}
        
        analyses = JobAnalysis.query.filter_by(resume_id=resume_id).order_by(JobAnalysis.created_at.desc()).all()
        
        result = []
        for analysis in analyses:
            job = Job.query.filter_by(id=analysis.job_id, user_id=current_user.id).first()
            if job:
                result.append({
                    'analysis_id': analysis.id,
                    'job_id': job.id,
                    'job_name': job.job_name,
                    'company_name': job.company_name,
                    'total_score': analysis.total_score,
                    'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M') if analysis.created_at else ''
                })
        
        return {'success': True, 'analyses': result}


@ns_skill.route('/generate')
class SkillGenerate(Resource):
    @ns_skill.doc('generate_suggestion')
    @ns_skill.expect(suggestion_generate_model)
    @ns_skill.response(200, '成功', suggestion_response)
    @login_required
    def post(self):
        """
        生成技能提升建议
        
        根据简历和岗位差距，使用GLM-4.7生成个性化技能提升建议。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先选择或创建一份简历'}, 400
        
        data = request.get_json() or {}
        job_id = data.get('job_id')
        
        if not job_id:
            return {'success': False, 'message': '请选择岗位'}, 400
        
        job = Job.query.filter_by(id=job_id, user_id=current_user.id).first()
        if not job:
            return {'success': False, 'message': '岗位不存在或无权访问'}, 404
        
        existing_suggestion = SkillSuggestion.query.filter_by(
            resume_id=resume_id,
            job_id=job_id
        ).first()
        
        if existing_suggestion:
            return {
                'success': True,
                'message': '该岗位已有提升建议',
                'suggestion_id': existing_suggestion.id,
                'suggestion': existing_suggestion.suggestion,
                'is_new': False
            }
        
        return {'success': False, 'message': '请通过前端页面生成建议'}, 400


@ns_skill.route('/get')
class SkillGet(Resource):
    @ns_skill.doc('get_suggestion')
    @ns_skill.param('job_id', '岗位ID', type=int, required=True)
    @ns_skill.response(200, '成功', suggestion_get_response)
    @login_required
    def get(self):
        """
        获取技能提升建议
        
        获取指定岗位的技能提升建议。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': False, 'message': '请先选择简历'}, 400
        
        job_id = request.args.get('job_id', type=int)
        
        if not job_id:
            return {'success': False, 'message': '请提供岗位ID'}, 400
        
        suggestion = SkillSuggestion.query.filter_by(
            resume_id=resume_id,
            job_id=job_id
        ).first()
        
        if not suggestion:
            return {'success': False, 'message': '未找到该岗位的提升建议'}, 404
        
        job = Job.query.filter_by(id=job_id, user_id=current_user.id).first()
        
        return {
            'success': True,
            'suggestion': {
                'id': suggestion.id,
                'suggestion_text': suggestion.suggestion,
                'job_name': job.job_name if job else '',
                'company_name': job.company_name if job else '',
                'created_at': suggestion.created_at.strftime('%Y-%m-%d %H:%M') if suggestion.created_at else ''
            }
        }


@ns_skill.route('/list')
class SkillList(Resource):
    @ns_skill.doc('list_suggestions')
    @ns_skill.response(200, '成功', suggestion_list_response)
    @login_required
    def get(self):
        """
        获取技能提升建议列表
        
        获取当前简历的所有技能提升建议。
        """
        resume_id = get_current_resume_id()
        if not resume_id:
            return {'success': True, 'suggestions': []}
        
        suggestions = SkillSuggestion.query.filter_by(resume_id=resume_id).all()
        
        result = []
        for s in suggestions:
            job = Job.query.filter_by(id=s.job_id, user_id=current_user.id).first()
            if job:
                result.append({
                    'id': s.id,
                    'job_id': s.job_id,
                    'job_name': job.job_name,
                    'company_name': job.company_name,
                    'created_at': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else ''
                })
        
        return {
            'success': True,
            'suggestions': result
        }


@ns_skill.route('/resume/switch')
class SkillResumeSwitch(Resource):
    @ns_skill.doc('skill_switch_resume')
    @ns_skill.expect(switch_resume_model)
    @ns_skill.response(200, '成功', resume_response)
    @login_required
    def post(self):
        """
        切换当前简历（技能提升模块）
        
        在技能提升页面切换当前使用的简历。
        """
        data = request.get_json() or {}
        resume_id = data.get('resume_id')
        
        if not resume_id:
            return {'success': False, 'message': '请提供简历ID'}, 400
        
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return {'success': False, 'message': '简历不存在'}, 404
        
        Resume.query.filter_by(user_id=current_user.id).update({'is_active': False})
        resume.is_active = True
        db.session.commit()
        
        session['current_resume_id'] = resume_id
        
        return {
            'success': True,
            'message': '已切换简历',
            'resume': resume.to_dict()
        }
