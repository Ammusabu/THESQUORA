"""Aggregation pipeline sanity tests via the analytics endpoints."""
from app.repositories import analytics_repository as repo


def test_overview_returns_all_keys(test_user):
    r = repo.overview(test_user["user"]["id"], is_admin=True)
    for k in ("total_documents", "total_chunks", "total_searches",
              "total_conversations", "total_users"):
        assert k in r
        assert isinstance(r[k], int)


def test_categories_returns_list(test_user):
    rows = repo.by_category(test_user["user"]["id"], is_admin=True)
    assert isinstance(rows, list)
    for row in rows:
        assert "category" in row and "count" in row


def test_search_trends_shape(test_user):
    rows = repo.search_trends(test_user["user"]["id"], is_admin=True, days=14)
    assert isinstance(rows, list)
    for row in rows:
        assert "date" in row and "count" in row


def test_popular_documents_shape(test_user):
    rows = repo.popular_documents(test_user["user"]["id"], is_admin=True, limit=5)
    assert isinstance(rows, list)
    for row in rows:
        assert "document_id" in row and "search_count" in row


def test_unanswered_shape(test_user):
    rows = repo.unanswered_queries(test_user["user"]["id"], is_admin=True, limit=5)
    assert isinstance(rows, list)
    for row in rows:
        assert "query" in row and "times" in row
