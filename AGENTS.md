# AGENTS.md

> Návod pre AI/agentov (Codex/MCP/CLI) ako efektívne pracovať s projektom **Digital Spiral** – mock Jira Cloud server s MCP integráciou a Python klientom.

---

## 1) Ciele a zásady

* **Primárny cieľ:** umožniť agentom spoľahlivo vyvíjať, testovať a používať mock Jira API, MCP nástroje a Python klienta.
* **Bezpečnosť a deterministickosť:** žiadne operácie mimo repozitára, rešpektuj rate‑limit a idempotenciu testov.
* **Zdroj pravdy:** kód v tomto repo + tento súbor. Pri rozpore uprednostni explicitné inštrukcie v PR/prome pred AGENTS.md.

---

## 2) Architektúra a adresáre

```
mockjira/          # FastAPI mock server (platform, agile, JSM, webhooks, admin)
  routers/         # API routery (platform.py, agile.py, service_management.py, webhooks.py, mock_admin.py)
  app.py           # application factory
  main.py          # CLI entrypoint (uvicorn)
  auth.py          # bearer auth + rate limiting
  utils.py         # ApiError, JQL parsing, pagination, helpers
  store.py         # InMemoryStore + dataclasses + seed data + webhooks

mcp_jira/          # MCP integration layer (server facade + tools registry)
  server.py        # get_tool, invoke_tool, list_tools
  tools.py         # t_jira_* and other MCP tool callables; TOOL_REGISTRY

📘 Detailné popisy komponentov nájdeš v:
- `mockjira/README.md`
- `mcp_jira/README.md`
- `clients/python/README.md`

clients/python/    # Python JiraAdapter (REST wrapper) + exceptions
  jira_adapter.py  # REST calls + retry + API groups (platform/agile/jsm)
  exceptions.py    # JiraError hierarchy

examples/          # orchestrator_demo.py – end‑to‑end demo workflow

tests/             # unit, integration, contract, e2e, smoke, mcp
scripts/           # OpenAPI fetch/bundle, parity report, contracts runner
```

---

## 3) Spúšťanie lokálne

### 3.1 Rýchly štart mock servera

```bash
python -m mockjira.main --host 0.0.0.0 --port 9000 --log-level info
# alebo (pri vývoji)
uvicorn mockjira.app:create_app --factory --host 0.0.0.0 --port 9000 --reload
```

### 3.2 Konfigurácia (env)

* `JIRA_BASE_URL` (default: `http://localhost:9000`)
* `JIRA_TOKEN` (default: `mock-token`)
* `JIRA_TIMEOUT` (default: `10`)
* `JIRA_USER_AGENT` (default: `MockJiraAdapter/1.0`)
* Webhook simulácia: `MOCKJIRA_WEBHOOK_JITTER_MIN`/`MAX`, `MOCKJIRA_WEBHOOK_POISON_PROB`

### 3.3 Python klient – rýchly test

```python
from clients.python.jira_adapter import JiraAdapter
adapter = JiraAdapter("http://localhost:9000", "mock-token")
issue = adapter.create_issue("SUP", "10003", "Demo from agent")
print(issue["key"])  # napr. SUP-101
```

---

## 4) MCP nástroje (tools)

### 4.1 Registry

```
jira.create_issue        jira.get_issue            jira.search
jira.list_transitions    jira.transition_issue     jira.add_comment
jsm.create_request       agile.list_sprints
```

### 4.2 Konvencie volania

* Všetky nástroje prijímajú `args: Dict[str, Any]` a vracajú JSON.
* **Povinné polia** (príklady):

  * `jira.create_issue`: `project_key`, `issue_type_id`, `summary`, [`description_adf`?], [`fields`?]
  * `jira.get_issue`: `key`
  * `jira.search`: `jql`, [`start_at`], [`max_results`]
  * `jira.list_transitions`/`jira.transition_issue`: `key` (+ `transition_id` pre transition)
  * `jira.add_comment`: `key`, `body_adf`
  * `jsm.create_request`: `service_desk_id`, `request_type_id`, `summary`, [`fields`?]
  * `agile.list_sprints`: `board_id`, [`start_at`], [`max_results`]

### 4.3 Facade pre agentov

Použi `mcp_jira.server.invoke_tool(name, args)` alebo `get_tool(name)(args)`. Na introspekciu `list_tools()` vráti názvy a `__doc__` popisy.

### 4.4 Pripojenie MCP ↔️ Jira

1. Skontroluj, že prostredie má nastavené premenné `JIRA_BASE_URL`, `JIRA_TOKEN` a voliteľne `JIRA_TIMEOUT`.
2. Uisti sa, že mock server (alebo produkčná Jira) beží a je dostupná na zvolenej URL.
3. Inicializuj MCP facade, napríklad:
   ```python
   from mcp_jira.server import list_tools, invoke_tool

   print(list_tools())
   issue = invoke_tool("jira.create_issue", {
       "project_key": "SUP",
       "issue_type_id": "10003",
       "summary": "Ticket from MCP agent"
   })
   print(issue["key"])
   ```
4. Pri potrebe OAuth pozri `mcp_jira/oauth.py`. Detailný onboarding je v `mcp_jira/README.md`.

#### 4.5 MCP Jira OAuth – .env autoload

`scripts/run_mcp_jira_oauth.py` automaticky načíta `.env` v koreňovom adresári repo a exportuje premenné do procesu bridge. Pre hands‑free štart stačí vytvoriť `.env`:

```
ATLASSIAN_CLIENT_ID="<client_id>"
ATLASSIAN_CLIENT_SECRET="<client_secret>"
ATLASSIAN_REDIRECT_URI="http://127.0.0.1:8055/oauth/callback"
```

