"""
用户蓝图 - 用户相关路由
"""
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User

user = Blueprint('user', __name__, url_prefix='/api/user')


@user.route('/list', methods=['GET'])
def user_list():
    """获取所有用户列表"""
    users = User.query.all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [user.to_dict() for user in users]
    })


@user.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取单个用户"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': user.to_dict()
    })


@user.route('/create', methods=['POST'])
def create_user():
    """创建用户"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'password', 'email', 'phone', 'sex', 'birthday', 'avatar']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'code': 400,
                'message': f'缺少必填字段: {field}'
            }), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'code': 400,
            'message': '用户名已存在'
        }), 400
    
    # 创建新用户
    new_user = User(
        username=data['username'],
        password=data['password'],
        email=data['email'],
        phone=data['phone'],
        sex=data['sex'],
        birthday=data['birthday'],
        avatar=data['avatar']
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': new_user.to_dict()
    }), 201


@user.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # 更新字段
    if 'username' in data:
        user.username = data['username']
    if 'password' in data:
        user.password = data['password']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'sex' in data:
        user.sex = data['sex']
    if 'birthday' in data:
        user.birthday = data['birthday']
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


@user.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })
