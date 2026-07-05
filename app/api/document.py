from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import CurrentUser, get_current_user
from app.core.permissions import Permission
from app.models import User
from app.schemas import BaseResponse, DocumentUploadResponse, DocumentListResponse, DocumentResponse
from app.services import DocumentService, ParagraphService

router = APIRouter()


@router.post("/upload/{kb_id}", response_model=BaseResponse[DocumentUploadResponse])
async def upload_document(
        kb_id: int,
        file: UploadFile = File(...),
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    """
    上传文档

    支持 txt, md, pdf 文件
    需要文档上传权限
    """
    from app.core.permissions import Permission, has_permission
    # 检查上传权限
    if not has_permission(current_user.user.role, Permission.DOC_UPLOAD):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足, 需要文档上传权限")

    # 检查文件类型
    allowed_types = ['text/plain', 'text/markdown', 'application/octet-stream', 'application/pdf']
    if file.content_type not in allowed_types and not file.filename.endswith((".pdf", ".txt", ".md")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 .txt、.md 和 .pdf 文件"
        )

    # 读取文件内容
    content = await file.read()
    # 检查知识库是否存在
    service = DocumentService(db)

    from app.models import KnowledgeBase
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id
    ).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    # 根据文件类型处理
    if file.filename.endswith(".pdf"):
        # PDF 文件：存储原始字节
        doc = service.create(
            tenant_id=current_user.tenant_id,
            kb_id=kb_id,
            content="",
            user_id=current_user.user_id,
            name=file.filename,
            raw_content=content
        )
        return {
            "code": 200,
            "message": "上传成功，正在解析...",
            "data": {
                "id": doc.id,
                "name": doc.name,
                "status": doc.status,
                "char_length": doc.char_length,
                "message": "上传成功"
            }
        }
    else:
        # 文本文件：解码并存储
        try:
            content_type = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件编码不支持，请使用 UTF-8 或 GBK 编码"
            )

        doc = service.create(
            tenant_id=current_user.tenant_id,
            kb_id=kb_id,
            user_id=current_user.user_id,
            name=file.filename,
            content=content_type
        )

        return {
            "code": 200,
            "message": "上传成功，正在解析...",
            "data": {
                "id": doc.id,
                "name": doc.name,
                "status": doc.status,
                "char_length": doc.char_length,
                "message": "上传成功"
            }
        }


