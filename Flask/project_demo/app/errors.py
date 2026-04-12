"""
错误处理蓝图 - 统一的错误处理
"""
from flask import Blueprint, jsonify, request

error_bp = Blueprint('error', __name__)


@error_bp.app_errorhandler(400)
def bad_request(error):
    """
    400 错误处理 - 错误请求
    
    触发场景：
    - 请求参数格式错误
    - JSON 格式不正确
    """
    return jsonify({
        'code': 400,
        'message': '错误的请求',
        'error': str(error.description) if hasattr(error, 'description') else '请求参数错误'
    }), 400


@error_bp.app_errorhandler(401)
def unauthorized(error):
    """
    401 错误处理 - 未授权
    
    触发场景：
    - 未登录访问需要认证的接口
    - token 过期或无效
    """
    return jsonify({
        'code': 401,
        'message': '未授权，请先登录',
        'error': str(error.description) if hasattr(error, 'description') else '认证失败'
    }), 401


@error_bp.app_errorhandler(403)
def forbidden(error):
    """
    403 错误处理 - 禁止访问
    
    触发场景：
    - 没有权限访问该资源
    - IP 被禁止
    """
    return jsonify({
        'code': 403,
        'message': '禁止访问',
        'error': str(error.description) if hasattr(error, 'description') else '权限不足'
    }), 403


@error_bp.app_errorhandler(404)
def not_found(error):
    """
    404 错误处理 - 资源未找到
    
    触发场景：
    - 访问不存在的 URL
    - 请求的资源不存在
    
    示例：
    GET /api/user/99999  -> 如果用户ID不存在会触发
    GET /nonexistent     -> 访问不存在的路由
    """
    # 判断是 API 请求还是普通页面请求
    if request.path.startswith('/api/'):
        return jsonify({
            'code': 404,
            'message': '资源未找到',
            'error': f'路径 {request.path} 不存在'
        }), 404
    else:
        return jsonify({
            'code': 404,
            'message': '页面未找到',
            'error': '您访问的页面不存在'
        }), 404


@error_bp.app_errorhandler(405)
def method_not_allowed(error):
    """
    405 错误处理 - 方法不允许
    
    触发场景：
    - 用 GET 请求 POST 接口
    - 用 POST 请求 DELETE 接口
    
    示例：
    GET /api/user/create  -> 该接口只允许 POST，会触发 405
    """
    return jsonify({
        'code': 405,
        'message': '请求方法不允许',
        'error': f'该接口不支持 {request.method} 方法'
    }), 405


@error_bp.app_errorhandler(500)
def internal_server_error(error):
    """
    500 错误处理 - 服务器内部错误
    
    触发场景：
    - 数据库连接失败
    - 代码逻辑错误
    - 第三方服务异常
    
    注意：
    - 生产环境不应该返回详细的错误信息（安全考虑）
    - 开发环境可以返回详细信息方便调试
    """
    from flask import current_app
    
    # 开发环境返回详细错误信息
    if current_app.debug:
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'error': str(error),
            'traceback': str(error.__traceback__) if hasattr(error, '__traceback__') else None
        }), 500
    else:
        # 生产环境返回简洁信息
        return jsonify({
            'code': 500,
            'message': '服务器内部错误，请稍后重试'
        }), 500


@error_bp.app_errorhandler(Exception)
def handle_exception(error):
    """
    捕获所有未处理的异常
    
    这是最后的防线，捕获所有其他错误处理器没有捕获的异常
    """
    from flask import current_app
    import traceback
    
    # 记录错误日志（生产环境应该写入日志文件）
    current_app.logger.error(f'未处理的异常: {str(error)}')
    current_app.logger.error(traceback.format_exc())
    
    return jsonify({
        'code': 500,
        'message': '服务器错误',
        'error': str(error) if current_app.debug else '系统繁忙，请稍后重试'
    }), 500
