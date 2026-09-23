import json

import httpx
import pytest

from hactl.client import HAClient, HAError

STATES = [
    {"entity_id": "light.kitchen", "state": "on", "attributes": {}},
    {"entity_id": "sensor.temp", "state": "unavailable", "attributes": {}},
    {"entity_id": "light.den", "state": "unknown", "attributes": {}},
    {"entity_id": "switch.fan", "state": "off", "attributes": {}},
]


def make_client(handler) -> HAClient:
    return HAClient("http://ha.test:8123/", "tok", transport=httpx.MockTransport(handler))


def test_sends_bearer_token_and_api_prefix():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["path"] = request.url.path
        return httpx.Response(200, json={"message": "API running."})

    assert make_client(handler).ping() == "API running."
    assert seen == {"auth": "Bearer tok", "path": "/api/"}


def test_states_filters_by_domain_and_sorts():
    client = make_client(lambda r: httpx.Response(200, json=STATES))
    assert [s["entity_id"] for s in client.states("light")] == ["light.den", "light.kitchen"]


def test_unavailable():
    client = make_client(lambda r: httpx.Response(200, json=STATES))
    assert [s["entity_id"] for s in client.unavailable()] == ["light.den", "sensor.temp"]


def test_call_service_posts_json():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=[])

    make_client(handler).call_service("light", "turn_on", {"entity_id": "light.kitchen"})
    assert seen == {
        "method": "POST",
        "path": "/api/services/light/turn_on",
        "body": {"entity_id": "light.kitchen"},
    }


def test_unauthorized_raises_helpful_error():
    client = make_client(lambda r: httpx.Response(401, text="401: Unauthorized"))
    with pytest.raises(HAError, match="HA_TOKEN"):
        client.ping()


def test_requires_url_and_token():
    with pytest.raises(HAError):
        HAClient("", "")
