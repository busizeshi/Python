"""
数据库实例
单独放在这里避免循环导入
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
