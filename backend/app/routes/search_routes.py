from fastapi import APIRouter, Depends, Query

from app.middleware.auth_middleware import get_current_user
from app.schemas.search import (
    SearchHistoryResponse, SearchRequest, SearchResponse,
)
from app.services import search_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, current_user: dict = Depends(get_current_user)):
    return search_service.search(
        current_user=current_user,
        query=payload.query,
        mode=payload.mode,
        limit=payload.limit,
        offset=payload.offset,
        category=payload.category,
        department=payload.department,
    )


@router.get("/history", response_model=SearchHistoryResponse)
def history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return search_service.history(current_user=current_user, page=page, limit=limit)
