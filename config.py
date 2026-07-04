from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础
    APP_NAME: str = "企业知识库系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库 - Mysql
    DB_HOST: str = "localhost"
    DB_PORT: int = 3307
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "mini_kb"

    # 向量数据库 - Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "mini_kb_embeddings"

    # JWT配置
    SECRET_KEY: str = "40f2101c5b5a5d1b170daacfe1906d9d81657e326579ed15b1d350375182cbda"
    ALGORITHM: str = "HS256" # 加密算法 HS265(哈希算法)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7天

    # LLM配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    LLM_MODEL: str = ""
    EMBEDDING_MODEL: str = ""

    # 文档处理
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    class Config:
        env_file = ".env"
        case_sensitive = True

# 缓存装饰器
# 函数只执行一次，后续每次调用直接返回缓存结果，不会重复新建 Settings 对象
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()