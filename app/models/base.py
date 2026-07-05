from datetime import datetime

from sqlalchemy import Column, DateTime, Integer

from app import Base


class BaseModel(Base):
    """基础模型 ID主键"""
    # 1. 仅用来给其他实体模型做父类，自动继承里面定义的字段、属性
    # 2. 所有继承它的子模型，都会自动带上 `id` 主键
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class TimestampModel:
    """时间戳混入模型"""

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)