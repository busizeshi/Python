"""
应用包初始化
"""
import sys
from pathlib import Path
from flask import Flask

# 添加项目根目录到 Python 路径，使 IDE 能识别 config 模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.extensions import db


def create_app(config_name='default'):
    """应用工厂函数"""
    from config import config  # 延迟导入，避免循环依赖
    
    app = Flask(__name__)
    
    # 加载配置对象
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.user import user as user_blueprint
    app.register_blueprint(user_blueprint)
    
    # 注册错误处理蓝图
    from app.errors import error_bp
    app.register_blueprint(error_bp)
    
    # 创建数据库表（仅用于开发环境）
    with app.app_context():
        from app.models import User
        db.create_all()
    
    return app