Potom spustiť:

```
python scripts/run_mcp_jira_oauth.py --open --test
```

- Po autorizácii v prehliadači sa uloží token do `~/.config/mcp-jira/token.json`.
- Bridge začne počúvať na `http://127.0.0.1:8055` a nástroje sú dostupné cez `/tools` a `/tools/invoke`.

---

## 5) API povrch mock servera

* **Platform** (`/rest/api/3`): project, field, status, issue (CRUD subset), search (JQL), transitions, comments, myself
* **Agile** (`/rest/agile/1.0`): board, sprint, backlog
* **Service Management** (`/rest/servicedeskapi`): request + approvals
* **Webhooks** (`/rest/api/3/webhook` a inspekcia `/rest/api/3/_mock/webhooks/deliveries`)
* **Admin** (`/_mock/...`): info, seed export/load, reset

> Pozn.: Server je **stateful**; `store.py` spravuje entity, seed data a webhook doručovanie.

---

## 6) Dôležité dátové formáty a funkcie

* **ADF (Atlassian Document Format)**: pomocou `normalize_adf()` akceptujeme `str|dict|None`, vždy ukladaj ako `{type:"doc",version:1,...}`.
* **JQL podmnožina**: podpora `field = value`, `IN (...)`, dátum `>=`, `ORDER BY`, `AND`, `currentUser()`.
* **Paginácia**: `paginate(items, start_at, max_results)` vracia aj `isLast`, `total`.
* **Rate limiting**: cost‑based (GET=1, write=2, search=5), okno ~60s, limit ~100. Rešpektuj hlavičky `Retry-After`.

---

## 7) Vývojové príkazy

```bash
# Testy
pytest -q                          # všetky
pytest tests/unit -q               # unit
pytest tests/integration -q        # integration
pytest tests/contract -q           # contract (schemathesis)
pytest tests/e2e -q                # end-to-end

# Lint/typy
ruff check . || flake8 .           # vyber jeden podľa projektu
mypy clients/python mockjira       # type-checking

# OpenAPI utility
python scripts/fetch_openapi.py
python scripts/bundle_openapi.py

# Zmluvné testy – pipeline
python scripts/run_contracts.py
# (spustí fetch_openapi → pytest tests/contract → parity_report)
```

### 7.1 Paritný report (quality gate)

* `scripts/parity_report.py artifacts/parity.json`
* Failuje (<95 % úspešnosť) s exit kódom `1`.

---

## 8) Štýl kódu a príspevky

* **Python ≥ 3.11**, úplné type‑hinty, docstringy pre verejné API.
* Konzistentný názvoslovný štýl: `snake_case` pre Python.
* PR musí obsahovať: *čo/why/how tested*, zahrnúť testy, prejsť CI (testy + lint + typy).

---

## 9) Povolenia a obmedzenia

**Povolené**

* Úpravy a tvorba súborov v rámci repozitára.
* Spúšťanie testov, lintru, bundlingu OpenAPI a mock servera.

**Zakázané**

* Menenie git histórie, tvorba vetiev bez pokynov.
* Sieťové volania mimo mock/servera, ak nie sú súčasťou testu (OpenAPI fetch je výnimka v `scripts/`).
* Operácie mimo koreňa projektu.

---

## 10) Vzorové postupy pre agentov

### 10.1 Vytvorenie issue cez MCP

```python
from mcp_jira.server import invoke_tool
res = invoke_tool("jira.create_issue", {
  "project_key": "SUP",
  "issue_type_id": "10003",
  "summary": "Orchestrator demo",
  "description_adf": {"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Hello"}]}]}
})
```

### 10.2 Transition + komentár

```python
key = res["key"]
from mcp_jira.server import get_tool
list_trans = get_tool("jira.list_transitions")({"key": key})
get_tool("jira.transition_issue")({"key": key, "transition_id": list_trans["transitions"][0]["id"]})
get_tool("jira.add_comment")({"key": key, "body_adf": {"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Done."}]}]}})
```

---

## 11) E2E demo (examples/orchestrator_demo.py)

* Konfiguruje adaptér z ENV, voliteľne zaregistruje webhook, vytvorí SUP issue, urobí transition, pridá komentár, vyhľadá issue, vytvorí JSM request, vypíše sprinty, vráti sumár s časovaním.

---

## 12) Diagnostika a logy

* **Request log**: `app.state.request_log` (posledných ~500 záznamov).
* **Webhooky**: kontrola cez `/_mock/webhooks/deliveries`.
* **Admin**: `/_mock/info`, `/_mock/seed/export`, `/_mock/seed/load`, `/_mock/reset`.
* Chyby vracaj cez `ApiError` → Jira‑štýl payload + správne hlavičky.

---

## 13) Rozšírenia a TODO pre agentov

* Doplniť ďalšie JQL operátory podľa potreby.
* Viac testov pre edge prípady rate‑limitov a ADF validácie.
* CI job pre `scripts/run_contracts.py` s artefaktom `artifacts/parity.json`.

---

## 14) Priorita pokynov

1. Explicitné inštrukcie v aktuálnej úlohe/PR.
2. Tento AGENTS.md (najbližší v adresári je nadradený všeobecnému).
3. Implicitné defaulty nástrojov a knižníc.

---

## 15) Rýchla kontrolná karta (pre agentov)

* [ ] Server beží (9000) a má seed data
* [ ] Máš `JIRA_TOKEN` (`mock-token`) a `JIRA_BASE_URL`
* [ ] Testy + lint + typy prešli
* [ ] Webhooky doručujú (ak použité)
* [ ] Paritný report ≥ 95 %
