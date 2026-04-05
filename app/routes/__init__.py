# -*- coding: utf-8 -*-
"""路由模块包

导出所有蓝图路由。
"""

from app.routes.auth import auth
from app.routes.dashboard import dashboard
from app.routes.job_crawler import job_crawler

__all__ = ['auth', 'dashboard', 'job_crawler']
