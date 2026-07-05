"""
RAG Pipeline

检索 -> 生成 完整流程
"""
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models import KnowledgeBase, Document
from app.rag.llm import LLMModel
from app.rag.store import VectorStore
from app.rag.vectorizer import EmbeddingModel


class RAGService:
    """rag服务"""

    def __init__(self, db: Session):
        self.db = db

    def retrieve(
            self,
            tenant_id: int,
            kb_id: int,
            query: str,
            top_k: int = 5,
            min_score: float = 0.2,
            user_department_id: int = None
    ) -> List[dict]:
        """
        完整召回逻辑：向量化 -> Qdrant向量检索 -> 分数过滤 -> 部门权限二次过滤
        Args:
            tenant_id: 租户 ID
            kb_id: 知识库 ID
            query: 查询文本
            top_k: 返回数量
            min_score: 最低相似度分数
            user_department_id: 用户所属部门 ID（用于部门可见性过滤）

        Returns:
            检索结果列表
        """
        query_vector = EmbeddingModel.embed_query(query)
        if query_vector is None:
            return []

        # 如果有部门权限过滤，先多召回3倍数据，后续再过滤裁剪，防止权限过滤后数据不足
        results = VectorStore.search(
            query_vector=query_vector,
            top_k=top_k * 3 if user_department_id else top_k,
            filter_conditions={"tenant_id": tenant_id, "kb_id": kb_id},
        )
        # 3. 过滤低分向量，只保留相似度≥0.2的片段
        results = [r for r in results if r.get("score") and r["score"] >= min_score]

        # 4. 部门权限过滤逻辑（可选）
        if user_department_id:
            accessible_kb_ids = set()
            # 取出本次召回所有结果对应的kb_id，去数据库查询知识库权限配置
            kb_id_list = [r["payload"].get("kb_id") for r in results]
            all_kbs = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.id.in_(kb_id_list)
            ).all()

            # 遍历知识库，筛选当前用户有权查看的知识库ID
            for kb in all_kbs:
                # 两种可见权限放行：公开知识库 / 部门知识库且和用户部门匹配
                if kb.visibility == "public" or (
                        kb.visibility == "department" and kb.department_id == user_department_id):
                    accessible_kb_ids.add(kb.id)

            # 只保留有权限的片段，最后截断到top_k条
            results = [r for r in results if r["payload"].get("kb_id") in accessible_kb_ids][:top_k]

        return results

    def generate_answer(
            self,
            tenant_id: int,
            kb_id: int,
            query: str,
            history: List[dict] = None,
            top_k: int = 5,
            user_department_id: int = None
    ) -> Tuple[str, List[dict], dict]:
        """
        RAG完整问答入口：检索段落 → 拼装引用信息 → 调用LLM生成答案

        Returns:
            (回答文本, 引用列表, token使用信息)
        """
        # 第一步：执行向量检索，拿到相关知识库片段
        chunks = self.retrieve(
            tenant_id=tenant_id,
            kb_id=kb_id,
            query=query,
            top_k=top_k,
            user_department_id=user_department_id
        )
        # 没有检索到任何匹配段落，直接返回固定提示
        if not chunks:
            return "抱歉，我在知识库中没有找到与您问题相关的信息。", [], None

        citations = []
        # 遍历检索到的段落，拼装前端展示用的引用来源（文档名、片段预览、相似度分数）
        for chunk in chunks:
            para_id = chunk["payload"].get("paragraph_id")
            doc_id = chunk["payload"].get("doc_id")
            content = chunk["payload"].get("content", "")

            doc_name = ""
            # 根据doc_id查询数据库，获取文档原始名称
            if doc_id:
                doc = self.db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc_name = doc.name
            # 片段过长截断，末尾加省略号
            preview_text = content[:200] + "..." if len(content) > 200 else content
            citations.append(
                {
                    "paragraph_id": para_id,
                    "content": preview_text,
                    "score": chunk["score"],
                    "document_name": doc_name,
                }
            )
        # 调用带RAG提示词封装的大模型接口，传入检索到的上下文+对话历史
        answer, usage = LLMModel.chat_with_rag(query, chunks, history)

        # LLM调用失败兜底文案
        if answer is None:
            return "抱歉，AI 服务暂时不可用，请稍后重试。", [], None

        # 返回三元组：AI回答、引用来源列表、token计费用量
        return answer, citations, usage

    def index_paragraph(
        self,
        tenant_id: int,
        kb_id: int,
        doc_id: int,
        para_id: int,
        content: str
    ) -> bool:
        """将单一段落写入向量库建立索引（文档切片后调用）"""
        vectors = EmbeddingModel.embed_texts([content])
        if vectors is None:
            return False

        return VectorStore.upsert_vectors(
            ids=[para_id],
            vectors=vectors,
            payloads=[{
                "tenant_id": tenant_id,
                "kb_id": kb_id,
                "doc_id": doc_id,
                "paragraph_id": para_id,
                "content": content
            }]
        )

    def delete_paragraph_index(self, para_id: int) -> bool:
        """删除段落索引"""
        return VectorStore.delete_by_ids([para_id])

    def delete_kb_index(self, tenant_id: int, kb_id: int) -> bool:
        """删除知识库的所有索引"""
        return VectorStore.delete_by_filter({
            "tenant_id": tenant_id,
            "kb_id": kb_id
        })
