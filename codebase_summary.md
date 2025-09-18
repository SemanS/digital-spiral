# KOMPLETNÝ SÚHRN CODEBASE - Digital Spiral (Mock Jira Cloud Server + MCP Integration)

## 📋 PREHĽAD PROJEKTU
**Digital Spiral** je komplexný projekt kombinujúci **Mock Jira Cloud Server** s **MCP (Model Context Protocol) integráciou**. Projekt poskytuje stateful mock server implementujúci najdôležitejšie API povrchy Jira Cloud REST APIs spolu s MCP tools pre seamless integráciu s AI asistentmi.

### 🎯 Hlavné komponenty:
1. **Mock Jira Server** - Stateful mock implementácia Jira Cloud APIs
2. **MCP Jira Tools** - MCP-kompatibilné nástroje pre Jira operácie
3. **Python Client Adapter** - Thin wrapper okolo Jira REST endpoints
4. **Orchestrator Examples** - Ukážkové workflow implementácie
5. **Comprehensive Testing** - Unit, integration, contract a e2e testy

### 🎯 Hlavné funkcie:
- **Jira Platform REST API v3**: Issues, search, transitions, comments, projects, fields, users, webhooks
- **Jira Software (Agile) API**: Boards, sprints, backlog s pagination
- **Jira Service Management API**: Portal requests CRUD s approval workflow
- **MCP Tool Registry**: 8 predefinovaných MCP tools pre Jira operácie
- **ADF aware payloads**: Atlassian Document Format pre descriptions a comments
- **Webhooks**: Mock webhook listeners s inspection endpointom
- **Auth + Rate limiting**: Bearer token auth s rate limiting simuláciou
- **Client Adapters**: Python wrapper s retry logikou a error handling

---

## 📁 DETAILNÁ ŠTRUKTÚRA SÚBOROV A FUNKCIÍ

### 🏠 ROOT ADRESÁR
```
/
├── README.md                    # Projektová dokumentácia (73 riadkov)
├── pyproject.toml              # Python projekt konfigurácia (31 riadkov)
├── requirements-contract.txt    # Contract test závislosti (6 riadkov)
├── Dockerfile                  # Container build konfigurácia
├── artifacts/                  # Výstupné súbory (prázdny)
├── schemas/                    # OpenAPI schémy (3 súbory JSON)
├── mockjira/                   # Hlavný mock server balík
├── mcp_jira/                   # MCP integration layer
├── clients/                    # Client adapters (Python)
├── examples/                   # Orchestrator demo examples
├── tests/                      # Comprehensive test suite
└── scripts/                    # Utility skripty
```

### 🔧 MCP_JIRA/ - MCP INTEGRATION LAYER

#### 📡 mcp_jira/server.py (30 riadkov)
```python
# FUNKCIE:
def get_tool(name: str):
    """Return a registered MCP tool callable by name"""

def invoke_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a tool with the provided arguments"""

def list_tools() -> Dict[str, Any]:
    """Return the metadata describing available tools"""
```

#### 🛠️ mcp_jira/tools.py (95 riadkov)
```python
# GLOBÁLNE OBJEKTY:
ADAPTER = JiraAdapter(...)  # Singleton JiraAdapter instance

# MCP TOOL FUNKCIE:
def t_jira_create_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre vytvorenie Jira issue"""

def t_jira_get_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre získanie Jira issue"""

def t_jira_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre JQL search"""

def t_jira_list_transitions(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre zoznam dostupných prechodov"""

def t_jira_transition_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre aplikovanie prechodu"""

def t_jira_add_comment(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre pridanie komentára"""

def t_jsm_create_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre vytvorenie JSM request"""

def t_agile_list_sprints(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre zoznam sprintov"""

# TOOL REGISTRY:
TOOL_REGISTRY: Dict[str, Callable] = {
    "jira.create_issue": t_jira_create_issue,
    "jira.get_issue": t_jira_get_issue,
    "jira.search": t_jira_search,
    "jira.list_transitions": t_jira_list_transitions,
    "jira.transition_issue": t_jira_transition_issue,
    "jira.add_comment": t_jira_add_comment,
    "jsm.create_request": t_jsm_create_request,
    "agile.list_sprints": t_agile_list_sprints,
}
```

