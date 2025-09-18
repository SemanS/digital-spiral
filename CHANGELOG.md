# Changelog

## Unreleased

### Changed
- Webhook deliveries now sign payloads with `sha256(secret + body)` and expose
  deterministic `X-MockJira-Signature-Version` headers.
- Dual signature mode can be toggled via `WEBHOOK_SIGNATURE_COMPAT` to keep the
  legacy HMAC digest during migration.

### Added
- Delivery metadata now persists the canonical wire body (base64) and headers
  for replay verification.
- New `/_mock/webhooks/logs` endpoint exposing structured delivery attempts and
  a FastAPI admin info payload advertising the active signature version.
- Expanded test coverage for webhooks, JQL order/filter behaviour, custom
  fields, issue links and changelog history.
