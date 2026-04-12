"""
主蓝图 - 首页
"""
from flask import Blueprint

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return '<h1>Welcome to Flask + MySQL Demo</h1>'


@main.route('/health')
def health():
    """健康检查"""
    return {'status': 'ok', 'message': 'Service is running'}
