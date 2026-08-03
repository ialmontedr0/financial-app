"""OCR API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from reportlab.pdfgen import canvas


def _make_pdf(text_lines: list[str]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 720
    for line in text_lines:
        pdf.drawString(72, y, line)
        y -= 20
    pdf.save()
    return buffer.getvalue()


@pytest.mark.api
class TestOcrAPI:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_status(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ocr_status@test.com", test_password)
        resp = await client.get(
            "/api/v1/ocr/status", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert ".pdf" in data["supported_extensions"]
        assert ".png" in data["supported_extensions"]

    async def test_extract_pdf(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ocr_pdf@test.com", test_password)
        pdf = _make_pdf(
            ["SUPERMERCADO EL TIGRE", "RUC 20123456789", "Total: $123.45", "Fecha: 15/03/2026"]
        )
        resp = await client.post(
            "/api/v1/ocr/extract",
            files={"file": ("recibo.pdf", pdf, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["suggestions"]["amount"] == 123.45
        assert data["suggestions"]["merchant"] == "SUPERMERCADO EL TIGRE"
        assert data["suggestions"]["date"] == "2026-03-15"
        assert data["data"]["text"]

    async def test_extract_unsupported_file(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ocr_bad@test.com", test_password)
        resp = await client.post(
            "/api/v1/ocr/extract",
            files={"file": ("nota.txt", b"hola", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_extract_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/ocr/extract",
            files={"file": ("recibo.png", b"fake", "image/png")},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401


@pytest.mark.api
class TestTransactionsOcrEndpoint:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_transactions_ocr_delegates(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ocr_tx@test.com", test_password)
        pdf = _make_pdf(["CAFETERIA CENTRAL", "Total: 15.00", "2026-06-10"])
        resp = await client.post(
            "/api/v1/transactions/ocr",
            files={"file": ("recibo.pdf", pdf, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["suggestions"]["amount"] == 15.00
        assert data["suggestions"]["merchant"] == "CAFETERIA CENTRAL"
