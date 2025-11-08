"""文档管理路由"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from admin.auth_simple import require_editor
from admin.services.doc_service import (
    list_docs, get_doc_detail, update_doc, delete_doc,
    batch_delete_docs, get_doc_stats
)
from admin.services.audit_service import create_audit_log
from admin.models.audit import AuditLogCreate


router = APIRouter(prefix="/docs", tags=["文档管理"])


class DocUpdate(BaseModel):
    """文档更新请求"""
    title: Optional[str] = None
    chapter: Optional[int] = None
    section_number: Optional[int] = None
    is_published: Optional[bool] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    doc_ids: List[int]
    hard_delete: bool = False


@router.get("")
async def list_documents(
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_editor)
):
    """获取文档列表"""
    docs, total = list_docs(source=source, search=search, limit=limit, offset=offset)
    return {
        "ok": True,
        "data": docs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_editor)):
    """获取文档统计"""
    stats = get_doc_stats()
    return {"ok": True, "stats": stats}


@router.get("/{doc_id}")
async def get_document(
    doc_id: int,
    current_user: dict = Depends(require_editor)
):
    """获取文档详情"""
    doc = get_doc_detail(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {"ok": True, "data": doc}


@router.put("/{doc_id}")
async def update_document(
    doc_id: int,
    doc_update: DocUpdate,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """更新文档"""
    updates = doc_update.dict(exclude_unset=True)
    doc = update_doc(doc_id, updates)
    
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="update",
            resource_type="doc",
            resource_id=doc_id,
            details={"updates": updates},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "data": doc}


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    request: Request,
    hard_delete: bool = Query(False),
    current_user: dict = Depends(require_editor)
):
    """删除文档"""
    success = delete_doc(doc_id, hard_delete=hard_delete)
    
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="delete",
            resource_type="doc",
            resource_id=doc_id,
            details={"hard_delete": hard_delete},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "message": "删除成功"}


@router.post("/batch-delete")
async def batch_delete(
    delete_request: BatchDeleteRequest,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """批量删除文档"""
    count = batch_delete_docs(
        delete_request.doc_ids,
        hard_delete=delete_request.hard_delete
    )
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="batch_delete",
            resource_type="doc",
            details={
                "doc_ids": delete_request.doc_ids,
                "count": count,
                "hard_delete": delete_request.hard_delete
            },
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "deleted_count": count}

