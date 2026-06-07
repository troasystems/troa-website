"""
Smoke tests for refactored backend after server.py modularization.
Verifies public GET endpoints, auth-protected 401 responses, membership POST,
WebSocket endpoint existence, and invoice PDF endpoint.
"""
import os
import pytest
import requests
import uuid
from websocket import create_connection, WebSocketException

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://websocket-app-3.preview.emergentagent.com').rstrip('/')
WS_BASE = BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://')


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
class TestHealth:
    def test_api_health(self, session):
        r = session.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_api_root(self, session):
        r = session.get(f"{BASE_URL}/api/", timeout=15)
        assert r.status_code == 200
        assert "TROA" in r.json().get("message", "")


# ---------- Public GETs (refactored routes) ----------
class TestPublicEndpoints:
    def test_committee_get(self, session):
        r = session.get(f"{BASE_URL}/api/committee", timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_amenities_get(self, session):
        r = session.get(f"{BASE_URL}/api/amenities", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # If amenities exist, verify structure (no _id leakage)
        for item in data:
            assert "_id" not in item
            assert "id" in item

    def test_gallery_get(self, session):
        r = session.get(f"{BASE_URL}/api/gallery", timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_events_get(self, session):
        r = session.get(f"{BASE_URL}/api/events", timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)


# ---------- Caching headers (Cache-Control middleware) ----------
class TestCacheHeaders:
    def test_cacheable_committee(self, session):
        r = session.get(f"{BASE_URL}/api/committee", timeout=15)
        cc = r.headers.get("Cache-Control", "")
        # Accept either cache control or proxy override (some CDNs override)
        assert cc, "Cache-Control header missing"

    def test_no_cache_users(self, session):
        # users endpoint should be no-store (also returns 401 unauthed)
        r = session.get(f"{BASE_URL}/api/users", timeout=15)
        cc = r.headers.get("Cache-Control", "")
        assert "no-store" in cc or "no-cache" in cc


# ---------- Auth-protected endpoints (expect 401) ----------
class TestAuthProtected:
    def test_feedback_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/feedback", timeout=15)
        assert r.status_code == 401, f"Expected 401 got {r.status_code}: {r.text}"

    def test_invoices_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/invoices", timeout=15)
        assert r.status_code == 401, f"Expected 401 got {r.status_code}: {r.text}"

    def test_users_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/users", timeout=15)
        assert r.status_code == 401, f"Expected 401 got {r.status_code}: {r.text}"

    def test_membership_get_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/membership", timeout=15)
        assert r.status_code == 401

    def test_invoice_pdf_requires_auth(self, session):
        invoice_id = "eee3f57b-9392-40bd-af53-994158a93928"
        r = session.get(f"{BASE_URL}/api/invoices/{invoice_id}/pdf", timeout=20)
        # 401 (auth missing) is expected; route must exist (not 404)
        assert r.status_code == 401, f"Expected 401 got {r.status_code}: {r.text[:200]}"

    def test_pending_count_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/invoices/pending/count", timeout=15)
        assert r.status_code == 401


# ---------- POST membership (public) ----------
class TestMembership:
    def test_membership_create(self, session):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "firstName": f"TEST_Applicant_{unique}",
            "lastName": "Smoke",
            "email": f"test_{unique}@example.com",
            "phone": "+919876543210",
            "villaNo": "TEST-001",
            "message": "Automated smoke test"
        }
        r = session.post(f"{BASE_URL}/api/membership", json=payload, timeout=25)
        assert r.status_code in (200, 201), f"Got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("email") == payload["email"]
        assert data.get("firstName") == payload["firstName"]
        assert "id" in data


# ---------- WebSocket endpoint accessibility ----------
class TestWebSocket:
    def test_chat_ws_endpoint_exists(self):
        """WS endpoint should exist; without a valid token it should close (1008/4401) not 404."""
        url = f"{WS_BASE}/api/chat/ws/mc-group?token=invalid_test_token"
        try:
            ws = create_connection(url, timeout=10)
            # If we connected, server should send a close/error then close
            try:
                ws.recv()
            except Exception:
                pass
            ws.close()
            # Connection established -> endpoint exists
            assert True
        except WebSocketException as e:
            msg = str(e).lower()
            # 403/1008/4401 indicate auth rejection but endpoint exists.
            # 404 / "not found" would mean route is missing.
            assert "404" not in msg and "not found" not in msg, f"WS endpoint missing: {e}"


# ---------- Auth login page route (handled by auth_router) ----------
class TestAuthRoutes:
    def test_auth_me_unauth(self, session):
        r = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        # Should be 401 when no session
        assert r.status_code in (401, 404)  # depending on route name
