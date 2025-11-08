"""分片管理路由"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from admin.auth_simple import require_editor
from admin.services.chunk_service import (
    list_chunks, get_chunk_detail, update_chunk, delete_chunk,
    batch_verify_chunks, batch_delete_chunks, get_chunk_stats
)
from admin.services.audit_service import create_audit_log
from admin.models.audit import AuditLogCreate


router = APIRouter(prefix="/chunks", tags=["分片管理"])


class ChunkUpdate(BaseModel):
    """分片更新请求"""
    content_md: Optional[str] = None
    content_plain: Optional[str] = None
    kind: Optional[str] = None
    heading_h1: Optional[str] = None
    heading_h2: Optional[str] = None
    is_verified: Optional[bool] = None
    quality_score: Optional[int] = None


class BatchVerifyRequest(BaseModel):
    """批量审核请求"""
    chunk_ids: List[int]
    verified: bool = True


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    chunk_ids: List[int]
    hard_delete: bool = False


@router.get("")
async def list_chunk_items(
    doc_id: Optional[int] = Query(None),
    kind: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    verified_only: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_editor)
):
    """获取分片列表"""
    chunks, total = list_chunks(
        doc_id=doc_id,
        kind=kind,
        search=search,
        verified_only=verified_only,
        limit=limit,
        offset=offset
    )
    return {
        "ok": True,
        "data": chunks,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_editor)):
    """获取分片统计"""
    stats = get_chunk_stats()
    return {"ok": True, "stats": stats}


@router.get("/{chunk_id}")
async def get_chunk(
    chunk_id: int,
    current_user: dict = Depends(require_editor)
):
    """获取分片详情"""
    chunk = get_chunk_detail(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="分片不存在")
    
    return {"ok": True, "data": chunk}


@router.put("/{chunk_id}")
async def update_chunk_route(
    chunk_id: int,
    chunk_update: ChunkUpdate,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """更新分片"""
    updates = chunk_update.dict(exclude_unset=True)
    chunk = update_chunk(chunk_id, updates)
    
    if not chunk:
        raise HTTPException(status_code=404, detail="分片不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="update",
            resource_type="chunk",
            resource_id=chunk_id,
            details={"updates": updates},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "data": chunk}


@router.delete("/{chunk_id}")
async def delete_chunk_route(
    chunk_id: int,
    request: Request,
    hard_delete: bool = Query(False),
    current_user: dict = Depends(require_editor)
):
    """删除分片"""
    success = delete_chunk(chunk_id, hard_delete=hard_delete)
    
    if not success:
        raise HTTPException(status_code=404, detail="分片不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="delete",
            resource_type="chunk",
            resource_id=chunk_id,
            details={"hard_delete": hard_delete},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "message": "删除成功"}


@router.post("/batch-verify")
async def batch_verify(
    verify_request: BatchVerifyRequest,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """批量审核分片"""
    count = batch_verify_chunks(
        verify_request.chunk_ids,
        verified=verify_request.verified
    )
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="batch_verify",
            resource_type="chunk",
            details={
                "chunk_ids": verify_request.chunk_ids,
                "count": count,
                "verified": verify_request.verified
            },
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "verified_count": count}


@router.post("/batch-delete")
async def batch_delete(
    delete_request: BatchDeleteRequest,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """批量删除分片"""
    count = batch_delete_chunks(
        delete_request.chunk_ids,
        hard_delete=delete_request.hard_delete
    )
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="batch_delete",
            resource_type="chunk",
            details={
                "chunk_ids": delete_request.chunk_ids,
                "count": count,
                "hard_delete": delete_request.hard_delete
            },
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "deleted_count": count}

