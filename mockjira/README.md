# MockJira Service Overview

## Purpose
The `mockjira` package provides a FastAPI implementation of Jira Cloud endpoints that power the Digital Spiral workspace. It enables agents to practice the kind of natural-language-to-action workflows described in [Introducing Codex](https://openai.com/index/introducing-codex/), by giving them a deterministic API surface to automate against.

## Key Capabilities
- Implements core Jira REST resources (projects, issues, search, comments, transitions) with in-memory persistence.
- Emulates Jira Agile and Service Management endpoints so orchestration flows can test sprint and request scenarios.
- Supports webhook simulation and administrative reset/export helpers for reproducible demos.

## Usage Notes
1. Start the server locally:
   ```bash
   python -m mockjira.main --host 0.0.0.0 --port 9000
   ```
2. Configure clients with the provided base URL and token (`mock-token`).
3. Interact through REST calls or via the MCP tooling described in the repository documentation.

## Relation to Codex
OpenAI Codex translates natural language instructions into working code. This mock server mirrors the downstream systems Codex-powered agents interact with—allowing them to convert task descriptions into API calls in a safe environment.
