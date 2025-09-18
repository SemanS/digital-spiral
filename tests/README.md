# Test Guide

- Webhook tests patch `httpx.AsyncClient` and rely on deterministic jitter.
  Adjust jitter/poison probabilities via `POST /rest/api/3/_mock/webhooks/settings`.
- Signature helpers live under `tests/utils/webhook_sig.py` and implement the
  `sha256(secret + body)` verifier used by new test cases.
- Set `WEBHOOK_SIGNATURE_COMPAT=1` before starting the app to surface the
  optional `X-MockJira-Legacy-Signature` header when validating older clients.
