"""End-to-end test for the OAuth redirect attack reported by security researcher.

Attack scenario:
  1. Attacker registers a malicious OAuth client with redirect_uri=https://attacker.com/steal
  2. Attacker crafts an authorization URL and tricks victim into visiting it
  3. Victim approves on the legitimate-looking consent page
  4. Server redirects auth code to attacker's domain
  5. Attacker exchanges code for access token cross-origin (enabled by CORS credentials:true)
  6. Attacker has full read/write access to victim's Plane workspace

This test replays the attack against the real server app and verifies each
security fix blocks the corresponding step.

Since fastmcp 3.4 the defense has two layers:
  1. Dynamic Client Registration (/register) rejects redirect URIs outside
     the allowlist outright with 400 invalid_redirect_uri.
  2. /authorize independently validates redirect_uri against the allowlist,
     so a legitimately registered client cannot swap in a malicious URI.
"""

import pytest
from fastmcp import FastMCP
from key_value.aio.stores.memory import MemoryStore
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.testclient import TestClient

from plane_mcp.auth import PlaneOAuthProvider
from plane_mcp.server import DEFAULT_ALLOWED_REDIRECT_URIS as ALLOWED_REDIRECT_URI_PATTERNS


@pytest.fixture(scope="module")
def app():
    """Build the real server app (same wiring as __main__.py) with dummy credentials."""
    oauth_mcp = FastMCP(
        "Plane MCP Server",
        auth=PlaneOAuthProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8211",
            plane_base_url="http://localhost:9999",
            plane_internal_base_url="http://localhost:9999",
            client_storage=MemoryStore(),
            required_scopes=["read", "write"],
            allowed_client_redirect_uris=ALLOWED_REDIRECT_URI_PATTERNS,
            require_authorization_consent=False,
        ),
    )

    oauth_app = oauth_mcp.http_app()

    starlette_app = Starlette(
        routes=[Mount("/", app=oauth_app)],
    )

    # Same CORS config as __main__.py
    starlette_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return starlette_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app, follow_redirects=False)


class TestOAuthRedirectAttack:
    """Replay the full attack chain and verify each fix blocks it.

    The server uses an OAuth proxy architecture: /authorize redirects to
    upstream Plane OAuth (not directly to the client's redirect_uri). After
    Plane approves, the server's /auth/callback handles the response and
    only then redirects to the MCP client's redirect_uri.

    The allowed_client_redirect_uris patterns restrict which client URIs
    the proxy will redirect to after the upstream callback completes.
    """

    def _register_client(self, client: TestClient, redirect_uri: str) -> dict:
        """Register an OAuth client with the given redirect_uri."""
        response = client.post(
            "/register",
            json={
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
            },
        )
        assert response.status_code == 201, f"Registration failed: {response.text}"
        data = response.json()
        assert "client_id" in data
        return data

    def _assert_registration_rejected(self, client: TestClient, redirect_uri: str) -> None:
        """Since fastmcp 3.4, DCR rejects non-allowlisted redirect URIs outright."""
        response = client.post(
            "/register",
            json={
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
            },
        )
        assert response.status_code == 400, (
            f"VULNERABILITY: Malicious redirect URI was accepted for registration: {response.text}"
        )
        assert response.json().get("error") == "invalid_redirect_uri"

    def _authorize(self, client: TestClient, client_id: str, redirect_uri: str):
        return client.get(
            "/authorize",
            params={
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )

    def test_full_attack_is_blocked(self, client: TestClient) -> None:
        """Replay the exact attack: register with attacker URI, hit /authorize.

        Layer 1: registration of the attacker URI is rejected outright.
        Layer 2: even a legitimately registered client cannot swap in the
        attacker's URI at /authorize — and the attacker's domain must never
        appear anywhere in any redirect chain.
        """
        attacker_uri = "https://attacker.com/steal"

        # Step 1: Attacker registers malicious client — rejected
        self._assert_registration_rejected(client, attacker_uri)

        # Step 2: Attacker registers a legitimate-looking client, then swaps
        # in the attacker URI at the authorization step — also blocked
        reg = self._register_client(client, "http://localhost:3000/callback")
        response = self._authorize(client, reg["client_id"], attacker_uri)

        assert response.status_code == 400, (
            f"VULNERABILITY: Swapped redirect URI was not blocked: {response.status_code}"
        )
        location = response.headers.get("location", "")
        assert "attacker.com" not in location, (
            f"VULNERABILITY: Attacker domain found in redirect! Location: {location}"
        )

    @pytest.mark.parametrize(
        "malicious_uri",
        [
            "https://attacker.com/steal",
            "http://evil.com/callback",
            "javascript:alert(document.cookie)",
            "data:text/html,<script>fetch('https://evil.com')</script>",
            "myapp://callback",
        ],
        ids=[
            "attacker-domain",
            "evil-domain",
            "javascript-injection",
            "data-uri-injection",
            "unknown-protocol",
        ],
    )
    def test_malicious_uris_never_appear_in_redirects(
        self, client: TestClient, malicious_uri: str
    ) -> None:
        """Verify various attack vectors are rejected at registration and
        never leak into redirect locations even when passed to /authorize."""
        self._assert_registration_rejected(client, malicious_uri)

        # No client_id was ever issued for this URI; /authorize must not leak
        # it either regardless of which client the attacker names.
        response = self._authorize(client, "any-client-id", malicious_uri)

        location = response.headers.get("location", "")
        if response.is_redirect:
            assert malicious_uri not in location, (
                f"VULNERABILITY: Malicious URI leaked into redirect: {location}"
            )

    def test_legitimate_redirect_uri_passes(self, client: TestClient) -> None:
        """Sanity check: legitimate localhost URI is accepted and the flow proceeds."""
        legitimate_uri = "http://localhost:3000/callback"

        reg = self._register_client(client, legitimate_uri)

        response = client.get(
            "/authorize",
            params={
                "client_id": reg["client_id"],
                "redirect_uri": legitimate_uri,
                "response_type": "code",
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )

        # Should proceed with the OAuth flow (302 to upstream), not error
        assert response.status_code != 400, (
            f"Legitimate redirect URI was rejected: {response.text}"
        )

    def test_cors_blocks_cross_origin_token_theft(self, client: TestClient) -> None:
        """Step 5: Even if attacker got a code, CORS blocks cross-origin token exchange.

        With allow_credentials=False, browsers will not attach cookies or allow
        attacker JS to read the response from a cross-origin POST to /token.
        The combination of Access-Control-Allow-Origin: * with credentials:true
        was the original vulnerability — now credentials is false.
        """
        response = client.options(
            "/token",
            headers={
                "Origin": "https://attacker.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        # Credentials must NOT be allowed
        assert response.headers.get("access-control-allow-credentials") != "true", (
            "VULNERABILITY: CORS allows credentials — attacker JS can steal tokens cross-origin"
        )

        # Wildcard origin is fine without credentials
        # (browsers enforce that * + credentials:true is invalid, so this combo is safe)
        assert response.headers.get("access-control-allow-origin") == "*"
