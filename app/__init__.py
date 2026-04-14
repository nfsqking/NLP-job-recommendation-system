# -*- coding: utf-8 -*-
"""Flask 应用工厂模块

负责创建 Flask 应用实例、注册扩展和蓝图。
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'warning'

semantic_model = None


def init_semantic_model():
    """初始化语义模型（应用启动时调用一次）"""
    global semantic_model
    if semantic_model is None:
        try:
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            from sentence_transformers import SentenceTransformer
            semantic_model = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2',
                local_files_only=True
            )
            print("[信息] 语义模型加载成功")
        except Exception as e:
            print(f"[警告] 无法加载本地语义模型: {e}")
            print("[提示] 请先运行以下命令下载模型到本地缓存:")
            print("  python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')\"")
            semantic_model = None
    return semantic_model


def get_semantic_model():
    """获取语义模型实例"""
    global semantic_model
    return semantic_model


def create_app(config_name='default'):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称
        
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    
    from config import config
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    from app.models import User
    from app.routes.auth import auth as auth_bp
    from app.routes.dashboard import dashboard as dashboard_bp
    from app.routes.job_crawler import job_crawler as job_crawler_bp
    from app.routes.resume import resume as resume_bp
    from app.routes.match import match as match_bp
    from app.routes.skill_improvement import skill_improvement as skill_improvement_bp
    from app.routes.api_docs import api_docs as api_docs_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(job_crawler_bp, url_prefix='/api')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(match_bp)
    app.register_blueprint(skill_improvement_bp)
    app.register_blueprint(api_docs_bp)
    
    from flask import redirect, url_for
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    is_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    if is_main_process:
        with app.app_context():
            db.create_all()
        
        init_semantic_model()
    
    return app
