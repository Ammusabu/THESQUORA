from fastapi import APIRouter, Depends, Query

from app.middleware.auth_middleware import get_current_user
from app.repositories import analytics_repository as repo
from app.schemas.analytics import (
    CategoryResponse, OverviewResponse, PopularDocsResponse,
    SearchTrendResponse, TopCategoriesResponse, UnansweredResponse,
    MLPerformanceResponse, SearchRelevanceResponse,
    UnansweredTrendsResponse, UsefulDocsResponse,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse)
def overview(current_user: dict = Depends(get_current_user)):
    return repo.overview(current_user["id"], current_user["role"] == "admin")


@router.get("/categories", response_model=CategoryResponse)
def categories(current_user: dict = Depends(get_current_user)):
    return {"items": repo.by_category(current_user["id"], current_user["role"] == "admin")}


@router.get("/search-trends", response_model=SearchTrendResponse)
def search_trends(
    days: int = Query(14, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.search_trends(
        current_user["id"], current_user["role"] == "admin", days=days)}


@router.get("/popular-documents", response_model=PopularDocsResponse)
def popular_documents(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.popular_documents(
        current_user["id"], current_user["role"] == "admin", limit=limit)}


@router.get("/unanswered-queries", response_model=UnansweredResponse)
def unanswered_queries(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.unanswered_queries(
        current_user["id"], current_user["role"] == "admin", limit=limit)}


@router.get("/top-categories-searched", response_model=TopCategoriesResponse)
def top_categories_searched(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.top_searched_categories(
        current_user["id"], current_user["role"] == "admin", limit=limit)}


@router.get("/ml-performance", response_model=MLPerformanceResponse)
def ml_performance(current_user: dict = Depends(get_current_user)):
    return repo.ml_performance(
        user_id=current_user["id"], is_admin=current_user["role"] == "admin",
    )


@router.get("/search-relevance", response_model=SearchRelevanceResponse)
def search_relevance(
    days: int = Query(30, ge=1, le=180),
    current_user: dict = Depends(get_current_user),
):
    return repo.search_relevance(
        user_id=current_user["id"], is_admin=current_user["role"] == "admin", days=days,
    )


@router.get("/unanswered-trends", response_model=UnansweredTrendsResponse)
def unanswered_trends(
    days: int = Query(60, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.unanswered_trends(
        user_id=current_user["id"], is_admin=current_user["role"] == "admin", days=days,
    )}


@router.get("/most-useful-documents", response_model=UsefulDocsResponse)
def most_useful_documents(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    return {"items": repo.most_useful_documents(
        user_id=current_user["id"], is_admin=current_user["role"] == "admin", limit=limit,
    )}
