"""题库管理路由"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from admin.auth import require_editor
from admin.services.question_service import (
    list_questions, get_question_detail, update_question, delete_question,
    batch_delete_questions, get_question_stats
)
from admin.services.audit_service import create_audit_log
from admin.models.audit import AuditLogCreate


router = APIRouter(prefix="/questions", tags=["题库管理"])


class QuestionUpdate(BaseModel):
    """题目更新请求"""
    qtype: Optional[str] = None
    stem_md: Optional[str] = None
    options_json: Optional[dict] = None
    answer_text: Optional[str] = None
    explanation_md: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[int] = None
    is_published: Optional[bool] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    qids: List[int]
    hard_delete: bool = False


@router.get("")
async def list_question_items(
    qtype: Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_editor)
):
    """获取题目列表"""
    questions, total = list_questions(
        qtype=qtype,
        difficulty=difficulty,
        search=search,
        limit=limit,
        offset=offset
    )
    return {
        "ok": True,
        "data": questions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_editor)):
    """获取题库统计"""
    stats = get_question_stats()
    return {"ok": True, "stats": stats}


@router.get("/{qid}")
async def get_question(
    qid: int,
    current_user: dict = Depends(require_editor)
):
    """获取题目详情"""
    question = get_question_detail(qid)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    return {"ok": True, "data": question}


@router.put("/{qid}")
async def update_question_route(
    qid: int,
    question_update: QuestionUpdate,
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """更新题目"""
    updates = question_update.dict(exclude_unset=True)
    question = update_question(qid, updates)
    
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="update",
            resource_type="question",
            resource_id=qid,
            details={"updates": updates},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "data": question}


@router.delete("/{qid}")
async def delete_question_route(
    qid: int,
    hard_delete: bool = Query(False),
    request: Request,
    current_user: dict = Depends(require_editor)
):
    """删除题目"""
    success = delete_question(qid, hard_delete=hard_delete)
    
    if not success:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="delete",
            resource_type="question",
            resource_id=qid,
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
    """批量删除题目"""
    count = batch_delete_questions(
        delete_request.qids,
        hard_delete=delete_request.hard_delete
    )
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="batch_delete",
            resource_type="question",
            details={
                "qids": delete_request.qids,
                "count": count,
                "hard_delete": delete_request.hard_delete
            },
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "deleted_count": count}

