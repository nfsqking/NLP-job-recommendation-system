# -*- coding: utf-8 -*-
"""Flask 应用配置模块

包含开发、生产、测试环境的配置类。
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置类"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2026'
    
    WTF_CSRF_ENABLED = False
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    PERMANENT_SESSION_LIFETIME = 86400
    
    CRAWLER_EDGE_DRIVER_PATH = r'E:\edgedriver_win64\msedgedriver.exe'
    CRAWLER_BASE_URL = 'https://jobonline.cn'
    CRAWLER_JOBS_PER_PAGE = 20
    
    ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY') or ''


class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')


class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
