import asyncio

import httpx

from app.main import app


async def request(method, url, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


def test_health():
    response = asyncio.run(request("GET", "/health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_file_routes_require_authentication():
    response = asyncio.run(request("GET", "/api/v1/files"))

    assert response.status_code == 401


def test_ingest_validates_payload():
    response = asyncio.run(request("POST", "/api/v1/files/ingest", headers={"X-User-Id": "user-a"}, json={}))

    assert response.status_code == 422
