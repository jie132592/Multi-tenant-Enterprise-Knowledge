"""
向量存储模块

封装 Qdrant 客户端操作
"""
from typing import Optional, List

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from config import settings


class VectorStore:
    """向量存储（Qdrant）"""
    # 类私有属性，全局唯一Qdrant客户端，初始为空，实现单例
    _client: Optional[QdrantClient] = None

    @classmethod
    # 类方法：全局只创建一次客户端连接，复用连接
    def get_client(cls) -> QdrantClient:
        # 如果客户端还没实例化，新建连接
        if cls._client is None:
            cls._client = QdrantClient(
                url=settings.QDRANT_URL,
                timeout=settings.QDRANT_TIMEOUT,
            )
        return cls._client

    @classmethod
    def ensure_collection(cls):
        # 类方法：检查向量集合是否存在，不存在则自动创建
        # 获取单例客户端
        client = cls.get_client()
        try:
            client.get_collection(settings.QDRANT_COLLECTION)
        except (UnexpectedResponse, Exception):
            # 读取失败=集合不存在，进入创建逻辑
            # 根据配置自动适配向量维度：智谱Embedding维度 / 默认1536
            vector_size = settings.ZHIPU_EMBEDDING_DIM if settings.ZHIPU_API_KEY else 1536
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vector_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    @classmethod
    def upsert_vectors(
            cls,
            ids: List[int], # 向量唯一ID列表
            vectors: List[List[float]], # 浮点向量数组列表
            payloads: List[dict] # 每条向量绑定的业务元数据字典
    ):
        """插入或更新向量"""
        try:
            # 批量写入向量：ID存在则更新，不存在则新增
            client = cls.get_client()
            # 先确认集合存在
            cls.ensure_collection()
            client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                # 组装每条向量PointStruct对象
                points=[
                    models.PointStruct(
                        id=point_id,  # 向量唯一编号
                        vector=vector,  # 嵌入向量数值
                        payload=payload,  # 附加业务（文档ID、租户ID、知识库ID等）
                    )
                    for point_id, vector, payload in zip(ids, vectors, payloads)
                ]
            )
            return True
        except Exception as e:
            print(f"Upsert vectors failed: {e}")  # 打印异常日志
            return False  # 写入失败返回False

    @classmethod
    def search(
            cls,
            query_vector: List[float], # 用户/问题转换后的查询向量
            top_k: int = 5,
            filter_conditions: dict = None, # 业务过滤条件(租户、知识库筛选等)
    ) -> List[dict]:
        """搜索向量"""
        # 向量相似度检索，支持业务字段过滤
        try:
            client = cls.get_client()
            filter_obj = None
            # 如果传入过滤条件，构建Qdrant过滤对象
            if filter_conditions:
                must = []
                for k, v in filter_conditions.items():
                    # models.FieldCondition 是 Qdrant Python SDK 里用来按 payload 字段精确过滤的条件结构体
                    must.append(models.FieldCondition(
                        key=k, # 过滤字段名（tenant_id、kb_id）
                        match=models.MatchValue(value=v) # 精确匹配值
                    ))
                # 组合所有AND条件
                filter_obj = models.Filter(must=must)

            # 新版统一接口，支持向量检索、全文检索、混合检索、重排,替换老版search
            results = client.query_points(
                collection_name=settings.QDRANT_COLLECTION,
                query=query_vector, # 查询向量
                limit=top_k, # 返回条数限制
                query_filter=filter_obj # 业务过滤
            )

            return [
                {
                    "id": hit.id, # 匹配向量ID
                    "score": hit.score, # 相似度分数
                    "payload": hit.payload
                }
                for hit in results.points
            ]
        except Exception as e:
            print(f"Search failed: {e}")
            return []  # 检索异常返回空列表

    @classmethod
    def delete_by_ids(
            cls,
            ids: List[int],
    ) -> bool:
        """删除向量"""
        # 根据向量ID批量删除向量数据
        try:
            client = cls.get_client()
            client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                # 按ID列表删除指定向量点
                points_selector=models.PointIdsList(points=ids)
            )
            return True
        except Exception as e:
            print(f"Delete vectors failed: {e}")
            return False

    @classmethod
    def delete_by_filter(cls, filter_conditions: dict) -> bool:
        """按条件删除"""
        # 按业务条件批量删除（比如删除某个知识库全部向量）
        try:
            client = cls.get_client()
            must = []
            for k, v in filter_conditions.items():
                must.append(
                    models.FieldCondition(
                        key=k,
                        match=models.MatchValue(value=v)
                    )
                )
            client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                # 使用过滤器批量删除符合条件的所有向量
                points_selector=models.FilterSelector(
                    filter=models.Filter(must=must),
                )
            )
            return True
        except Exception as e:
            print(f"Delete vectors failed: {e}")
            return False