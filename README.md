# 初始化数据库
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('数据库初始化完成')"