# KOMPLETNÝ SÚHRN CODEBASE - Mock Jira Cloud Server

## 📋 PREHĽAD PROJEKTU
**Mock Jira Cloud Server** je pokročilý stateful mock server implementujúci najdôležitejšie API povrchy Jira Cloud REST APIs. Projekt je určený pre integračné testovanie a lokálny vývoj, kde priame volanie Atlassian endpointov nie je praktické.

### 🎯 Hlavné funkcie:
- **Jira Platform REST API v3**: Issues, search, transitions, comments, projects, fields, users, webhooks
- **Jira Software (Agile) API**: Boards, sprints, backlog s pagination
- **Jira Service Management API**: Portal requests CRUD s approval workflow
- **ADF aware payloads**: Atlassian Document Format pre descriptions a comments
- **Webhooks**: Mock webhook listeners s inspection endpointom
- **Auth + Rate limiting**: Bearer token auth s rate limiting simuláciou

---

## 📁 DETAILNÁ ŠTRUKTÚRA SÚBOROV A FUNKCIÍ

### 🏠 ROOT ADRESÁR
```
/
├── README.md                    # Projektová dokumentácia (67 riadkov)
├── pyproject.toml              # Python projekt konfigurácia (30 riadkov)
├── requirements-contract.txt    # Contract test závislosti (6 riadkov)
├── artifacts/                  # Výstupné súbory (prázdny)
└── schemas/                    # OpenAPI schémy (3 súbory JSON)
```

### 📦 MOCKJIRA/ - HLAVNÝ APLIKAČNÝ BALÍK

#### 🔧 mockjira/__init__.py (4 riadky)
```python
# EXPORTOVANÉ FUNKCIE:
- create_app  # Import z app.py
```

#### 🚀 mockjira/app.py (41 riadkov)
```python
# FUNKCIE:
def create_app(store: InMemoryStore | None = None) -> FastAPI:
    """Vytvorí FastAPI aplikáciu s nakonfigurovanými routami
    - Nastaví dependency overrides pre auth
    - Pripojí všetky routery (platform, agile, service_management, webhooks)
    - Nastaví store do app.state
    """
```

#### 🔐 mockjira/auth.py (56 riadkov)
```python
# FUNKCIE:
async def get_current_user(authorization: str, x_force_429: str) -> str:
    """Placeholder pre auth dependency - nahradený počas app setup"""

def auth_dependency(store: InMemoryStore) -> Callable:
    """Vráti dependency funkciu pre:
    - Bearer token validáciu
    - Rate limiting kontrolu
    - X-Force-429 header simuláciu
    """
```

#### 🖥️ mockjira/main.py (48 riadkov)
```python
# FUNKCIE:
def build_parser() -> argparse.ArgumentParser:
    """Vytvorí CLI argument parser s options:
    --host, --port, --log-level, --no-seed"""

def run(argv: list[str] | None = None) -> None:
    """Hlavná entry point funkcia:
    - Parsuje argumenty
    - Vytvorí app s/bez seed data
    - Spustí Uvicorn server
    """
```

