"""
对话 API
"""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import CurrentUser, get_current_user
from app.models import KnowledgeBase, ChatSession, ChatMessage, TokenUsage, Document
from app.schemas import BaseResponse, ChatSessionResponse, ChatSessionCreate
from app.services import ChatService
from app.rag.pipeline import RAGService
from app.rag.llm import LLMModel
from config import settings

router = APIRouter()


@router.post("", response_model=BaseResponse[ChatSessionResponse])
def create_chat(
        chat: ChatSessionCreate,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    创建对话会话
    """
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == chat.kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id
    ).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    service = ChatService(db)
    session = service.create_session(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        kb_id=chat.kb_id,
        title=chat.title,
    )

    return {
        "code": 200,
        "message": "成功",
        "data": ChatSessionResponse(
            id=session.id,
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            kb_id=session.kb_id,
            title=session.title,
            is_active=session.is_active,
            message_count=0,
            created_at=session.created_at
        )
    }


@router.get("", response_model=BaseResponse[List[ChatSessionResponse]])
def list_sessions(
        kb_id: int = Query(None, description="知识库ID"),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取会话列表
    """
    service = ChatService(db)

    sessions, total = service.list_sessions(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        kb_id=kb_id,
        page=page,
        page_size=page_size,
    )

    result = []
    for session in sessions:
        # 1. 获取消息数
        msg_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count()
        # 2. 查询当前会话最新一条消息（按创建时间倒序取第一条）
        last_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).first()

        result.append(ChatSessionResponse(
            id=session.id,
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            kb_id=session.kb_id,
            title=session.title,
            is_active=session.is_active,
            message_count=msg_count,
            last_message=last_msg.content if last_msg else "",
            last_message_at=last_msg.created_at if last_msg else None,
            created_at=session.created_at
        ))

    return {
        "code": 200,
        "message": "成功",
        "data": result
    }

@router.get("/{session_id}", response_model=BaseResponse)
def get_session(
        session_id: int,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取会话详情和消息历史
    """
    service = ChatService(db)
    session = service.get_session(
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    messages = service.get_messages(session_id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "session": {
                "id": session.id,
                "tenant_id": session.tenant_id,
                "user_id": session.user_id,
                "kb_id": session.kb_id,
                "title": session.title,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat() if session.created_at else None
            },
            "messages": [
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "role": msg.role,
                    "content": msg.content,
                    "meta": msg.meta or {},
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        }
    }

@router.delete("/{session_id}", response_model=BaseResponse)
def delete_session(
        session_id: int,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """删除会话"""
    service = ChatService(db)
    success = service.delete_session(
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    return {
        "code": 200,
        "message": "删除成功",
    }


@router.post("/{session_id}/message", response_model=BaseResponse)
def send_message(
    session_id: int,
    request: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息（RAG 对话）

    请求体:
    {
        "content": "用户问题",
        "kb_id": 1  // 可选，不传则使用会话绑定的知识库
    }
    """
    content = request.get("content")
    kb_id = request.get("kb_id")

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空")

    service = ChatService(db)
    session = service.get_session(session_id, current_user.tenant_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # 确定使用的知识库
    use_kb_id = kb_id or session.kb_id
    if not use_kb_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先选择知识库")

    # 检查知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == use_kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id
    ).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    # 保存用户消息
    user_msg = service.add_message(session_id, "user", content)

    # 获取对话历史
    history_msgs = service.get_messages(session_id)
    history = [{"role": msg.role, "content": msg.content} for msg in history_msgs[:-1]]

    # RAG 生成回答
    try:
        from app.rag.pipeline import RAGService
        rag_service = RAGService(db)
        answer, citations, token_usage = rag_service.generate_answer(
            tenant_id=current_user.tenant_id,
            kb_id=use_kb_id,
            query=content,
            history=history[-6:],  # 最近3轮
            user_department_id=current_user.user.department_id if current_user.user else None
        )
    except ImportError:
        # 如果 RAGService 不存在，返回模拟回答
        answer = f"收到消息: {content}"
        citations = []
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 保存 AI 消息
    assistant_msg = service.add_message(
        session_id,
        "assistant",
        answer,
        meta={"citations": citations}
    )

    # 如果是第一轮对话，自动更新标题
    if len(history_msgs) == 1:
        title = content[:50] + "..." if len(content) > 50 else content
        service.update_title(session_id, title)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "answer": answer,
            "citations": citations,
            "message_id": assistant_msg.id,
            "token_usage": token_usage
        }
    }


