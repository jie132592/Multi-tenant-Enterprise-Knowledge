from datetime import datetime

from sqlalchemy import Column, DateTime

from app import Base


class BaseModel(Base):
    pass



class TimestampModel:
    """时间戳混入模型"""

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)