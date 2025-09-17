from __future__ import annotations

import pytest
import requests
pytest.importorskip("schemathesis")
import schemathesis as st
from hypothesis import HealthCheck, settings

SCHEMA = st.from_path("schemas/jira-platform.v3.json")
CONTRACT_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

ALLOWED_ENDPOINTS = {
    "GET /rest/api/3/project",
    "GET /rest/api/3/field",
    "GET /rest/api/3/status",
    "GET /rest/api/3/issue/{issueIdOrKey}",
    "GET /rest/api/3/issue/{issueIdOrKey}/transitions",
    "GET /rest/api/3/issue/{issueIdOrKey}/comment",
    "GET /rest/api/3/search",
    "GET /rest/api/3/myself",
}


@CONTRACT_SETTINGS
@SCHEMA.parametrize()
@pytest.mark.filterwarnings("ignore::hypothesis.errors.NonInteractiveExampleWarning")
def test_platform_contract(case, base_url, auth_header, parity_recorder):
    if case.method not in ("GET", "HEAD"):
        pytest.skip("Read-only sweep here")

    operation_id = f"{case.method} {getattr(case.operation, 'path', case.path)}"
    if operation_id not in ALLOWED_ENDPOINTS:
        pytest.skip("Endpoint not implemented in mock")

    with requests.Session() as session:
        response = case.call(
            session=session,
            base_url=base_url,
            headers=auth_header,
        )

    path_template = getattr(case.operation, "path", case.path)

    try:
        case.validate_response(response)
    except AssertionError as exc:  # pragma: no cover - schemathesis raises AssertionError
        parity_recorder(
            api="platform",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[str(exc)],
        )
        raise
    except Exception as exc:  # pragma: no cover - defensive catch
        parity_recorder(
            api="platform",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[str(exc)],
        )
        raise
    else:
        parity_recorder(
            api="platform",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[],
        )
