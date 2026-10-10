def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_database_is_up(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_info_exposes_hostname_and_version(client):
    data = client.get("/api/info").json()
    assert data["hostname"]
    assert data["version"]


def test_create_then_list_items(client):
    created = client.post("/api/items", json={"name": "premier"})
    assert created.status_code == 201
    assert created.json()["name"] == "premier"

    items = client.get("/api/items").json()
    assert [i["name"] for i in items] == ["premier"]


def test_name_is_validated(client):
    assert client.post("/api/items", json={"name": ""}).status_code == 422
    assert client.post("/api/items", json={"name": "   "}).status_code == 422
    assert client.post("/api/items", json={"name": "x" * 101}).status_code == 422
    assert client.post("/api/items", json={}).status_code == 422


def test_delete_item(client):
    item_id = client.post("/api/items", json={"name": "a supprimer"}).json()["id"]
    assert client.delete(f"/api/items/{item_id}").status_code == 204
    assert client.get("/api/items").json() == []
    assert client.delete(f"/api/items/{item_id}").status_code == 404


def test_cache_miss_then_hit(client, fake_cache):
    client.post("/api/items", json={"name": "mis en cache"})

    first = client.get("/api/items")
    second = client.get("/api/items")

    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    assert second.json() == first.json()


def test_cache_is_invalidated_after_write(client, fake_cache):
    client.get("/api/items")  # remplit le cache
    client.post("/api/items", json={"name": "nouveau"})

    response = client.get("/api/items")
    assert response.headers["X-Cache"] == "MISS"
    assert [i["name"] for i in response.json()] == ["nouveau"]


def test_response_tells_which_pod_served_it(client):
    assert client.get("/health").headers["X-Served-By"]


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_stress_is_bounded(client):
    assert client.get("/api/stress?iterations=1000").status_code == 200
    assert client.get("/api/stress?iterations=99999999").status_code == 422