### 🐍 CLIENTS/PYTHON/ - PYTHON CLIENT ADAPTER

#### 🔌 clients/python/jira_adapter.py (256 riadkov)
```python
# HLAVNÁ TRIEDA:
class JiraAdapter:
    """Thin wrapper around Jira REST endpoints with opinionated defaults"""

    def __init__(self, base_url: str, token: str, timeout: float = 10.0, user_agent: str = "MockJiraAdapter/1.0"):
        """Inicializácia s requests.Session a auth headers"""

    # UTILITY METÓDY:
    def _call(self, method: str, path: str, params=None, json_body=None) -> dict[str, Any]:
        """HTTP volanie s error handling a retry logikou"""

    def _handle_error(self, response: requests.Response) -> None:
        """Error handling pre HTTP responses"""

    # PLATFORM API METÓDY:
    def create_issue(self, project_key: str, issue_type_id: str, summary: str, description_adf=None, fields=None):
        """Vytvorenie nového issue"""

    def get_issue(self, key: str) -> dict[str, Any]:
        """Získanie issue podľa kľúča"""

    def list_transitions(self, key: str) -> list[dict[str, Any]]:
        """Zoznam dostupných prechodov pre issue"""

    def transition_issue(self, key: str, transition_id: str) -> dict[str, Any]:
        """Aplikovanie prechodu na issue"""

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        """Pridanie komentára k issue"""

    def search(self, jql: str, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        """JQL search s pagination"""

    def register_webhook(self, url: str, jql: str, events: list[str]) -> dict[str, Any]:
        """Registrácia webhook listenera"""

    # AGILE API METÓDY:
    def list_sprints(self, board_id: int, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        """Zoznam sprintov pre board"""

    # JSM API METÓDY:
    def create_request(self, service_desk_id: str, request_type_id: str, summary: str, fields=None) -> dict[str, Any]:
        """Vytvorenie JSM service request"""
```

#### ⚠️ clients/python/exceptions.py (20 riadkov)
```python
# VÝNIMKY:
class JiraAdapterError(Exception):
    """Base exception pre JiraAdapter"""

class JiraNotFoundError(JiraAdapterError):
    """404 Not Found exception"""

class JiraAuthError(JiraAdapterError):
    """401/403 Authentication/Authorization exception"""

class JiraRateLimitError(JiraAdapterError):
    """429 Rate Limit exception s retry_after"""
```

### 📦 MOCKJIRA/ - HLAVNÝ MOCK SERVER BALÍK

#### 🚀 mockjira/app.py (83 riadky)
```python
# FUNKCIE:
def create_app(store: InMemoryStore | None = None) -> FastAPI:
    """Vytvorí FastAPI aplikáciu s nakonfigurovanými routami
    - Nastaví dependency overrides pre auth
    - Pripojí všetky routery (platform, agile, service_management, webhooks, mock_admin)
    - Nastaví store do app.state
    - Pridá exception handlers a middleware
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

#### 💾 mockjira/store.py (1300+ riadkov) - NAJVÄČŠÍ SÚBOR
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
    sprint_id, comments, custom_fields"""

@dataclass class WebhookRegistration:
    """Webhook: id, url, events, jql"""

# HLAVNÁ TRIEDA:
class InMemoryStore:
    """Centrálny state container pre mock server s pokročilými funkciami"""

    def __init__(self):
        """Inicializácia všetkých collections a counters"""

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
        - 4 sample issues s komentármi
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

    def check_force_429(self, token: str) -> bool:
        """Kontrola X-Force-429 header simulácie"""

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
        """Definície polí (summary, description, labels, custom fields)"""

    def get_issue(self, key: str) -> Issue | None:
        """Získanie issue podľa kľúča"""

    def create_issue(self, payload: dict, reporter_id: str) -> Issue:
        """Vytvorenie nového issue s webhook dispatch"""

    def update_issue(self, key: str, payload: dict) -> Issue:
        """Aktualizácia issue s webhook dispatch"""

    def search_issues(self, filters: dict) -> list[Issue]:
        """Vyhľadávanie issues podľa filtrov (project, status, assignee, JQL)"""

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
        """Odoslanie webhook eventu všetkým listenerom s jitter a poison simulation"""

    def _send_webhook(self, url: str, delivery: dict) -> None:
        """HTTP POST webhook delivery (fail silently)"""

    # ADMIN & UTILITY METÓDY:
    def normalize_adf(self, value: Any) -> dict:
        """Normalizácia ADF payloadu"""

    def _ensure_service_request(self, issue: Issue) -> ServiceRequest:
        """Vytvorenie service request pre SUP issue"""

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parsovanie datetime hodnôt"""

    def reset_store(self) -> None:
        """Reset store do prázdneho stavu"""

    def load_from_json(self, payload: dict) -> None:
        """Načítanie store z JSON payload"""
```

