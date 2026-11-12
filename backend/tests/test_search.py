def test_vector_search_returns_scored_results(client, auth_headers):
    r = client.post("/api/search", headers=auth_headers,
                    json={"query": "authentication tokens", "mode": "vector", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "vector"
    assert "results" in body
    if body["results"]:
        assert "score" in body["results"][0]
        assert isinstance(body["results"][0]["score"], (int, float))


def test_keyword_search_mode(client, auth_headers):
    r = client.post("/api/search", headers=auth_headers,
                    json={"query": "JWT", "mode": "keyword", "limit": 5})
    assert r.status_code == 200
    assert r.json()["mode"] == "keyword"


def test_hybrid_search_returns_rrf_score(client, auth_headers):
    r = client.post("/api/search", headers=auth_headers,
                    json={"query": "bearer tokens", "mode": "hybrid", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    for hit in body["results"]:
        if hit["rrf_score"] is not None:
            assert hit["rrf_score"] > 0


def test_invalid_mode_rejected(client, auth_headers):
    r = client.post("/api/search", headers=auth_headers,
                    json={"query": "test", "mode": "magic"})
    assert r.status_code == 422


def test_empty_query_rejected(client, auth_headers):
    r = client.post("/api/search", headers=auth_headers, json={"query": ""})
    assert r.status_code == 422
