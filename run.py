# -*- coding: utf-8 -*-
"""Flask 应用启动入口

启动开发服务器。
"""

import os
from app import create_app

config_name = os.environ.get('FLASK_ENV', 'development')

if __name__ == '__main__':
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    app = create_app(config_name)