#### 💾 mockjira/store.py (855 riadkov) - NAJVÄČŠÍ SÚBOR
```python
# VÝNIMKY:
class RateLimitError(Exception):
    """Rate limit exceeded exception s retry_after"""

# DATACLASSES (všetky s to_api() metódou):
@dataclass class User:
    """Používateľ: account_id, display_name, email, time_zone"""

@dataclass class Project:
    """Projekt: id, key, name, project_type, lead_account_id"""

@dataclass class IssueType:
    """Typ issue: id, name, subtask"""

@dataclass class StatusCategory:
    """Kategória statusu: id, key, name"""

@dataclass class Status:
    """Status: id, name, status_category"""

@dataclass class Transition:
    """Prechod: id, name, to_status"""

@dataclass class Comment:
    """Komentár: id, author_id, body, created"""

@dataclass class Sprint:
    """Sprint: id, board_id, name, state, start_date, end_date, goal"""

@dataclass class Board:
    """Board: id, name, type, project_key"""

@dataclass class ServiceRequest:
    """Service request: id, issue_key, request_type_id, approvals"""

@dataclass class Issue:
    """Issue: id, key, project_key, issue_type_id, summary, description,
    status_id, reporter_id, assignee_id, labels, created, updated,
    sprint_id, comments"""

@dataclass class WebhookRegistration:
    """Webhook: id, url, events, jql"""

# HLAVNÁ TRIEDA:
class InMemoryStore:
    """Centrálny state container pre mock server"""

    # FACTORY METÓDY:
    @classmethod
    def with_seed_data(cls) -> "InMemoryStore":
        """Vytvorí store s predvyplnenými dátami"""

    def _seed(self) -> None:
        """Naplní store základnými dátami:
        - 3 používatelia (Alice, Bob, Carol)
        - 2 projekty (DEV, SUP)
        - 4 issue typy (Bug, Task, Story, Service Request)
        - 3 statusy (To Do, In Progress, Done)
        - 2 boards (Scrum, Kanban)
        - 3 sprinty (closed, active, future)
        - 4 sample issues
        """

    # UTILITY METÓDY:
    def _create_issue(...) -> Issue:
        """Vytvorí nové issue s auto-generovaným kľúčom"""

    def _adf(self, text: str) -> dict:
        """Vytvorí Atlassian Document Format z textu"""

    # AUTH & RATE LIMITING:
    def is_valid_token(self, token: str) -> bool:
        """Validácia API tokenu"""

    def register_call(self, token: str) -> None:
        """Rate limiting - 100 calls/60s window"""

    # PLATFORM API METÓDY:
    def list_projects(self) -> list[dict]:
        """Zoznam všetkých projektov"""

    def list_issue_types(self) -> list[dict]:
        """Zoznam všetkých typov issues"""

    def list_statuses(self) -> list[dict]:
        """Zoznam všetkých statusov"""

    def list_users(self, query: str = None) -> list[dict]:
        """Vyhľadávanie používateľov podľa mena/emailu"""

    def fields_payload(self) -> list[dict]:
        """Definície polí (summary, description, labels)"""

    def get_issue(self, key: str) -> Issue | None:
        """Získanie issue podľa kľúča"""

    def create_issue(self, payload: dict, reporter_id: str) -> Issue:
        """Vytvorenie nového issue s webhook dispatch"""

    def update_issue(self, key: str, payload: dict) -> Issue:
        """Aktualizácia issue s webhook dispatch"""

    def search_issues(self, filters: dict) -> list[Issue]:
        """Vyhľadávanie issues podľa filtrov (project, status, assignee)"""

    def get_transitions(self, issue: Issue) -> list[Transition]:
        """Dostupné prechody pre issue"""

    def apply_transition(self, issue: Issue, transition_id: str) -> Issue:
        """Aplikovanie prechodu s webhook dispatch"""

    def add_comment(self, issue: Issue, author_id: str, body: Any) -> Comment:
        """Pridanie komentára s webhook dispatch"""

    # AGILE API METÓDY:
    def list_boards(self) -> list[dict]:
        """Zoznam všetkých boards"""

    def list_sprints(self, board_id: int) -> list[dict]:
        """Zoznam sprintov pre board"""

    def create_sprint(self, payload: dict) -> Sprint:
        """Vytvorenie nového sprintu"""

    def backlog_issues(self, board_id: int) -> list[Issue]:
        """Issues v backlogu (bez sprintu)"""

    # SERVICE MANAGEMENT API METÓDY:
    def list_service_requests(self) -> list[dict]:
        """Zoznam všetkých service requests"""

    def create_service_request(self, payload: dict, reporter_id: str) -> ServiceRequest:
        """Vytvorenie service request s webhook dispatch"""

    def update_service_request(self, request_id: str, approval_id: str, approve: bool) -> ServiceRequest:
        """Aktualizácia approval s webhook dispatch"""

    # WEBHOOK API METÓDY:
    def register_webhook(self, payload: dict) -> list[dict]:
        """Registrácia webhook listeners"""

    def list_webhooks(self) -> list[dict]:
        """Zoznam registrovaných webhooks"""

    def delete_webhook(self, webhook_id: str) -> None:
        """Zmazanie webhook"""

    def dispatch_event(self, event_type: str, payload: dict) -> None:
        """Odoslanie webhook eventu všetkým listenerom"""

    def _send_webhook(self, url: str, delivery: dict) -> None:
        """HTTP POST webhook delivery (fail silently)"""

    # UTILITY METÓDY:
    def normalize_adf(self, value: Any) -> dict:
        """Normalizácia ADF payloadu"""

    def _ensure_service_request(self, issue: Issue) -> ServiceRequest:
        """Vytvorenie service request pre SUP issue"""

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parsovanie datetime hodnôt"""
```

