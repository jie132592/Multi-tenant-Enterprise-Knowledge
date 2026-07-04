"""租户模型"""
import enum

from sqlalchemy import Column, Integer, String

from app import Base
from app.models.base import TimestampModel


class TenantStatus(enum.Enum):
    ACTIVE = 1
    INACTIVE = 0

class Tenant(Base, TimestampModel):
    """租户表"""
    # 指定数据库真实表名
    __tablename__ = "tenants"

    # 主键、整数、自增
    # primary\_key=True 主键
    # autoincrement=True 数据库自增+1
    id = Column(Integer, primary_key=True, autoincrement=True)
    # nullable=False 字段必填，数据库不允许存NULL
    name = Column(String(128), nullable=False, comment="租户名称")
    # unique=True 整表不能重复，用来区分不同租户
    code = Column(String(64), unique=True, nullable=False, comment="租户编码")
    # 租户状态，默认启用；取值来自枚举：1正常，0禁用
    status = Column(Integer, default=TenantStatus.ACTIVE.value, comment="状态：1=正常 0=禁用")
    description = Column(String(512), default="", comment="描述")

    # 打印对象时的格式化输出，调试查看日志
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, code={self.code})>"