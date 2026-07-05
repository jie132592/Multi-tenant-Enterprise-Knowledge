"""
Qdrant 向量数据库初始化脚本

运行方式:
    python init_qdrant.py

确保 Qdrant 服务已启动:
    docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
"""
from qdrant_client import QdrantClient

from config import settings


def init_qdrant():
    """初始化Qdrant"""
    print(f"连接 Qdrant: {settings.QDRANT_URL}")

    client = QdrantClient(url=settings.QDRANT_URL, timeout=settings.QDRANT_TIMEOUT)
    # 检查是否存在
    collection_name = settings.QDRANT_COLLECTION
    print(f"检查 collection: {collection_name}")

    try:
        client.get_collection(collection_name)
        print(f"Collection '{collection_name}' 已存在")
    except Exception as e:
        # 创建 collection
        print(f"创建 collection: {collection_name}")
        from qdrant_client.http import models
        client.create_collection(
            collection_name=collection_name,
            # 向量全局参数
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' 创建成功")

    print("初始化完成!")

if __name__ == '__main__':
    init_qdrant()