#### 🛠️ mockjira/utils.py (72 riadkov)
```python
# FUNKCIE:
def parse_jql(jql: str | None) -> dict[str, Any]:
    """Parsuje podmnožinu JQL do dictionary filtrov
    - Podporuje IN a = operátory
    - Ignoruje ORDER BY klauzuly
    - Normalizuje quoted hodnoty
    """

def _normalise_value(raw: str) -> str:
    """Odstráni quotes z hodnôt"""

def paginate(items: Iterable[Any], start_at: int, max_results: int) -> dict:
    """Implementuje pagination logiku s metadátami:
    - startAt, maxResults, total, isLast, values
    """
```

### 🌐 MOCKJIRA/ROUTERS/ - API ROUTERY

#### 📋 mockjira/routers/__init__.py (11 riadkov)
```python
# EXPORTY:
__all__ = ["agile", "platform", "service_management", "webhooks"]
```

#### 🏃 mockjira/routers/agile.py (87 riadkov) - JIRA SOFTWARE API
```python
# HELPER FUNKCIE:
def get_store(request: Request) -> InMemoryStore:
    """Získa store z app.state"""

# API ENDPOINTS:
@router.get("/board")
async def list_boards(...) -> dict:
    """GET /rest/agile/1.0/board - Zoznam boards s pagination"""

@router.get("/board/{board_id}/sprint")
async def list_sprints(...) -> dict:
    """GET /rest/agile/1.0/board/{board_id}/sprint - Sprinty pre board"""

@router.post("/sprint")
async def create_sprint(...) -> dict:
    """POST /rest/agile/1.0/sprint - Vytvorenie sprintu"""

@router.get("/board/{board_id}/backlog")
async def backlog(...) -> dict:
    """GET /rest/agile/1.0/board/{board_id}/backlog - Backlog issues"""
```

#### 🏢 mockjira/routers/platform.py (203 riadkov) - JIRA PLATFORM API
```python
# HELPER FUNKCIE:
def get_store(request: Request) -> InMemoryStore:
    """Získa store z app.state"""

# API ENDPOINTS:
@router.get("/project")
async def list_projects(...) -> dict:
    """GET /rest/api/3/project - Zoznam projektov"""

@router.get("/field")
async def list_fields(...) -> dict:
    """GET /rest/api/3/field - Definície polí"""

@router.get("/status")
async def list_statuses(...) -> dict:
    """GET /rest/api/3/status - Zoznam statusov"""

@router.get("/issue/{issue_id_or_key}")
async def get_issue(...) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey} - Získanie issue"""

@router.post("/issue")
async def create_issue(...) -> dict:
    """POST /rest/api/3/issue - Vytvorenie issue"""

@router.put("/issue/{issue_id_or_key}")
async def update_issue(...) -> dict:
    """PUT /rest/api/3/issue/{issueIdOrKey} - Aktualizácia issue"""

@router.get("/search")
async def search_issues(...) -> dict:
    """GET /rest/api/3/search - JQL search s currentuser() support"""

@router.get("/issue/{issue_id_or_key}/transitions")
async def list_transitions(...) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey}/transitions - Dostupné prechody"""

@router.post("/issue/{issue_id_or_key}/transitions")
async def apply_transition(...) -> dict:
    """POST /rest/api/3/issue/{issueIdOrKey}/transitions - Aplikovanie prechodu"""

@router.get("/issue/{issue_id_or_key}/comment")
async def list_comments(...) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey}/comment - Zoznam komentárov"""

@router.post("/issue/{issue_id_or_key}/comment")
async def create_comment(...) -> dict:
    """POST /rest/api/3/issue/{issueIdOrKey}/comment - Vytvorenie komentára"""

@router.get("/myself")
async def get_myself(...) -> dict:
    """GET /rest/api/3/myself - Info o aktuálnom používateľovi"""
```

#### 🎫 mockjira/routers/service_management.py (78 riadkov) - JSM API
```python
# HELPER FUNKCIE:
def get_store(request: Request) -> InMemoryStore:
    """Získa store z app.state"""

# API ENDPOINTS:
@router.get("/request")
async def list_requests(...) -> dict:
    """GET /rest/servicedeskapi/request - Zoznam service requests"""

@router.post("/request")
async def create_request(...) -> dict:
    """POST /rest/servicedeskapi/request - Vytvorenie service request"""

@router.get("/request/{request_id}")
async def get_request(...) -> dict:
    """GET /rest/servicedeskapi/request/{issueIdOrKey} - Získanie request"""

@router.post("/request/{request_id}/approval/{approval_id}")
async def update_approval(...) -> dict:
    """POST /rest/servicedeskapi/request/{requestId}/approval/{approvalId} - Approval workflow"""
```