#### 🛠️ mockjira/utils.py (72 riadkov)
```python
# VÝNIMKY:
class ApiError(Exception):
    """Base API error s HTTP status code a response generation"""

# FUNKCIE:
def parse_jql(jql: str | None) -> dict[str, Any]:
    """Parsuje podmnožinu JQL do dictionary filtrov
    - Podporuje IN a = operátory
    - Ignoruje ORDER BY klauzuly
    - Normalizuje quoted hodnoty
    - Podporuje currentUser() funkciu
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
__all__ = ["agile", "platform", "service_management", "webhooks", "mock_admin"]
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

#### 🔧 mockjira/routers/mock_admin.py (45 riadkov) - ADMIN API
```python
# HELPER FUNKCIE:
def get_store(request: Request) -> InMemoryStore:
    """Získa store z app.state"""

# API ENDPOINTS:
@router.post("/_mock/reset")
async def reset_store(...) -> dict:
    """POST /_mock/reset - Reset store do prázdneho stavu"""

@router.post("/_mock/load")
async def load_store(...) -> dict:
    """POST /_mock/load - Načítanie store z JSON payload"""

@router.get("/_mock/export")
async def export_store(...) -> dict:
    """GET /_mock/export - Export aktuálneho store stavu"""
```

### 📝 EXAMPLES/ - ORCHESTRATOR DEMO

#### 🎭 examples/orchestrator_demo.py (70 riadkov)
```python
# FUNKCIE:
def _adapter() -> JiraAdapter:
    """Vytvorí JiraAdapter s env konfiguráciou"""

def main() -> Dict[str, Any]:
    """Orchestrator demo workflow:
    - Registrácia webhook (ak je MOCKJIRA_WEBHOOK_URL nastavené)
    - Vytvorenie SUP issue s ADF description
    - Aplikovanie transition
    - Pridanie komentára
    - JQL search
    - JSM request vytvorenie
    - Agile sprint listing
    - Return summary s timing info
    """
```

---

## 🧪 TESTS/ - KOMPLEXNÁ TESTOVACIA SADA

### 📋 tests/test_mockjira.py (171 riadkov) - HLAVNÉ UNIT TESTY
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

### 🔧 tests/test_errors_and_limits.py (50 riadkov) - ERROR HANDLING TESTY
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_rate_limiting_behavior(client):
    """Test rate limiting logiky"""

@pytest.mark.asyncio
async def test_auth_errors(client):
    """Test authentication error handling"""

@pytest.mark.asyncio
async def test_not_found_errors(client):
    """Test 404 error responses"""
```

### 🐍 tests/clients/ - CLIENT ADAPTER TESTY

#### 🔄 tests/clients/test_adapter_issue_flow.py (80 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_issue_crud_flow(mock_server):
    """Test kompletného issue CRUD workflow cez JiraAdapter:
    - create_issue
    - get_issue
    - list_transitions
    - transition_issue
    - add_comment
    - search
    """

@pytest.mark.asyncio
async def test_webhook_registration(mock_server):
    """Test webhook registrácie cez adapter"""
```

#### 🎫 tests/clients/test_adapter_jsm_flow.py (40 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_jsm_request_flow(mock_server):
    """Test JSM request workflow cez JiraAdapter:
    - create_request
    - Validácia response štruktúry
    """
```

#### ⏱️ tests/clients/test_adapter_retry_rate_limit.py (60 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_rate_limit_retry(mock_server):
    """Test retry logiky pri rate limiting"""

@pytest.mark.asyncio
async def test_auth_error_handling(mock_server):
    """Test error handling pre auth errors"""
