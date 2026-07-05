"""
向量化模块

封装 Embedding 模型，支持 OpenAI / 智谱
"""
from typing import List, Optional

from config import settings


class EmbeddingModel:
    """模型"""
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                from langchain_openai import OpenAIEmbeddings

                if settings.ZHIPU_API_KEY:
                    base_url = settings.ZHIPU_BASE_URL.rstrip('/')
                    cls._model = OpenAIEmbeddings(
                        model=settings.ZHIPU_EMBEDDING_MODEL,
                        openai_api_key=settings.ZHIPU_API_KEY,
                        openai_api_base=base_url,
                        check_embedding_ctx_length=False
                    )
                else:
                    base_url = settings.OPENAI_BASE_URL.rstrip('/')
                    cls._model = OpenAIEmbeddings(
                        model=settings.EMBEDDING_MODEL,
                        openai_api_key=settings.OPENAI_API_KEY,
                        openai_api_base=base_url,
                        check_embedding_ctx_length=False
                    )
            except Exception as e:
                print(f"Failed to load embedding model: {e}")
                return None
        return cls._model

    @classmethod
    def embed_texts(cls, texts: List[str]) -> Optional[List[List[float]]]:
        """批量将文本转换为向量"""
        model = cls.get_model()
        if model is None:
            return None
        try:
            return model.embed_documents(texts)
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            return None

    @classmethod
    def embed_query(cls, query: str) -> Optional[List[float]]:
        """将查询文本转为向量化"""
        model = cls.get_model()
        if model is None:
            return None
        try:
            return model.embed_query(query)
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            return None