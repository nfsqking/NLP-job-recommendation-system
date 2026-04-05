/* 登录页面 JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            if (tab === 'login') {
                loginForm.classList.add('active');
                registerForm.classList.remove('active');
            } else {
                loginForm.classList.remove('active');
                registerForm.classList.add('active');
            }
        });
    });
    
    loginForm.addEventListener('submit', function(e) {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value.trim();
        
        if (!username || !password) {
            e.preventDefault();
            showFlashMessage('请输入用户名和密码', 'danger');
        }
    });
    
    registerForm.addEventListener('submit', function(e) {
        const username = document.getElementById('register-username').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value.trim();
        const passwordConfirm = document.getElementById('register-password-confirm').value.trim();
        
        if (!username || !email || !password || !passwordConfirm) {
            e.preventDefault();
            showFlashMessage('请填写所有必填字段', 'danger');
            return;
        }
        
        if (password !== passwordConfirm) {
            e.preventDefault();
            showFlashMessage('两次输入的密码不一致', 'danger');
            return;
        }
        
        if (password.length < 6) {
            e.preventDefault();
            showFlashMessage('密码长度至少为6位', 'danger');
            return;
        }
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            e.preventDefault();
            showFlashMessage('请输入有效的邮箱地址', 'danger');
            return;
        }
    });
});
