# -*- coding: utf-8 -*-
"""用户认证路由模块

处理用户登录、登出等认证相关请求。
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'danger')
            return render_template('login.html')
        
        login_user(user, remember=remember)
        flash(f'欢迎回来，{user.nickname or user.username}！', 'success')
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        return redirect(next_page)
    
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        nickname = request.form.get('nickname', '').strip()
        
        if not all([username, email, password, password_confirm]):
            flash('请填写所有必填字段', 'danger')
            return render_template('login.html')
        
        if password != password_confirm:
            flash('两次输入的密码不一致', 'danger')
            return render_template('login.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('login.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('login.html')
        
        user = User(
            username=username,
            email=email,
            nickname=nickname or username
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('login.html')
