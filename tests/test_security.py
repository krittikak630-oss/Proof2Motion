from .conftest import upload


def test_rejects_unsupported_extension(client):
    res = client.post("/api/analyze", files=upload("evil.exe", b"MZ", "application/octet-stream"))
    assert res.status_code == 400


def test_rejects_fake_pdf(client):
    res = client.post("/api/analyze", files=upload("x.pdf", b"not really a pdf", "application/pdf"))
    assert res.status_code == 400 and "PDF" in res.json()["detail"]


def test_rejects_binary_disguised_as_text(client):
    res = client.post("/api/analyze", files=upload("x.txt", b"abc\x00\x01\x02"))
    assert res.status_code == 400


def test_rejects_oversized_file(make_client):
    client = make_client(max_file_bytes=10)
    res = client.post("/api/analyze", files=upload(content=b"x" * 100))
    assert res.status_code in (400, 413)


def test_rejects_too_many_files(make_client):
    client = make_client(max_files=2)
    files = [("files", (f"{i}.txt", b"hello world evidence", "text/plain")) for i in range(3)]
    assert client.post("/api/analyze", files=files).status_code == 400


def test_rate_limit(make_client):
    client = make_client(rate_limit_per_minute=2)
    codes = [client.post("/api/analyze", files=upload()).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_security_headers_present(client):
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in headers["content-security-policy"]
    assert headers["cache-control"] == "no-store"


def test_no_path_traversal(client):
    for path in ("/..%2f..%2f..%2fetc/passwd", "/%2e%2e/%2e%2e/etc/passwd", "/../../etc/passwd"):
        res = client.get(path)
        assert "root:" not in res.text


def test_unknown_api_route_is_404_json(client):
    assert client.get("/api/nope").status_code == 404


def test_docs_hidden_in_production(make_client):
    client = make_client(environment="production")
    assert client.get("/api/docs").status_code != 200
