"""Thin client for the Home Assistant REST API.

Docs: https://developers.home-assistant.io/docs/api/rest/
"""

from __future__ import annotations

from typing import Any

import httpx

UNAVAILABLE_STATES = frozenset({"unavailable", "unknown"})


class HAError(RuntimeError):
    pass


class HAClient:
    def __init__(
        self,
        url: str,
        token: str,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not url or not token:
            raise HAError("HA_URL and HA_TOKEN must be set (see .env.example)")
        self._http = httpx.Client(
            base_url=url.rstrip("/") + "/api",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )

    def __enter__(self) -> HAClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._http.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._http.request(method, path, **kwargs)
        if resp.status_code == 401:
            raise HAError("Unauthorized: check HA_TOKEN")
        if resp.is_error:
            raise HAError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        return resp.json() if resp.content else None

    def ping(self) -> str:
        return self._request("GET", "/")["message"]

    def config(self) -> dict[str, Any]:
        return self._request("GET", "/config")

    def states(self, domain: str | None = None) -> list[dict[str, Any]]:
        states = self._request("GET", "/states")
        if domain:
            states = [s for s in states if s["entity_id"].split(".", 1)[0] == domain]
        return sorted(states, key=lambda s: s["entity_id"])

    def state(self, entity_id: str) -> dict[str, Any]:
        return self._request("GET", f"/states/{entity_id}")

    def unavailable(self) -> list[dict[str, Any]]:
        return [s for s in self.states() if s["state"] in UNAVAILABLE_STATES]

    def call_service(
        self, domain: str, service: str, data: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        return self._request("POST", f"/services/{domain}/{service}", json=data or {})

    def check_config(self) -> dict[str, Any]:
        """Validate the config currently on disk on the HA host.

        Returns {"result": "valid" | "invalid", "errors": str | None, ...}.
        """
        return self._request("POST", "/config/core/check_config")

    def reload_all(self) -> None:
        self.call_service("homeassistant", "reload_all")

    def restart(self) -> None:
        self.call_service("homeassistant", "restart")