@router.post("/{session_id}/message/stream")
def send_message_stream(
    session_id: int,
    request: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息（RAG 对话）- 流式版本
    """
    content = request.get("content")
    kb_id = request.get("kb_id")

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空")

    service = ChatService(db)
    session = service.get_session(session_id, current_user.tenant_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    use_kb_id = kb_id or session.kb_id
    if not use_kb_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先选择知识库")

    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == use_kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id
    ).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    user_department_id = current_user.user.department_id if current_user.user else None

    # 保存用户消息
    user_msg = service.add_message(session_id, "user", content)

    # 获取对话历史
    history_msgs = service.get_messages(session_id)
    history = [{"role": msg.role, "content": msg.content} for msg in history_msgs[:-1]]

    # RAG 检索
    rag_service = RAGService(db)
    chunks = rag_service.retrieve(
        tenant_id=current_user.tenant_id,
        kb_id=use_kb_id,
        query=content,
        top_k=5,
        user_department_id=user_department_id
    )

    # 构建消息
    context = "\n\n".join([
        f"【文档{i+1}】{chunk['payload']['content']}"
        for i, chunk in enumerate(chunks)
    ])

    system_prompt = f"""你是一个专业的知识库问答助手。根据以下参考文档，直接回答用户问题。

参考文档：
{context}

要求：
1. 直接从参考文档中提取相关信息回答用户问题
2. 如果文档中有明确答案，直接给出答案
3. 如果文档中没有相关信息，回答"抱歉，我在知识库中没有找到相关信息"
4. 回答要简洁准确，直接使用文档中的原文"""

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": content})

    # 流式生成回答
    collected_answer = ""
    token_usage = None

    def generate():
        nonlocal collected_answer, token_usage

        for chunk_content in LLMModel.chat_stream(messages):
            collected_answer += chunk_content
            yield f"data: {json.dumps({'content': chunk_content}, ensure_ascii=False)}\n\n"

        # 流式结束后，获取 token 使用量
        try:
            _, token_usage = LLMModel.chat(messages)
        except Exception as e:
            print(f"Failed to get token usage: {e}")

        # 发送完成信号
        citations = []
        for chunk in chunks:
            para_id = chunk["payload"].get("paragraph_id")
            doc_id = chunk["payload"].get("doc_id")
            doc_content = chunk["payload"].get("content", "")
            doc_name = ""
            if doc_id:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc_name = doc.name
            citations.append({
                "paragraph_id": para_id,
                "content": doc_content[:200] + "..." if len(doc_content) > 200 else doc_content,
                "score": chunk["score"],
                "document_name": doc_name
            })

        yield f"data: {json.dumps({'done': True, 'citations': citations, 'token_usage': token_usage}, ensure_ascii=False)}\n\n"

        # 保存 AI 消息
        service.add_message(
            session_id,
            "assistant",
            collected_answer,
            meta={"citations": citations, "token_usage": token_usage}
        )

        # 保存 token 使用统计
        if token_usage:
            model_name = settings.ZHIPU_CHAT_MODEL if settings.ZHIPU_API_KEY else settings.LLM_MODEL
            token_record = TokenUsage(
                tenant_id=current_user.tenant_id,
                user_id=current_user.user_id,
                session_id=session_id,
                model=model_name,
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                total_tokens=token_usage.get("total_tokens", 0)
            )
            db.add(token_record)
            db.commit()

        # 更新会话标题
        if len(history_msgs) == 1:
            title = content[:50] + "..." if len(content) > 50 else content
            service.update_title(session_id, title)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )