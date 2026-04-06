# -*- coding: utf-8 -*-
"""Flask 应用工厂模块

负责创建 Flask 应用实例、注册扩展和蓝图。
"""

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
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(job_crawler_bp, url_prefix='/api')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    
    from flask import redirect, url_for
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    with app.app_context():
        db.create_all()
    
    return app
