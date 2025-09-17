from __future__ import annotations

import json
from pathlib import Path

import requests
from openapi_core import OpenAPI
from openapi_core.configurations import Config
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.contrib.requests import RequestsOpenAPIResponse
from requests import Response


def load_openapi(path: str) -> OpenAPI:
    """Load an OpenAPI document without validating the upstream spec."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    servers = raw.get("servers") or []
    server_url = servers[0].get("url") if servers else ""
    api = OpenAPI.from_dict(
        raw, config=Config(spec_validator_cls=None, server_base_url=server_url)
    )
    api._server_url = server_url or "https://your-domain.atlassian.net"
    return api


def validate_response(api: OpenAPI, response: Response, path_template: str):
    """Validate the given requests response against the OpenAPI document."""

    server_url = getattr(api, "_server_url", "https://your-domain.atlassian.net")
    original = response.request
    prepared = requests.Request(
        method=original.method,
        url=f"{server_url}{original.path_url}",
        headers=dict(original.headers),
        data=original.body,
    ).prepare()
    openapi_request = RequestsOpenAPIRequest(prepared)
    openapi_request.full_url_pattern = f"{server_url}{path_template}"

    openapi_response = RequestsOpenAPIResponse(response)
    return list(api.response_validator.iter_errors(openapi_request, openapi_response))
