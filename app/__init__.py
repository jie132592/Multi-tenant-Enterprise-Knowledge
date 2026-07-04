"""
数据库连接
"""
# 上下文变量，用于在线程、异步环境隔离数据库会话
from contextvars import ContextVar
# 导入sqlalchemy创建数据库引擎的工具
from sqlalchemy import create_engine
# 导入ORM模型基类（所有数据模型都要继承这个类）
from sqlalchemy.ext.declarative import declarative_base
# sessionmaker创建数据库会话工厂，session会话类型注解
from sqlalchemy.orm import sessionmaker, Session

from config import settings

# 同步引擎（用户创建表等操作）
# 创建同步数据库连接引擎，负责底层和Mysql建立连接
engine = create_engine(
    # 从配置读取完整Mysql连接字符串
    settings.DATABASE_URL,
    # 连接池预检测：每次使用连接前测试连接是否存活，避免断连报错
    pool_pre_ping=True,
    # 连接池常驻连接数量，默认保留10个空闲连接复用
    pool_size=10,
    # 最大溢出连接，业务高峰最多额外新建20个临时连接
    max_overflow=20,
    # # 开启SQL日志打印，DEBUG=True时会输出执行的SQL语句，生产关闭
    echo=settings.DEBUG
)

# 同步SessionFactory会话工厂
# 生成数据库会话的工厂类，autocommit=False 手动提交事务，autoflush=False不自动刷新数据
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 异步上下文变量
# 定义上下文变量，用来存储当前运行环境的数据库会话，默认值为空
_db_session: ContextVar[Session] = ContextVar("db_session", default=None)

def get_db() -> Session:
    """获取数据库会话（同步版本，用于依赖注入）"""
    # 从会话工厂新建一个数据库会话
    db = SessionLocal()
    try:
        # 返回会话接口
        return db
    finally:
        pass # 不要在这里close，交给调用方管理会话关闭

class DBSession:
    """数据库会话管理器，with语法自动处理提交、回滚、关闭"""
    def __init__(self):
        # 初始化会话为空
        self._session: Session = None

    # 写 `with 类实例:` 时会自动执行这个函数
    def __enter__(self) -> Session:
        # 使用with语句进入时，创建会话并返回
        self._session = SessionLocal()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with代码块执行完毕后自动触发"""
        if self._session:
            # 没有异常，正常提交事务
            if exc_type is None:
                self._session.commit()
            # 出现异常：回滚所有数据库操作，防止脏数据
            else:
                self._session.rollback()
            # 无论成功失败，最终关闭会话归还连接池
            self._session.close()

def get_db_session():
    """获取数据库会话的上下文管理器，配合with使用"""
    # 返回会话管理实例，外部可以with get_db_session() as db:
    return DBSession()

#OCR模型基类，所有数据表实体类都需要继承Base
Base = declarative_base()

def init_db():
    """初始化数据库(创建所有表)"""
    from app.models import tenant, user, knowledge, chat
    Base.metadata.create_all(bind=engine)