#### 🪝 mockjira/routers/webhooks.py (56 riadkov) - WEBHOOK API
```python
# HELPER FUNKCIE:
def get_store(request: Request) -> InMemoryStore:
    """Získa store z app.state"""

# API ENDPOINTS:
@router.post("/webhook")
async def register_webhook(...) -> dict:
    """POST /rest/api/3/webhook - Registrácia webhook"""

@router.get("/webhook")
async def list_webhook(...) -> dict:
    """GET /rest/api/3/webhook - Zoznam webhooks"""

@router.delete("/webhook/{webhook_id}")
async def delete_webhook(...) -> dict:
    """DELETE /rest/api/3/webhook/{webhookId} - Zmazanie webhook"""

@router.get("/_mock/webhooks/deliveries")
async def list_deliveries(...) -> dict:
    """GET /rest/api/3/_mock/webhooks/deliveries - Inspection endpoint pre deliveries"""
```

---

## 🧪 TESTS/ - TESTOVACIA SADA

### 📋 tests/test_mockjira.py (171 riadkov) - HLAVNÉ TESTY
```python
# FIXTURES:
@pytest.fixture
def app():
    """FastAPI aplikácia s seed dátami"""

@pytest_asyncio.fixture
async def client(app):
    """Async HTTP klient pre testovanie"""

# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_projects_and_fields(client):
    """Test základných endpointov - projekty a polia"""

@pytest.mark.asyncio
async def test_issue_lifecycle_and_webhook_delivery(client):
    """Komplexný test:
    - Vytvorenie issue
    - Získanie issue
    - JQL search
    - Transitions
    - Comments
    - Webhook deliveries
    """

@pytest.mark.asyncio
async def test_agile_endpoints(client):
    """Test agile API - boards, backlog, sprints"""

@pytest.mark.asyncio
async def test_service_management_flow(client):
    """Test JSM workflow - create request, approval"""

@pytest.mark.asyncio
async def test_webhook_registration(client):
    """Test webhook registrácie"""

@pytest.mark.asyncio
async def test_rate_limit_simulation(client):
    """Test X-Force-429 header simulácie"""
```

### 🔍 TESTS/CONTRACT/ - CONTRACT TESTY

#### ⚙️ tests/contract/conftest.py (84 riadkov)
```python
# TRIEDY:
class ParityRecorder:
    """Zaznamenáva výsledky contract testov
    - records: List[Dict] s api, method, path, status, detail
    """

    def record(self, *, api: str, method: str, path: str, status: int, detail: List[str] = None):
        """Zaznamená test výsledok"""

# PYTEST HOOKS:
def pytest_configure(config: pytest.Config):
    """Nastaví ParityRecorder do config"""

def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    """Generuje parity.json a parity.md reporty do artifacts/"""

# FIXTURES:
@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL z MOCK_JIRA_BASE_URL env var"""

@pytest.fixture(scope="session")
def auth_header() -> Dict[str, str]:
    """Authorization header s mock-token"""

@pytest.fixture
def parity_recorder(request: pytest.FixtureRequest) -> Callable:
    """Recorder funkcia pre test výsledky"""
```

#### 🔧 tests/contract/openapi_validator.py (43 riadkov)
```python
# FUNKCIE:
def load_openapi(path: str) -> OpenAPI:
    """Načíta OpenAPI dokument bez spec validácie
    - Nastaví server_base_url z servers[0].url
    - Používa Config(spec_validator_cls=None)
    """

def validate_response(api: OpenAPI, response: Response, path_template: str):
    """Validuje HTTP response proti OpenAPI schéme
    - Vytvorí RequestsOpenAPIRequest/Response objekty
    - Vráti list validation errors
    """
```

#### 🌊 tests/contract/test_flows_contract.py (165 riadkov)
```python
# HELPER FUNKCIE:
def _json(response: requests.Response):
    """Bezpečné JSON parsing s fallback na {}"""

def _record(parity_recorder, api: str, path: str, response, errors):
    """Zaznamená test výsledok do parity recorderu"""

# TEST FUNKCIE:
def test_issue_crud_workflow(base_url, auth_header, parity_recorder):
    """End-to-end test issue CRUD workflow:
    1. POST /rest/api/3/issue - vytvorenie
    2. GET /rest/api/3/issue/{key} - získanie
    3. GET /rest/api/3/issue/{key}/transitions - zoznam prechodov
    4. POST /rest/api/3/issue/{key}/transitions - aplikovanie prechodu
    5. POST /rest/api/3/search - JQL search
    Každý krok validuje response proti OpenAPI schéme
    """

def test_jsm_request_flow(base_url, auth_header, parity_recorder):
    """JSM workflow test:
    1. POST /rest/servicedeskapi/request - vytvorenie
    2. GET /rest/servicedeskapi/request/{id} - získanie
    Validácia proti JSM OpenAPI schéme
    """

def test_agile_board_flow(base_url, auth_header, parity_recorder):
    """Agile workflow test:
    1. GET /rest/agile/1.0/board - zoznam boards
    2. GET /rest/agile/1.0/board/{id}/sprint - sprinty
    Validácia proti Software OpenAPI schéme
    """
```

#### 🎫 tests/contract/test_jsm_contract.py (65 riadkov)
```python
# SCHEMATHESIS SETUP:
SCHEMA = st.from_path("schemas/jsm.v3.json")
CONTRACT_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

ALLOWED_ENDPOINTS = {
    "GET /rest/servicedeskapi/request",
    "GET /rest/servicedeskapi/request/{issueIdOrKey}",
}

# TEST FUNKCIE:
@CONTRACT_SETTINGS
@SCHEMA.parametrize()
def test_jsm_contract(case, base_url, auth_header, parity_recorder):
    """Schemathesis property-based test pre JSM API
    - Testuje iba GET/HEAD metódy
    - Filtruje iba implementované endpointy
    - Validuje response proti OpenAPI schéme
    - Zaznamenáva výsledky do parity recorderu
    """
```

#### 🏢 tests/contract/test_platform_contract.py (71 riadkov)
```python
# SCHEMATHESIS SETUP:
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

# TEST FUNKCIE:
@CONTRACT_SETTINGS
@SCHEMA.parametrize()
def test_platform_contract(case, base_url, auth_header, parity_recorder):
    """Schemathesis property-based test pre Platform API
    - Testuje iba GET/HEAD metódy
    - Filtruje iba implementované endpointy
    - Validuje response proti OpenAPI schéme
    - Zaznamenáva výsledky do parity recorderu
    """
```

#### 🏃 tests/contract/test_software_contract.py (66 riadkov)
```python
# SCHEMATHESIS SETUP:
SCHEMA = st.from_path("schemas/jira-software.v3.json")
CONTRACT_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

ALLOWED_ENDPOINTS = {
    "GET /rest/agile/1.0/board",
    "GET /rest/agile/1.0/board/{boardId}/sprint",
    "GET /rest/agile/1.0/board/{boardId}/backlog",
}

# TEST FUNKCIE:
@CONTRACT_SETTINGS
@SCHEMA.parametrize()
def test_software_contract(case, base_url, auth_header, parity_recorder):
    """Schemathesis property-based test pre Software API
    - Testuje iba GET/HEAD metódy
    - Filtruje iba implementované endpointy
    - Validuje response proti OpenAPI schéme
    - Zaznamenáva výsledky do parity recorderu
    """
```

---

## 🔧 SCRIPTS/ - UTILITY SKRIPTY

#### 📦 scripts/bundle_openapi.py (26 riadkov)
```python
# FUNKCIE:
def bundle(src: str | pathlib.Path, dst: str | pathlib.Path):
    """Bundluje OpenAPI schému pomocou prance ResolvingParser
    - Resolves všetky $ref odkazy
    - Uloží do JSON súboru
    """

def main():
    """Bundluje všetky 3 OpenAPI schémy:
    - jira-platform.v3.json → jira-platform.v3.json.bundled.json
    - jira-software.v3.json → jira-software.v3.json.bundled.json
    - jsm.v3.json → jsm.v3.json.bundled.json
    """
```

#### 🌐 scripts/fetch_openapi.py (25 riadkov)
```python
# KONŠTANTY:
SPECS = {
    "jira-platform.v3.json": "https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8171.0",
    "jira-software.v3.json": "https://dac-static.atlassian.com/cloud/jira/software/swagger.v3.json?_v=1.8171.0",
    "jsm.v3.json": "https://dac-static.atlassian.com/cloud/jira/service-desk/swagger.v3.json?_v=1.8171.0",
}

# FUNKCIE:
def main():
    """Stiahne OpenAPI schémy z Atlassian CDN
    - Vytvorí schemas/ adresár
    - Stiahne všetky 3 schémy s timeout 60s
    - Vypíše veľkosť každej schémy
    """
```