```

### 🎯 tests/mcp/ - MCP INTEGRATION TESTY

#### 🛠️ tests/mcp/test_mcp_golden_path.py (75 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_mcp_tools_golden_path(mock_server):
    """Test všetkých MCP tools v golden path scenári:
    - t_jira_create_issue
    - t_jira_get_issue
    - t_jira_list_transitions
    - t_jira_transition_issue
    - t_jira_add_comment
    - t_jira_search
    - t_jsm_create_request
    - t_agile_list_sprints
    - Validácia TOOL_REGISTRY
    """
```

### 🌐 tests/e2e/ - END-TO-END TESTY

#### 🎭 tests/e2e/test_orchestrator_flow.py (50 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.asyncio
async def test_orchestrator_demo_flow(mock_server):
    """Test orchestrator_demo.py workflow:
    - Spustenie kompletného demo
    - Validácia všetkých krokov
    - Kontrola webhook deliveries
    """
```

### 🔍 tests/contract/ - CONTRACT TESTY

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

### 💨 tests/smoke/ - SMOKE TESTY

#### 🌐 tests/smoke/test_against_real_jira.py (30 riadkov)
```python
# TEST FUNKCIE:
@pytest.mark.skipif(not os.getenv("REAL_JIRA_URL"), reason="Real Jira not configured")
def test_against_real_jira():
    """Smoke test proti reálnej Jira inštancii
    - Používa sa pre validáciu kompatibility
    - Spúšťa sa iba ak je REAL_JIRA_URL nastavené
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
├── jira-platform.v3.json     # Jira Platform REST API v3 schéma (veľká)
├── jira-software.v3.json     # Jira Software (Agile) API schéma (stredná)
└── jsm.v3.json              # Jira Service Management API schéma (malá)
```

## 📁 ARTIFACTS/ - VÝSTUPNÉ SÚBORY
```
artifacts/                    # Prázdny adresár pre generované súbory
├── parity.json              # (generovaný) Contract test výsledky
└── parity.md                # (generovaný) Human-readable parity report
```

---

## 📈 AKTUALIZOVANÉ ŠTATISTIKY PROJEKTU

### 📊 SÚBORY A RIADKY:
- **Celkový počet súborov**: 35+
- **Najväčší súbor**: mockjira/store.py (1300+ riadkov)
- **Celkový počet riadkov kódu**: ~2,500+
- **Python súbory**: 30+
- **Konfiguračné súbory**: 5

### 🔧 FUNKCIE A TRIEDY:
- **Celkový počet funkcií**: ~150+
- **Dataclasses**: 12 (User, Project, Issue, atď.)
- **API endpointy**: 25+ (Platform: 12, Agile: 4, JSM: 4, Webhooks: 4, Admin: 3)
- **MCP Tools**: 8 predefinovaných tools
- **Test funkcie**: 25+

### 🏗️ ARCHITEKTÚRA:
- **FastAPI routery**: 5 (platform, agile, service_management, webhooks, mock_admin)
- **MCP Integration Layer**: server.py + tools.py s TOOL_REGISTRY
- **Python Client Adapter**: JiraAdapter s retry logikou
- **Centrálny store**: InMemoryStore s 40+ metódami
- **Auth systém**: Bearer token + rate limiting + X-Force-429 simulation
- **Webhook systém**: Registration + delivery tracking + jitter simulation

### 🧪 KOMPLEXNÉ TESTOVANIE:
- **Unit testy**: 8 test súborov
- **Client adapter testy**: 3 test súbory
- **MCP integration testy**: 1 test súbor
- **E2E testy**: 1 test súbor
- **Contract testy**: 6 schemathesis testov
- **Smoke testy**: 1 test súbor proti reálnej Jira
- **Test coverage**: Platform, Agile, JSM, MCP, Client APIs

### 📦 ZÁVISLOSTI:
- **Runtime**: FastAPI, Uvicorn, Pydantic, httpx, requests
- **Testing**: pytest, pytest-asyncio, anyio
- **Contract testing**: schemathesis, openapi-core, prance
- **Python verzia**: >=3.11

### 🎯 API POKRYTIE:
- **Jira Platform API**: 12 endpointov (issues, search, comments, projects, fields, users, atď.)
- **Jira Software API**: 4 endpointy (boards, sprints, backlog)
- **JSM API**: 4 endpointy (requests, approvals)
- **Webhook API**: 4 endpointy (register, list, delete, deliveries)
- **Admin API**: 3 endpointy (reset, load, export)
- **MCP Tools**: 8 tools (jira.*, jsm.*, agile.*)

---

## 🚀 POUŽITIE A DEPLOYMENT

### 💻 Lokálny vývoj:
```bash
# Inštalácia
pip install -e .[test]

# Spustenie mock servera
mock-jira-server --port 9000

# Spustenie s prázdnym store
mock-jira-server --no-seed --port 9000
```

### 🧪 Testovanie:
```bash
# Unit a integration testy
pytest

# Contract testy proti OpenAPI schémam
python scripts/run_contracts.py

# Špecifické test kategórie
pytest tests/mcp/                    # MCP integration testy
pytest tests/clients/                # Client adapter testy
pytest tests/e2e/                    # End-to-end testy
pytest tests/contract/               # Contract testy
pytest tests/smoke/                  # Smoke testy
```

### 🐳 Docker deployment:
```bash
# Build image
docker build -t digital-spiral .

# Run container
docker run -p 9000:9000 digital-spiral
```

### 🔧 MCP Integration:
```python
# Použitie MCP tools
from mcp_jira import server

# Zoznam dostupných tools
tools = server.list_tools()

# Vyvolanie tool
result = server.invoke_tool("jira.create_issue", {
    "project_key": "DEV",
    "issue_type_id": "10001",
    "summary": "Test issue"
})
```

### 🐍 Python Client Adapter:
```python
# Použitie JiraAdapter
from clients.python.jira_adapter import JiraAdapter

adapter = JiraAdapter("http://localhost:9000", "mock-token")
issue = adapter.create_issue("DEV", "10001", "Test issue")
```

### 🔧 Rozšírenie:
- **Nové API endpointy**: Pridanie do príslušných routerov v `mockjira/routers/`
- **Nové MCP tools**: Rozšírenie `TOOL_REGISTRY` v `mcp_jira/tools.py`
- **Nové entity**: Pridanie dataclasses do `mockjira/store.py`
- **Nové seed dáta**: Úprava `_seed()` metódy v `InMemoryStore`
- **Client adapters**: Pridanie nových jazykov do `clients/`

---

## 🎯 ZÁVER

**Digital Spiral** predstavuje **komplexný ekosystém pre Jira Cloud API simuláciu a integráciu** s pokročilými funkciami:

### ✅ **Hlavné výhody:**
- **Stateful mock server** - Všetky zmeny sa zachovávajú v pamäti počas session
- **MCP integrácia** - Seamless integrácia s AI asistentmi cez Model Context Protocol
- **Python client adapter** - Production-ready wrapper s retry logikou a error handling
- **Realistické dáta** - Predvyplnené projekty, používatelia, issues, sprinty
- **Webhook systém** - Plne funkčný s delivery tracking a jitter simulation
- **Contract testing** - Validácia proti oficiálnym Atlassian OpenAPI schémam
- **Rate limiting** - Simulácia reálnych API limitov s X-Force-429 header
- **ADF support** - Atlassian Document Format pre rich text content
- **Comprehensive testing** - Unit, integration, contract, e2e a smoke testy
- **Admin API** - Reset, load a export funkcionalita pre testing scenarios

### 🎯 **Použitie:**
- **AI Assistant Integration** - MCP tools pre Jira operácie v AI workflows
- **Integration Testing** - Mock Jira pre testovanie aplikácií
- **Local Development** - Lokálny vývoj bez pripojenia k reálnej Jira
- **CI/CD Pipelines** - Automatizované testovanie s mock Jira
- **API Prototyping** - Rýchle prototypovanie Jira integrácie
- **Training & Demos** - Bezpečné prostredie pre školenia

### 🚀 **Technológie:**
- **Backend**: FastAPI + Uvicorn + Pydantic
- **Testing**: pytest + schemathesis + openapi-core
- **Client**: requests + httpx s retry logikou
- **MCP**: Model Context Protocol integration
- **Container**: Docker support
- **Python**: >=3.11 s type hints

Projekt je ideálny pre **AI-driven development**, **integračné testovanie**, **lokálny vývoj** a **CI/CD pipelines** kde je potrebné simulovať Jira Cloud API bez pripojenia k reálnej inštancii.