@router.get("/list/{kb_id}", response_model=BaseResponse[List[DocumentListResponse]])
def list_documents(
        kb_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取文档列表"""
    from app.models import KnowledgeBase
    # 检查知识库权限
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id
    ).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    service = DocumentService(db)
    docs, total = service.list_by_kb(kb_id, current_user.tenant_id, page, page_size)

    results = []
    for doc in docs:
        # 获取上传者用户名
        uploader_username = ""
        if doc.user_id:
            user = db.query(User).filter(User.id == doc.user_id).first()
            if user:
                uploader_username = user.username

        results.append(DocumentListResponse(
            id=doc.id,
            kb_id=doc.kb_id,
            name=doc.name,
            char_length=doc.char_length,
            status=doc.status,
            paragraph_count=service.get_paragraph_count(doc.id),
            uploader_username=uploader_username,
            created_at=doc.created_at
        ))

    return {
        "code": 200,
        "message": "success",
        "data": results
    }


@router.get("/{doc_id}", response_model=BaseResponse[DocumentResponse])
def get_document(
        doc_id: int,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取文档详情"""
    service = DocumentService(db)
    doc = service.get(doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    uploader_username = ""
    if doc.user_id:
        user = db.query(User).filter(User.id == doc.user_id).first()
        if user:
            uploader_username = user.username

    return {
        "code": 200,
        "message": "success",
        "data": DocumentResponse(
            id=doc.id,
            tenant_id=doc.tenant_id,
            kb_id=doc.kb_id,
            name=doc.name,
            char_length=doc.char_length,
            status=doc.status,
            error_message=doc.error_message or "",
            paragraph_count=service.get_paragraph_count(doc.id),
            user_id=doc.user_id,
            uploader_username=uploader_username,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
    }


@router.delete("/{doc_id}", response_model=BaseResponse)
def delete_document(
        doc_id: int,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """删除文档"""
    from app.core.permissions import Permission, has_permission

    # 检查删除权限
    if not has_permission(current_user.user.role, Permission.DOC_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要文档删除权限"
        )

    service = DocumentService(db)
    success = service.delete(doc_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    return {
        "code": 200,
        "message": "删除成功"
    }


@router.post("/{doc_id}/parse", response_model=BaseResponse)
def parse_document(
        doc_id: int,
        background_tasks: BackgroundTasks,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    解析分块
    异步任务
    :param doc_id:
    :param background_tasks:
    :param current_user:
    :param db:
    :return:
    """
    service = DocumentService(db)
    # 根据文档ID + 当前用户租户校验文档归属（多租户隔离，防止越权解析别人文档）
    doc = service.get(doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # 修改文档状态为 1=处理中，前端可轮询查看任务进度
    service.update_status(doc_id, 1)

    # FastAPI内置后台任务：把耗时的文档解析、切片、向量化、向量入库丢到后台执行
    background_tasks.add_task(parse_document_task, doc_id, current_user.tenant_id)
    return {
        "code": 200,
        "message": "解析任务已启动"
    }

def parse_document_task(doc_id: int, tenant_id: int):
    """文档解析后台任务"""
    from app import SessionLocal
    # 手动新建独立数据库会话，不能复用接口里过期的db连接
    db = SessionLocal()
    try:
        # 实例化文档、段落业务服务
        service = DocumentService(db)
        para_service = ParagraphService(db)

        # 校验文档归属：防止跨租户越权、文档已被删除
        doc = service.get(doc_id, tenant_id)
        if not doc:
            return
        try:
            # 延迟导入文档解析工具，仅任务执行时加载
            from app.rag.parser import DocumentParser
            # 判断文件类型，走不同解析逻辑
            if doc.name.lower().endswith(".pdf") and doc.raw_content:
                # PDF二进制内容解析，返回切分好的文本块列表
                chunks = DocumentParser.parse_pdf(doc.raw_content)
            else:
                chunks = DocumentParser.parse_text(doc.content)

            # 先删除该文档下所有旧段落（覆盖重解析场景）
            para_service.delete_by_doc(doc_id)

            # 批量插入所有分块到段落表MySQL，返回段落对象列表（带自增id）
            paragraphs = para_service.create_batch(tenant_id, doc_id, chunks)

            # 批量段落循环向量化、写入Qdrant
            try:
                from app.rag.pipeline import RAGService
                rag_service = RAGService(db)
                # 逐条循环，每一段单独调用一次向量入库
                for para in paragraphs:
                    rag_service.index_paragraph(
                        tenant_id,
                        kb_id=doc.kb_id,
                        doc_id=doc_id,
                        para_id=para.id,
                        content=para.content,
                    )
            except Exception as e:
                # 向量库异常只打印日志，不阻断整体任务
                print(f"向量索引失败: {e}")

            # 全部流程无异常，文档状态改为2=解析完成
            service.update_status(doc_id, 2)
        except Exception as e:
            # 解析/切分异常，标记文档状态3=失败，并记录错误详情
            service.update_status(doc_id, 3, str(e))
    finally:
        db.close()

@router.get("/{doc_id}/content", response_model=BaseResponse)
def get_document_content(
    doc_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文档内容"""
    service = DocumentService(db)
    para_service = ParagraphService(db)
    doc = service.get(doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # 如果是 PDF 且没有直接 content，返回段落内容拼接
    if doc.name.lower().endswith('.pdf') and not doc.content:
        paragraphs = para_service.get_active_by_doc(doc_id)
        content = "\n\n".join([p.content for p in paragraphs])
        char_length = len(content)
    else:
        content = doc.content
        char_length = doc.char_length

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": doc.id,
            "name": doc.name,
            "content": content,
            "char_length": char_length
        }
    }