#### 📊 scripts/parity_report.py (26 riadkov)
```python
# FUNKCIE:
def main(json_path: str):
    """Analyzuje parity.json report
    - Spočíta total/ok/bad responses
    - Vypočíta success ratio
    - Exit code 1 ak < 95% threshold
    - Používa sa v CI/CD pipeline
    """
```

#### 🚀 scripts/run_contracts.py (20 riadkov)
```python
# FUNKCIE:
def run(cmd: list[str]):
    """Spustí shell príkaz s check=True"""

def main():
    """Orchestruje contract testing pipeline:
    1. python scripts/fetch_openapi.py - stiahne schémy
    2. pytest tests/contract - spustí contract testy
    3. python scripts/parity_report.py artifacts/parity.json - analyzuje výsledky
    """
```

---

## 📄 SCHEMAS/ - OPENAPI SCHÉMY
```
schemas/
├── jira-platform.v3.json     # Jira Platform REST API v3 schéma
├── jira-software.v3.json     # Jira Software (Agile) API schéma
└── jsm.v3.json              # Jira Service Management API schéma
```

## 📁 ARTIFACTS/ - VÝSTUPNÉ SÚBORY
```
artifacts/                    # Prázdny adresár pre generované súbory
├── parity.json              # (generovaný) Contract test výsledky
└── parity.md                # (generovaný) Human-readable parity report
```

---

## 📈 ŠTATISTIKY PROJEKTU

### 📊 SÚBORY A RIADKY:
- **Celkový počet súborov**: 25
- **Najväčší súbor**: mockjira/store.py (855 riadkov)
- **Celkový počet riadkov kódu**: ~1,500+
- **Python súbory**: 22
- **Konfiguračné súbory**: 3

### 🔧 FUNKCIE A TRIEDY:
- **Celkový počet funkcií**: ~85+
- **Dataclasses**: 12 (User, Project, Issue, atď.)
- **API endpointy**: 20+
- **Test funkcie**: 15+

### 🏗️ ARCHITEKTÚRA:
- **FastAPI routery**: 4 (platform, agile, service_management, webhooks)
- **Centrálny store**: InMemoryStore s 25+ metódami
- **Auth systém**: Bearer token + rate limiting
- **Webhook systém**: Registration + delivery tracking

### 🧪 TESTOVANIE:
- **Unit testy**: 6 test funkcií
- **Contract testy**: 6 schemathesis testov
- **Integration testy**: 3 workflow testy
- **Test coverage**: Platform, Agile, JSM APIs

### 📦 ZÁVISLOSTI:
- **Runtime**: FastAPI, Uvicorn, Pydantic, httpx
- **Testing**: pytest, pytest-asyncio, anyio
- **Contract testing**: schemathesis, openapi-core, prance
- **Python verzia**: >=3.11

### 🎯 API POKRYTIE:
- **Jira Platform API**: 10 endpointov (issues, search, comments, projects, atď.)
- **Jira Software API**: 4 endpointy (boards, sprints, backlog)
- **JSM API**: 3 endpointy (requests, approvals)
- **Webhook API**: 4 endpointy (register, list, delete, deliveries)

---

## 🚀 POUŽITIE A DEPLOYMENT

### 💻 Lokálny vývoj:
```bash
pip install -e .[test]
mock-jira-server --port 9000
```

### 🧪 Testovanie:
```bash
pytest                           # Unit testy
python scripts/run_contracts.py  # Contract testy
```

### 🔧 Rozšírenie:
- Pridanie nových API endpointov do routerov
- Rozšírenie InMemoryStore o nové entity
- Pridanie nových seed dát
- Integrácia s reálnymi OpenAPI schémami

---

## 🎯 ZÁVER

Tento projekt predstavuje **komplexný mock server pre Jira Cloud APIs** s pokročilými funkciami:

✅ **Stateful implementácia** - Všetky zmeny sa zachovávajú v pamäti
✅ **Realistické dáta** - Predvyplnené projekty, používatelia, issues
✅ **Webhook systém** - Plne funkčný s delivery tracking
✅ **Contract testing** - Validácia proti oficiálnym OpenAPI schémam
✅ **Rate limiting** - Simulácia reálnych API limitov
✅ **ADF support** - Atlassian Document Format pre rich text
✅ **Rozsiahle testovanie** - Unit, integration a property-based testy

Projekt je ideálny pre **integračné testovanie**, **lokálny vývoj** a **CI/CD pipelines** kde je potrebné simulovať Jira Cloud API bez pripojenia k reálnej inštancii.
