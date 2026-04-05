# -*- coding: utf-8 -*-
"""Flask 应用启动入口

启动开发服务器。
"""

import os
from app import create_app

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
