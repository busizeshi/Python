"""
应用入口文件
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# 使用应用工厂创建应用实例
app = create_app('development')


if __name__ == '__main__':
    app.run(debug=True)
