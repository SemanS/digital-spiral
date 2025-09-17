from __future__ import annotations

import pytest
import requests
import schemathesis as st
from hypothesis import HealthCheck, settings

SCHEMA = st.from_path("schemas/jsm.v3.json")
CONTRACT_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

ALLOWED_ENDPOINTS = {
    "GET /rest/servicedeskapi/request",
    "GET /rest/servicedeskapi/request/{issueIdOrKey}",
}


@CONTRACT_SETTINGS
@SCHEMA.parametrize()
@pytest.mark.filterwarnings("ignore::hypothesis.errors.NonInteractiveExampleWarning")
def test_jsm_contract(case, base_url, auth_header, parity_recorder):
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
    except AssertionError as exc:
        parity_recorder(
            api="jsm",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[str(exc)],
        )
        raise
    except Exception as exc:
        parity_recorder(
            api="jsm",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[str(exc)],
        )
        raise
    else:
        parity_recorder(
            api="jsm",
            method=case.method,
            path=path_template,
            status=getattr(response, "status_code", 0),
            detail=[],
        )
