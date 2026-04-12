"""
数据库模型
"""
from datetime import datetime
from app.extensions import db  # 从 extensions 导入 db 实例


class User(db.Model):
    """用户模型"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    sex = db.Column(db.String(20), nullable=False)
    birthday = db.Column(db.String(20), nullable=False)
    avatar = db.Column(db.String(20), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'sex': self.sex,
            'birthday': self.birthday,
            'avatar': self.avatar,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
