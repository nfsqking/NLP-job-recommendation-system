# -*- coding: utf-8 -*-
"""API文档路由模块

使用Flask-RESTX自动生成可视化API文档。
提供系统所有后端接口的说明文档。
"""

from flask import Blueprint, render_template
from flask_restx import Api, Resource, fields, Namespace

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
    version='1.0',
    title='岗位推荐系统 API文档',
    description='系统所有后端接口的说明文档，包含用户认证、简历管理、岗位查找、简历匹配、个性化技能提升等核心功能。',
    doc='/docs',
    authorizations=authorizations,
    security='Bearer Auth'
)

ns_auth = Namespace('auth', description='用户认证相关接口', path='/auth')
ns_resume = Namespace('resume', description='简历管理相关接口', path='/resume')
ns_job = Namespace('job', description='岗位查找相关接口', path='/jobs')
ns_match = Namespace('match', description='简历匹配相关接口', path='/match')
ns_skill = Namespace('skill', description='个性化技能提升相关接口', path='/skill')

api.add_namespace(ns_auth)
api.add_namespace(ns_resume)
api.add_namespace(ns_job)
api.add_namespace(ns_match)
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
    'max_jobs': fields.Integer(required=False, description='最大爬取数量', example=20)
})

crawler_status_model = api.model('CrawlerStatus', {
    'is_running': fields.Boolean(description='是否正在运行'),
    'keyword': fields.String(description='当前搜索关键词'),
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
        pass


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
        pass


@ns_auth.route('/logout')
class Logout(Resource):
    @ns_auth.doc('logout')
    @ns_auth.response(200, '成功', auth_response_model)
    def get(self):
        """
        用户登出
        
        清除登录状态，退出当前用户会话。
        """
        pass


@ns_resume.route('/list')
class ResumeList(Resource):
    @ns_resume.doc('list_resumes')
    @ns_resume.response(200, '成功', resume_list_response)
    def get(self):
        """
        获取简历列表
        
        获取当前用户的所有简历，最多3份。
        返回简历列表及当前选中的简历ID。
        """
        pass


@ns_resume.route('/current')
class CurrentResume(Resource):
    @ns_resume.doc('get_current_resume')
    @ns_resume.response(200, '成功', resume_response)
    def get(self):
        """
        获取当前简历
        
        获取当前用户正在使用的简历详情。
        """
        pass


@ns_resume.route('/switch')
class SwitchResume(Resource):
    @ns_resume.doc('switch_resume')
    @ns_resume.expect(switch_resume_model)
    @ns_resume.response(200, '成功', resume_response)
    def post(self):
        """
        切换当前简历
        
        切换到指定的简历作为当前使用的简历。
        """
        pass


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
    def get(self):
        """
        搜索岗位
        
        根据关键词、地点、经验、学历等条件搜索岗位。
        支持分页查询。
        """
        pass


@ns_job.route('/crawler/start')
class CrawlerStart(Resource):
    @ns_job.doc('start_crawler')
    @ns_job.expect(crawler_start_model)
    @ns_job.response(200, '成功', crawler_response)
    def post(self):
        """
        启动爬虫
        
        启动岗位爬虫，根据关键词爬取岗位信息。
        爬虫在后台运行，可通过状态接口查询进度。
        """
        pass


@ns_job.route('/crawler/status')
class CrawlerStatus(Resource):
    @ns_job.doc('crawler_status')
    @ns_job.response(200, '成功', crawler_response)
    def get(self):
        """
        获取爬虫状态
        
        获取当前爬虫的运行状态、进度等信息。
        """
        pass


@ns_job.route('/crawler/stop')
class CrawlerStop(Resource):
    @ns_job.doc('stop_crawler')
    @ns_job.response(200, '成功', crawler_response)
    def post(self):
        """
        停止爬虫
        
        停止正在运行的爬虫任务。
        """
        pass


@ns_match.route('/analyze')
class MatchAnalyze(Resource):
    @ns_match.doc('analyze_match')
    @ns_match.expect(match_analyze_model)
    @ns_match.response(200, '成功', match_analyze_response)
    def post(self):
        """
        执行匹配分析
        
        对选定的岗位进行简历匹配分析，计算匹配分数。
        使用语义相似度算法，综合考虑教育、技能、经历等多维度。
        """
        pass


@ns_match.route('/list')
class MatchList(Resource):
    @ns_match.doc('get_match_list')
    @ns_match.response(200, '成功', match_list_response)
    def get(self):
        """
        获取匹配结果列表
        
        获取当前简历的所有匹配结果，按匹配分数降序排列。
        """
        pass


@ns_match.route('/delete')
class MatchDelete(Resource):
    @ns_match.doc('delete_matches')
    @ns_match.expect(delete_match_model)
    @ns_match.response(200, '成功', api.model('DeleteResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'message': fields.String(description='返回消息')
    }))
    def post(self):
        """
        删除匹配记录
        
        删除指定的匹配记录，支持批量删除。
        """
        pass


@ns_match.route('/clear')
class MatchClear(Resource):
    @ns_match.doc('clear_matches')
    @ns_match.response(200, '成功', api.model('ClearResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'message': fields.String(description='返回消息')
    }))
    def post(self):
        """
        清空匹配记录
        
        清空当前简历的所有匹配记录。
        """
        pass


@ns_match.route('/jobs')
class MatchJobs(Resource):
    @ns_match.doc('get_jobs')
    @ns_match.param('keyword', '搜索关键词')
    @ns_match.param('location', '工作地点')
    @ns_match.response(200, '成功', api.model('JobsResponse', {
        'success': fields.Boolean(description='操作是否成功'),
        'jobs': fields.List(fields.Nested(job_model), description='岗位列表')
    }))
    def get(self):
        """
        获取岗位列表
        
        获取可用于匹配分析的岗位列表。
        """
        pass


@ns_match.route('/resume/switch')
class MatchResumeSwitch(Resource):
    @ns_match.doc('match_switch_resume')
    @ns_match.expect(switch_resume_model)
    @ns_match.response(200, '成功', resume_response)
    def post(self):
        """
        切换当前简历（匹配模块）
        
        在匹配页面切换当前使用的简历。
        """
        pass


@ns_skill.route('/generate')
class SuggestionGenerate(Resource):
    @ns_skill.doc('generate_suggestion')
    @ns_skill.expect(suggestion_generate_model)
    @ns_skill.response(200, '成功', suggestion_response)
    def post(self):
        """
        生成技能提升建议
        
        根据简历和目标岗位，使用GLM-4.7 AI生成个性化技能提升建议。
        包含核心差距技能、提升路径、优先级等内容。
        """
        pass


@ns_skill.route('/stream')
class SuggestionStream(Resource):
    @ns_skill.doc('stream_suggestion')
    @ns_skill.expect(suggestion_generate_model)
    @ns_skill.response(200, '成功（Server-Sent Events流式响应）')
    def post(self):
        """
        流式生成技能提升建议
        
        使用SSE（Server-Sent Events）流式输出技能提升建议。
        实时返回AI生成的内容，支持自动滚动显示。
        """
        pass


@ns_skill.route('/get')
class SuggestionGet(Resource):
    @ns_skill.doc('get_suggestion')
    @ns_skill.param('job_id', '岗位ID', type=int, required=True)
    @ns_skill.response(200, '成功', suggestion_get_response)
    def get(self):
        """
        获取技能提升建议
        
        获取指定岗位的技能提升建议详情。
        """
        pass


@ns_skill.route('/list')
class SuggestionList(Resource):
    @ns_skill.doc('list_suggestions')
    @ns_skill.response(200, '成功', suggestion_list_response)
    def get(self):
        """
        获取建议列表
        
        获取当前简历的所有技能提升建议列表。
        """
        pass


@ns_skill.route('/resume/switch')
class SkillResumeSwitch(Resource):
    @ns_skill.doc('skill_switch_resume')
    @ns_skill.expect(switch_resume_model)
    @ns_skill.response(200, '成功', resume_response)
    def post(self):
        """
        切换当前简历（技能提升模块）
        
        在技能提升页面切换当前使用的简历。
        """
        pass
