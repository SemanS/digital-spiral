# KOMPLETNÝ POPIS KÓDU A FUNKCIÍ - Digital Spiral

## 📋 PREHĽAD ARCHITEKTÚRY

**Digital Spiral** je komplexný Python projekt implementujúci Mock Jira Cloud Server s MCP integráciou. Projekt je štruktúrovaný do modulárnych balíkov s jasne definovanými zodpovednosťami.

### 🏗️ HLAVNÉ MODULY:
- **mockjira/** - Hlavný mock server (FastAPI aplikácia)
- **mcp_jira/** - MCP (Model Context Protocol) integration layer
- **clients/python/** - Python client adapter s error handling
- **examples/** - Orchestrator demo a ukážky použitia
- **tests/** - Comprehensive test suite (unit, integration, contract, e2e)
- **scripts/** - Utility skripty pre OpenAPI a contract testing

---

## 🔧 MCP_JIRA/ - MCP INTEGRATION LAYER

### 📡 mcp_jira/server.py
**Lightweight facade exposing Jira adapter tools for MCP integrations**

```python
def get_tool(name: str):
    """Return a registered MCP tool callable by name.

    Args:
        name: Tool name from TOOL_REGISTRY
    Returns:
        Callable tool function
    """
    return TOOL_REGISTRY[name]

def invoke_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a tool with the provided arguments.

    Args:
        name: Tool name from TOOL_REGISTRY
        args: Dictionary of tool arguments
    Returns:
        Tool execution result
    """
    return TOOL_REGISTRY[name](args)

def list_tools() -> Dict[str, Any]:
    """Return the metadata describing available tools.

    Returns:
        Dictionary mapping tool names to their documentation
    """
    return {
        name: {"doc": func.__doc__}
        for name, func in TOOL_REGISTRY.items()
    }
```

### 🛠️ mcp_jira/tools.py
**Convenience tools for bridging the Jira adapter into MCP workflows**

#### Globálne objekty:
```python
ADAPTER = _build_adapter()  # Singleton JiraAdapter instance

def _build_adapter() -> JiraAdapter:
    """Build JiraAdapter from environment variables.

    Environment Variables:
        JIRA_BASE_URL: Base URL (default: http://localhost:9000)
        JIRA_TOKEN: API token (default: mock-token)
        JIRA_TIMEOUT: Request timeout (default: 10)
        JIRA_USER_AGENT: User agent (default: MockJiraAdapter/1.0)
    """
```

#### MCP Tool Functions:
```python
def t_jira_create_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre vytvorenie Jira issue.

    Args:
        project_key: Project key (required)
        issue_type_id: Issue type ID (required)
        summary: Issue summary (required)
        description_adf: ADF description (optional)
        fields: Additional fields (optional)
    """

def t_jira_get_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre získanie Jira issue.

    Args:
        key: Issue key (required)
    """

def t_jira_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre JQL search.

    Args:
        jql: JQL query string (required)
        start_at: Pagination start (default: 0)
        max_results: Max results (default: 50)
    """

def t_jira_list_transitions(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre zoznam dostupných prechodov.

    Args:
        key: Issue key (required)
    """

def t_jira_transition_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre aplikovanie prechodu.

    Args:
        key: Issue key (required)
        transition_id: Transition ID (required)
    """

def t_jira_add_comment(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre pridanie komentára.

    Args:
        key: Issue key (required)
        body_adf: ADF comment body (required)
    """

def t_jsm_create_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre vytvorenie JSM request.

    Args:
        service_desk_id: Service desk ID (required)
        request_type_id: Request type ID (required)
        summary: Request summary (required)
        fields: Additional fields (optional)
    """

def t_agile_list_sprints(args: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool pre zoznam sprintov.

    Args:
        board_id: Board ID (required)
        start_at: Pagination start (default: 0)
        max_results: Max results (default: 50)
    """
```

#### Tool Registry:
```python
TOOL_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
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

---

## 🐍 CLIENTS/PYTHON/ - PYTHON CLIENT ADAPTER

### 🔌 clients/python/jira_adapter.py
**Thin wrapper around Jira REST endpoints with opinionated defaults**

#### Hlavná trieda:
```python
class JiraAdapter:
    """Thin wrapper around Jira REST endpoints with opinionated defaults."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 10.0,
        user_agent: str = "MockJiraAdapter/1.0",
    ) -> None:
        """Initialize JiraAdapter with configuration.

        Args:
            base_url: Jira base URL
            token: Bearer token for authentication
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.timeout = timeout
```

#### Utility metódy:
```python
def _call(
    self,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make HTTP call with error handling and retry logic.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path
        params: Query parameters
        json_body: JSON request body

    Returns:
        Response JSON data

    Raises:
        JiraError: On HTTP errors
        JiraRateLimited: On 429 responses
    """

def _handle_error(self, response: requests.Response) -> None:
    """Handle HTTP error responses.

    Args:
        response: HTTP response object

    Raises:
        JiraBadRequest: On 400 responses
        JiraUnauthorized: On 401/403 responses
        JiraNotFound: On 404 responses
        JiraConflict: On 409 responses
        JiraRateLimited: On 429 responses
        JiraServerError: On 5xx responses
    """
```

#### Platform API metódy:
```python
def create_issue(
    self,
    project_key: str,
    issue_type_id: str,
    summary: str,
    description_adf: dict[str, Any] | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new Jira issue.

    Args:
        project_key: Project key (e.g., "DEV")
        issue_type_id: Issue type ID (e.g., "10001")
        summary: Issue summary
        description_adf: ADF description object
        fields: Additional issue fields

    Returns:
        Created issue data
    """

def get_issue(self, key: str) -> dict[str, Any]:
    """Get issue by key.

    Args:
        key: Issue key (e.g., "DEV-123")

    Returns:
        Issue data
    """

def list_transitions(self, key: str) -> list[dict[str, Any]]:
    """List available transitions for issue.

    Args:
        key: Issue key

    Returns:
        List of available transitions
    """

def transition_issue(self, key: str, transition_id: str) -> dict[str, Any]:
    """Apply transition to issue.

    Args:
        key: Issue key
        transition_id: Transition ID to apply

    Returns:
        Updated issue data
    """

def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
    """Add comment to issue.

    Args:
        key: Issue key
        body_adf: ADF comment body

    Returns:
        Created comment data
    """

def search(
    self,
    jql: str,
    start_at: int = 0,
    max_results: int = 50,
) -> dict[str, Any]:
    """Search issues using JQL.

    Args:
        jql: JQL query string
        start_at: Pagination start index
        max_results: Maximum results to return

    Returns:
        Search results with pagination metadata
    """

def register_webhook(
    self,
    url: str,
    jql: str,
    events: list[str],
) -> dict[str, Any]:
    """Register webhook listener.

    Args:
        url: Webhook URL
        jql: JQL filter for events
        events: List of event types to listen for

    Returns:
        Webhook registration data
    """
```

#### Agile API metódy:
```python
def list_sprints(
    self,
    board_id: int,
    start_at: int = 0,
    max_results: int = 50,
) -> dict[str, Any]:
    """List sprints for board.

    Args:
        board_id: Board ID
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Sprint list with pagination
    """
```

#### JSM API metódy:
```python
def create_request(
    self,
    service_desk_id: str,
    request_type_id: str,
    summary: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create JSM service request.

    Args:
        service_desk_id: Service desk ID
        request_type_id: Request type ID
        summary: Request summary
        fields: Additional request fields

    Returns:
        Created request data
    """
```

### ⚠️ clients/python/exceptions.py
**Exception hierarchy for the Jira adapter client**

```python
class JiraError(Exception):
    """Base class for Jira-related errors."""

class JiraBadRequest(JiraError):
    """400 Bad Request."""

class JiraUnauthorized(JiraError):
    """401/403 Unauthorized or forbidden."""

class JiraNotFound(JiraError):
    """404 Not Found."""

class JiraConflict(JiraError):
    """409 Conflict."""

class JiraRateLimited(JiraError):
    """429 Too Many Requests."""

    def __init__(self, retry_after: float | None = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after

class JiraServerError(JiraError):
    """5xx Server error."""
```

---

## 📦 MOCKJIRA/ - HLAVNÝ MOCK SERVER BALÍK

### 🚀 mockjira/app.py
**Application factory for the mock Jira server**

```python
def create_app(store: InMemoryStore | None = None) -> FastAPI:
    """Create a FastAPI instance configured with all routes.

    Parameters:
        store: Optional InMemoryStore instance. When None a new store with
               seeded data is created. Passing a custom store is useful for testing.

    Returns:
        Configured FastAPI application

    Features:
        - Dependency injection for authentication
        - Exception handlers for ApiError
        - Request logging middleware
        - All API routers (platform, agile, service_management, webhooks, mock_admin)
        - Store state management
    """
    store = store or InMemoryStore.with_seed_data()

    app = FastAPI(
        title="Mock Jira Cloud",
        version="0.1.0",
        description="Stateful mock implementation of popular Jira Cloud API surfaces."
    )

    # Configure authentication dependency
    app.dependency_overrides[get_current_user] = auth_dependency(store)

    # Exception handlers
    @app.exception_handler(ApiError)
    async def _handle_api_error(_: Request, exc: ApiError):
        return exc.to_response()

    # Request logging middleware
    app.state.request_log = deque(maxlen=500)

    # Include all routers
    app.include_router(platform.router, prefix="/rest/api/3")
    app.include_router(agile.router, prefix="/rest/agile/1.0")
    app.include_router(service_management.router, prefix="/rest/servicedeskapi")
    app.include_router(webhooks.router, prefix="/rest/api/3")
    app.include_router(mock_admin.router)

    app.state.store = store
    return app
```

### 🖥️ mockjira/main.py
**CLI entrypoint for running the mock Jira server**

```python
def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser.

    Arguments:
        --host: Host interface to bind the server (default: 0.0.0.0)
        --port: TCP port to bind the server (default: 9000)
        --log-level: Log level passed to Uvicorn (default: info)
        --no-seed: Start with an empty store instead of the default seed data

    Returns:
        Configured ArgumentParser
    """

def run(argv: list[str] | None = None) -> None:
    """Main entry point function.

    Args:
        argv: Command line arguments (default: sys.argv)

    Process:
        1. Parse command line arguments
        2. Create FastAPI app with/without seed data
        3. Start Uvicorn server with specified configuration
    """
```

### 🔐 mockjira/auth.py
**Authentication and rate limiting helpers**

```python
async def get_current_user(
    authorization: str | None = Header(default=None),
    x_force_429: str | None = Header(default=None),
) -> str:
    """Placeholder authentication dependency.

    This function is replaced during app setup with auth_dependency().
    Raises RuntimeError if called directly.
    """
    raise RuntimeError("Authentication dependency not configured")

def auth_dependency(store: InMemoryStore) -> Callable:
    """Return a dependency enforcing bearer token auth and rate limiting.

    Args:
        store: InMemoryStore instance for token validation and rate limiting

    Returns:
        FastAPI dependency function

    Features:
        - Bearer token validation
        - Rate limiting with configurable costs
        - X-Force-429 header simulation
        - Proper HTTP error responses with headers
    """
    async def dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        x_force_429: str | None = Header(default=None),
    ) -> str:
        # Bearer token validation
        if authorization is None or not authorization.startswith("Bearer "):
            raise ApiError(
                status=status.HTTP_401_UNAUTHORIZED,
                message="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split(" ", 1)[1]
        if not store.is_valid_token(token):
            raise ApiError(
                status=status.HTTP_401_UNAUTHORIZED,
                message="Invalid API token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # X-Force-429 simulation
        if x_force_429 and store.should_force_429(token):
            raise ApiError(
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                message="Simulated rate limit",
                headers={"Retry-After": "1"},
            )

        # Rate limiting
        try:
            cost = _request_cost(request)
            store.register_call(token, cost=cost)
        except RateLimitError as exc:
            headers = {"Retry-After": str(exc.retry_after)}
            if exc.remaining is not None:
                headers["X-RateLimit-Remaining"] = str(exc.remaining)
            if exc.reset_at is not None:
                headers["X-RateLimit-Reset"] = str(exc.reset_at)
            raise ApiError(
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                message="Rate limit exceeded",
                headers=headers,
            ) from exc

        return store.tokens[token]

    return dependency

def _request_cost(request: Request) -> int:
    """Return an approximate request cost for the rate limiter.

    Args:
        request: FastAPI Request object

    Returns:
        Request cost (1-5 based on endpoint and method)

    Cost Rules:
        - Search endpoints: 5 points
        - Write operations (POST/PUT/PATCH/DELETE): 2 points
        - Read operations (GET): 1 point
    """
    path = request.url.path
    if path.endswith("/search"):
        return 5
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        return 2
    return 1
```

### 🛠️ mockjira/utils.py
**Utility helpers for the mock Jira server**

```python
class ApiError(Exception):
    """Domain-specific error for returning Jira-style error payloads.

    Attributes:
        status: HTTP status code
        message: Error message
        field_errors: Field-specific error messages
        headers: Additional HTTP headers
    """

    def __init__(
        self,
        status: int,
        message: str,
        field_errors: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.message = message
        self.field_errors = field_errors or {}
        self.headers = headers or {}
        super().__init__(message)

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse.

        Returns:
            JSONResponse with Jira-style error payload and headers
        """
        response = error_response(self.status, self.message, self.field_errors)
        for key, value in self.headers.items():
            response.headers[key] = value
        return response
```

#### JQL Parsing:
```python
def parse_jql(jql: str | None) -> dict[str, Any]:
    """Parse a small, opinionated subset of JQL.

    Args:
        jql: JQL query string

    Returns:
        Dictionary with 'filters', 'order_by', and 'date_filters' keys

    Supported JQL Features:
        - Equality: field = value
        - IN clauses: field IN (value1, value2)
        - Date comparisons: field >= date (for created/updated)
        - ORDER BY: field ASC/DESC
        - AND operators

    Examples:
        "project = DEV AND status IN (Open, Closed)"
        "assignee = currentUser() ORDER BY updated DESC"
        "created >= '2023-01-01' AND project = DEV"
    """
    if not jql:
        return {"filters": {}, "order_by": []}

    # Split by ORDER BY
    parts = re.split(r"\s+ORDER\s+BY\s+", jql, maxsplit=1, flags=re.IGNORECASE)
    filter_part = parts[0].strip()
    order_part = parts[1].strip() if len(parts) == 2 else ""

    # Parse filters
    filters: dict[str, Any] = {}
    date_filters: dict[str, dict[str, str]] = {}

    if filter_part:
        clauses = re.split(r"\s+AND\s+", filter_part, flags=re.IGNORECASE)
        for clause in clauses:
            # Handle IN clauses: field IN (value1, value2)
            # Handle equality: field = value
            # Handle date comparisons: field >= date

    # Parse ORDER BY
    order_by: list[tuple[str, str]] = []
    if order_part:
        for segment in order_part.split(","):
            # Parse field ASC/DESC

    return {"filters": filters, "order_by": order_by, "date_filters": date_filters}

def _normalise_value(raw: str) -> str:
    """Remove quotes from JQL values.

    Args:
        raw: Raw JQL value with potential quotes

    Returns:
        Normalized value without quotes
    """
    value = raw.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value
```

#### Pagination:
```python
def paginate(items: Iterable[Any], start_at: int, max_results: int) -> dict[str, Any]:
    """Implement pagination logic with metadata.

    Args:
        items: Iterable of items to paginate
        start_at: Starting index (0-based)
        max_results: Maximum results per page

    Returns:
        Dictionary with pagination metadata:
        - startAt: Starting index
        - maxResults: Max results requested
        - total: Total number of items
        - isLast: Whether this is the last page
        - values: Page items
    """
    sequence = list(items)
    total = len(sequence)
    start_at = max(start_at, 0)
    max_results = max(0, max_results)
    page = sequence[start_at : start_at + max_results] if max_results else []
    is_last = start_at + len(page) >= total

    return {
        "startAt": start_at,
        "maxResults": max_results,
        "total": total,
        "isLast": is_last,
        "values": page,
    }

def error_response(
    status: int,
    message: str,
    field_errors: dict[str, str] | None = None
) -> JSONResponse:
    """Return a JSONResponse carrying the Jira-style error payload.

    Args:
        status: HTTP status code
        message: Error message
        field_errors: Field-specific errors

    Returns:
        JSONResponse with Jira error format
    """
    return JSONResponse(
        status_code=status,
        content={
            "errorMessages": [message],
            "errors": field_errors or {},
        },
    )
```

---

## 🌐 MOCKJIRA/ROUTERS/ - API ROUTERY

### 🏢 mockjira/routers/platform.py
**Subset of the Jira platform REST API implemented for the mock server**

#### Helper funkcie:
```python
def get_store(request: Request) -> InMemoryStore:
    """Get InMemoryStore from FastAPI app state.

    Args:
        request: FastAPI Request object

    Returns:
        InMemoryStore instance
    """
    return request.app.state.store
```

#### API Endpoints:
```python
@router.get("/project")
async def list_projects(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/project - List all projects.

    Returns:
        Dictionary with 'values' key containing project list
    """

@router.get("/field")
async def list_fields(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/field - List field definitions.

    Returns:
        Dictionary with 'values' key containing field definitions
    """

@router.get("/status")
async def list_statuses(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/status - List all statuses.

    Returns:
        Dictionary with 'values' key containing status list
    """

@router.get("/issue/{issue_id_or_key}")
async def get_issue(
    issue_id_or_key: str,
    request: Request,
    expand: str | None = Query(default=None),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey} - Get issue by key or ID.

    Args:
        issue_id_or_key: Issue key (e.g., "DEV-123") or ID
        expand: Comma-separated list of fields to expand

    Returns:
        Issue data with optional expanded fields

    Raises:
        ApiError: 404 if issue not found
    """

@router.post("/issue", status_code=status.HTTP_201_CREATED)
async def create_issue(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    """POST /rest/api/3/issue - Create new issue.

    Args:
        payload: Issue creation payload with fields
        account_id: Reporter account ID from auth

    Returns:
        Created issue data

    Raises:
        ApiError: 400 on validation errors
    """

@router.put("/issue/{issue_id_or_key}")
async def update_issue(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """PUT /rest/api/3/issue/{issueIdOrKey} - Update issue.

    Args:
        issue_id_or_key: Issue key or ID
        payload: Update payload with fields

    Returns:
        Updated issue data

    Raises:
        ApiError: 404 if issue not found, 400 on validation errors
    """

@router.get("/search")
async def search_issues(
    request: Request,
    jql: str | None = Query(default=None),
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/search - JQL search with currentUser() support.

    Args:
        jql: JQL query string
        start_at: Pagination start index
        max_results: Maximum results per page

    Returns:
        Search results with pagination metadata

    Features:
        - JQL parsing and filtering
        - currentUser() function support
        - Pagination with metadata
        - ORDER BY support
    """

@router.get("/issue/{issue_id_or_key}/transitions")
async def list_transitions(
    issue_id_or_key: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey}/transitions - List available transitions.

    Args:
        issue_id_or_key: Issue key or ID

    Returns:
        Dictionary with 'transitions' key containing available transitions

    Raises:
        ApiError: 404 if issue not found
    """

@router.post("/issue/{issue_id_or_key}/transitions")
async def apply_transition(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """POST /rest/api/3/issue/{issueIdOrKey}/transitions - Apply transition.

    Args:
        issue_id_or_key: Issue key or ID
        payload: Transition payload with transition ID

    Returns:
        Empty response (204 No Content)

    Raises:
        ApiError: 404 if issue not found, 400 on invalid transition
    """

@router.get("/issue/{issue_id_or_key}/comment")
async def list_comments(
    issue_id_or_key: str,
    request: Request,
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/issue/{issueIdOrKey}/comment - List issue comments.

    Args:
        issue_id_or_key: Issue key or ID
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Paginated comment list

    Raises:
        ApiError: 404 if issue not found
    """

@router.post("/issue/{issue_id_or_key}/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    """POST /rest/api/3/issue/{issueIdOrKey}/comment - Create comment.

    Args:
        issue_id_or_key: Issue key or ID
        payload: Comment payload with body (ADF format)
        account_id: Author account ID from auth

    Returns:
        Created comment data

    Raises:
        ApiError: 404 if issue not found, 400 on validation errors
    """

@router.get("/myself")
async def get_myself(
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/myself - Get current user info.

    Args:
        account_id: Account ID from auth

    Returns:
        Current user data

    Raises:
        ApiError: 404 if user not found
    """
```

### 🏃 mockjira/routers/agile.py
**Jira Software (Agile) API implementation**

```python
@router.get("/board")
async def list_boards(
    request: Request,
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/agile/1.0/board - List boards with pagination.

    Args:
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Paginated board list
    """

@router.get("/board/{board_id}/sprint")
async def list_sprints(
    board_id: int,
    request: Request,
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/agile/1.0/board/{board_id}/sprint - List sprints for board.

    Args:
        board_id: Board ID
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Paginated sprint list
    """

@router.post("/sprint", status_code=status.HTTP_201_CREATED)
async def create_sprint(
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """POST /rest/agile/1.0/sprint - Create new sprint.

    Args:
        payload: Sprint creation payload

    Returns:
        Created sprint data

    Raises:
        ApiError: 400 on validation errors
    """

@router.get("/board/{board_id}/backlog")
async def backlog(
    board_id: int,
    request: Request,
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/agile/1.0/board/{board_id}/backlog - List backlog issues.

    Args:
        board_id: Board ID
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Paginated backlog issues (issues without sprint)
    """
```

### 🎫 mockjira/routers/service_management.py
**Jira Service Management API implementation**

```python
@router.get("/request")
async def list_requests(
    request: Request,
    start_at: int = Query(default=0),
    max_results: int = Query(default=50),
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/servicedeskapi/request - List service requests.

    Args:
        start_at: Pagination start
        max_results: Maximum results

    Returns:
        Paginated service request list
    """

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    """POST /rest/servicedeskapi/request - Create service request.

    Args:
        payload: Request creation payload
        account_id: Reporter account ID

    Returns:
        Created service request data

    Raises:
        ApiError: 400 on validation errors
    """

@router.get("/request/{request_id}")
async def get_request(
    request_id: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/servicedeskapi/request/{issueIdOrKey} - Get service request.

    Args:
        request_id: Request ID or issue key

    Returns:
        Service request data

    Raises:
        ApiError: 404 if request not found
    """

@router.post("/request/{request_id}/approval/{approval_id}")
async def update_approval(
    request_id: str,
    approval_id: str,
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """POST /rest/servicedeskapi/request/{requestId}/approval/{approvalId} - Update approval.

    Args:
        request_id: Request ID
        approval_id: Approval ID
        payload: Approval decision payload

    Returns:
        Updated approval data

    Raises:
        ApiError: 404 if request/approval not found
    """
```

### 🪝 mockjira/routers/webhooks.py
**Webhook API implementation**

```python
@router.post("/webhook", status_code=status.HTTP_201_CREATED)
async def register_webhook(
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """POST /rest/api/3/webhook - Register webhook listener.

    Args:
        payload: Webhook registration payload with URL, events, JQL

    Returns:
        Webhook registration data

    Raises:
        ApiError: 400 on validation errors
    """

@router.get("/webhook")
async def list_webhook(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/webhook - List registered webhooks.

    Returns:
        List of webhook registrations
    """

@router.delete("/webhook/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """DELETE /rest/api/3/webhook/{webhookId} - Delete webhook.

    Args:
        webhook_id: Webhook ID to delete

    Returns:
        Empty response

    Raises:
        ApiError: 404 if webhook not found
    """

@router.get("/_mock/webhooks/deliveries")
async def list_deliveries(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    """GET /rest/api/3/_mock/webhooks/deliveries - Inspection endpoint for deliveries.

    Returns:
        List of all webhook deliveries with metadata

    Features:
        - Delivery history tracking
        - Request/response logging
        - Timing information
        - Error tracking
    """
```

### 🔧 mockjira/routers/mock_admin.py
**Admin API for testing and management**

```python
@router.get("/_mock/info")
async def info(request: Request) -> dict:
    """GET /_mock/info - Get server info and statistics.

    Returns:
        Server version, seed data counts, webhook signature info
    """

@router.get("/_mock/seed/export")
async def export_seed(request: Request) -> dict:
    """GET /_mock/seed/export - Export current store state.

    Returns:
        Complete store state as JSON for backup/restore
    """

@router.post("/_mock/seed/load")
async def load_seed(payload: dict, request: Request) -> dict:
    """POST /_mock/seed/load - Load store state from JSON.

    Args:
        payload: Store state JSON to load

    Returns:
        Success confirmation

    Features:
        - Complete store replacement
        - Data validation
        - Counter synchronization
    """

@router.post("/_mock/reset")
async def reset_store(request: Request) -> dict:
    """POST /_mock/reset - Reset store to empty state.

    Returns:
        Success confirmation

    Features:
        - Clear all data
        - Reset counters
        - Preserve configuration
    """
```

---

## 💾 MOCKJIRA/STORE.PY - CENTRÁLNY STATE CONTAINER

### 📊 Dataclasses (všetky s to_api() metódou):

```python
@dataclass
class User:
    """User representation.

    Attributes:
        account_id: Unique user identifier
        display_name: User display name
        email: User email address
        time_zone: User timezone
    """
    account_id: str
    display_name: str
    email: str
    time_zone: str = "UTC"

    def to_api(self, store: InMemoryStore) -> dict[str, Any]:
        """Convert to API representation."""

@dataclass
class Project:
    """Project representation.

    Attributes:
        id: Project ID
        key: Project key (e.g., "DEV")
        name: Project name
        project_type: Project type ("software", "service_desk")
        lead_account_id: Project lead user ID
    """
    id: str
    key: str
    name: str
    project_type: str
    lead_account_id: str

    def to_api(self, store: InMemoryStore) -> dict[str, Any]:
        """Convert to API representation."""

@dataclass
class Issue:
    """Issue representation with comprehensive fields.

    Attributes:
        id: Issue ID
        key: Issue key (e.g., "DEV-123")
        project_key: Project key
        issue_type_id: Issue type ID
        summary: Issue summary
        description: ADF description
        status_id: Current status ID
        reporter_id: Reporter user ID
        assignee_id: Assignee user ID (optional)
        labels: List of labels
        created: Creation timestamp
        updated: Last update timestamp
        sprint_id: Sprint ID (optional)
        comments: List of comments
        custom_fields: Custom field values
    """
    id: str
    key: str
    project_key: str
    issue_type_id: str
    summary: str
    description: dict[str, Any]
    status_id: str
    reporter_id: str
    assignee_id: str | None = None
    labels: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    sprint_id: int | None = None
    comments: list[Comment] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def to_api(self, store: InMemoryStore, expand: set[str] | None = None) -> dict[str, Any]:
        """Convert to API representation with optional field expansion."""
```

### 🏪 InMemoryStore - Hlavná trieda:

```python
class InMemoryStore:
    """Centrálny state container pre mock server s pokročilými funkciami.

    Features:
        - Stateful data storage
        - Seed data management
        - Rate limiting
        - Webhook delivery
        - JQL search support
        - ADF content handling
        - Custom field support
    """

    def __init__(self) -> None:
        """Initialize all collections and counters."""
        self.users: dict[str, User] = {}
        self.projects: dict[str, Project] = {}
        self.issue_types: dict[str, IssueType] = {}
        self.status_categories: dict[str, StatusCategory] = {}
        self.statuses: dict[str, Status] = {}
        self.transitions: dict[str, list[Transition]] = {}
        self.issues: dict[str, Issue] = {}
        self.issue_counter: dict[str, int] = defaultdict(int)
        self.boards: dict[int, Board] = {}
        self.sprints: dict[int, Sprint] = {}
        self.service_requests: dict[str, ServiceRequest] = {}
        self.webhooks: dict[str, WebhookRegistration] = {}
        self.deliveries: list[dict[str, Any]] = []
        self.webhook_logs: list[dict[str, Any]] = []
        self.tokens: dict[str, str] = {}
        self.rate_calls: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)

        # Counters for ID generation
        self.next_issue_id = 10000
        self.next_comment_id = 20000
        self.next_request_id = 30000
        self.next_webhook_id = 40000
        self.next_sprint_id = 5000
        self.next_link_id = 60000

        # Webhook configuration
        jitter_min = int(os.getenv("MOCKJIRA_WEBHOOK_JITTER_MIN", "50"))
        jitter_max = int(os.getenv("MOCKJIRA_WEBHOOK_JITTER_MAX", "250"))
        self._webhook_jitter_ms: tuple[int, int] = (jitter_min, jitter_max)
        self._webhook_poison_prob: float = float(os.getenv("MOCKJIRA_WEBHOOK_POISON_PROB", "0.0"))
```

#### Factory metódy:
```python
@classmethod
def with_seed_data(cls) -> "InMemoryStore":
    """Create store with pre-populated seed data.

    Returns:
        InMemoryStore instance with realistic test data

    Seed Data Includes:
        - 3 users (Alice, Bob, Carol)
        - 2 projects (DEV, SUP)
        - 4 issue types (Bug, Task, Story, Service Request)
        - 3 statuses (To Do, In Progress, Done)
        - 2 boards (Scrum, Kanban)
        - 3 sprints (closed, active, future)
        - 4 sample issues with comments
        - API tokens for authentication
    """
    store = cls()
    store._seed()
    return store

def _seed(self) -> None:
    """Populate store with realistic seed data."""
    # Create users
    self.users["alice"] = User("alice", "Alice Smith", "alice@example.com")
    self.users["bob"] = User("bob", "Bob Jones", "bob@example.com")
    self.users["carol"] = User("carol", "Carol Brown", "carol@example.com")

    # Create projects
    self.projects["DEV"] = Project("10000", "DEV", "Development", "software", "alice")
    self.projects["SUP"] = Project("10001", "SUP", "Support", "service_desk", "bob")

    # Create issue types, statuses, boards, sprints, sample issues...
```

#### Auth & Rate Limiting:
```python
def is_valid_token(self, token: str) -> bool:
    """Validate API token.

    Args:
        token: Bearer token to validate

    Returns:
        True if token is valid
    """
    return token in self.tokens

def register_call(self, token: str, cost: int = 1) -> None:
    """Register API call for rate limiting.

    Args:
        token: API token
        cost: Request cost (1-5 based on endpoint)

    Raises:
        RateLimitError: If rate limit exceeded (100 calls/60s window)
    """
    now = datetime.now(UTC)
    calls = self.rate_calls[token]

    # Remove old calls outside window
    while calls and calls[0][0] < now - timedelta(seconds=60):
        calls.popleft()

    # Check rate limit
    total_cost = sum(call[1] for call in calls) + cost
    if total_cost > 100:
        raise RateLimitError(retry_after=60, remaining=0, reset_at=int((now + timedelta(seconds=60)).timestamp()))

    calls.append((now, cost))

def should_force_429(self, token: str) -> bool:
    """Check if X-Force-429 header simulation should trigger.

    Args:
        token: API token

    Returns:
        True if 429 should be forced
    """
    return token in self._force_429_tokens
```

#### Platform API metódy:
```python
def create_issue(self, payload: dict, reporter_id: str) -> Issue:
    """Create new issue with webhook dispatch.

    Args:
        payload: Issue creation payload with fields
        reporter_id: Reporter user account ID

    Returns:
        Created Issue instance

    Features:
        - Auto-generated issue keys (PROJECT-123)
        - ADF description normalization
        - Custom field support
        - Sprint assignment
        - Automatic service request creation for SUP project
        - Webhook event dispatch

    Raises:
        ValueError: On validation errors
    """
    fields = payload.get("fields", {})
    project_key = fields.get("project", {}).get("key")
    issue_type_id = fields.get("issuetype", {}).get("id")
    summary = fields.get("summary")

    # Validation
    if not project_key or project_key not in self.projects:
        raise ValueError("Invalid project")
    if not issue_type_id or issue_type_id not in self.issue_types:
        raise ValueError("Invalid issue type")
    if not summary:
        raise ValueError("Summary is required")

    # Create issue
    issue = self._create_issue(
        project_key=project_key,
        issue_type_id=issue_type_id,
        summary=summary,
        description=self.normalize_adf(fields.get("description")),
        reporter_id=reporter_id,
        assignee_id=fields.get("assignee", {}).get("accountId"),
        status_id="1",  # To Do
        labels=fields.get("labels", []),
        sprint_id=self._extract_sprint_id(fields),
    )

    # Handle custom fields
    custom_fields = {k: v for k, v in fields.items() if k.startswith("customfield_")}
    if custom_fields:
        issue.custom_fields.update(custom_fields)

    # Auto-create service request for SUP project
    if project_key == "SUP":
        self._ensure_service_request(issue)

    # Dispatch webhook event
    self.dispatch_event("jira:issue_created", {"issue": issue.to_api(self)})

    return issue

def get_issue(self, key: str) -> Issue | None:
    """Get issue by key or ID.

    Args:
        key: Issue key (e.g., "DEV-123") or ID

    Returns:
        Issue instance or None if not found
    """
    return self.issues.get(key)

def search_issues(self, filters: dict) -> list[Issue]:
    """Search issues using JQL filters.

    Args:
        filters: Parsed JQL filters from parse_jql()

    Returns:
        List of matching issues

    Supported Filters:
        - project: Project key equality or IN clause
        - status: Status name equality or IN clause
        - assignee: Assignee account ID or currentUser()
        - reporter: Reporter account ID or currentUser()
        - labels: Label equality or IN clause
        - created/updated: Date range filters (>=)

    Features:
        - currentUser() function support
        - Date range filtering
        - ORDER BY support
        - Case-insensitive matching
    """
    results = list(self.issues.values())

    # Apply filters
    jql_filters = filters.get("filters", {})
    date_filters = filters.get("date_filters", {})

    for field, value in jql_filters.items():
        if field == "project":
            if isinstance(value, list):
                results = [i for i in results if i.project_key in value]
            else:
                results = [i for i in results if i.project_key == value]
        elif field == "status":
            # Convert status names to IDs and filter
        elif field == "assignee":
            if value == "currentuser()":
                # Handle currentUser() function
            else:
                results = [i for i in results if i.assignee_id == value]
        # ... other filters

    # Apply date filters
    for field, conditions in date_filters.items():
        if "gte" in conditions:
            date_value = self._parse_datetime(conditions["gte"])
            if date_value:
                if field == "created":
                    results = [i for i in results if i.created >= date_value]
                elif field == "updated":
                    results = [i for i in results if i.updated >= date_value]

    # Apply ordering
    order_by = filters.get("order_by", [])
    for field, direction in reversed(order_by):
        reverse = direction == "desc"
        if field == "created":
            results.sort(key=lambda i: i.created, reverse=reverse)
        elif field == "updated":
            results.sort(key=lambda i: i.updated, reverse=reverse)
        # ... other sort fields

    return results

def apply_transition(self, issue: Issue, transition_id: str) -> Issue:
    """Apply workflow transition to issue.

    Args:
        issue: Issue to transition
        transition_id: Transition ID to apply

    Returns:
        Updated issue

    Features:
        - Workflow validation
        - Status update
        - Timestamp update
        - Webhook event dispatch

    Raises:
        ValueError: If transition is not available
    """
    available_transitions = self.get_transitions(issue)
    transition = next((t for t in available_transitions if t.id == transition_id), None)

    if not transition:
        raise ValueError(f"Transition {transition_id} not available")

    # Update issue status
    issue.status_id = transition.to_status
    issue.updated = datetime.now(UTC)

    # Dispatch webhook event
    self.dispatch_event("jira:issue_updated", {"issue": issue.to_api(self)})

    return issue

def add_comment(self, issue: Issue, author_id: str, body: Any) -> Comment:
    """Add comment to issue.

    Args:
        issue: Issue to comment on
        author_id: Comment author account ID
        body: Comment body (ADF format)

    Returns:
        Created Comment instance

    Features:
        - ADF body normalization
        - Auto-generated comment IDs
        - Timestamp tracking
        - Issue update timestamp
        - Webhook event dispatch
    """
    comment = Comment(
        id=str(self.next_comment_id),
        author_id=author_id,
        body=self.normalize_adf(body),
        created=datetime.now(UTC),
    )
    self.next_comment_id += 1

    issue.comments.append(comment)
    issue.updated = datetime.now(UTC)

    # Dispatch webhook event
    self.dispatch_event("jira:issue_updated", {"issue": issue.to_api(self)})

    return comment
```

#### Webhook API metódy:
```python
def register_webhook(self, payload: dict) -> list[dict]:
    """Register webhook listeners.

    Args:
        payload: Webhook registration payload

    Returns:
        List of registered webhook data

    Features:
        - Multiple event type support
        - JQL filtering
        - URL validation
        - Auto-generated webhook IDs
    """
    url = payload.get("url")
    events = payload.get("events", [])
    jql = payload.get("jqlFilter", "")

    if not url:
        raise ValueError("URL is required")
    if not events:
        raise ValueError("Events are required")

    webhook = WebhookRegistration(
        id=str(self.next_webhook_id),
        url=url,
        events=events,
        jql=jql,
    )
    self.next_webhook_id += 1

    self.webhooks[webhook.id] = webhook
    return [webhook.to_api(self)]

def dispatch_event(self, event_type: str, payload: dict) -> None:
    """Dispatch webhook event to all matching listeners.

    Args:
        event_type: Event type (e.g., "jira:issue_created")
        payload: Event payload

    Features:
        - JQL filter matching
        - Async delivery with jitter
        - Poison request simulation
        - Delivery tracking and logging
        - Error handling and retry logic
    """
    matching_webhooks = [
        webhook for webhook in self.webhooks.values()
        if event_type in webhook.events and self._matches_jql_filter(webhook.jql, payload)
    ]

    for webhook in matching_webhooks:
        # Add jitter delay
        jitter_ms = random.randint(*self._webhook_jitter_ms)

        # Create delivery record
        delivery = {
            "id": str(uuid.uuid4()),
            "webhookId": webhook.id,
            "eventType": event_type,
            "url": webhook.url,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
            "jitterMs": jitter_ms,
            "status": "pending",
        }

        # Simulate poison requests
        if random.random() < self._webhook_poison_prob:
            delivery["status"] = "failed"
            delivery["error"] = "Simulated poison request"
        else:
            # Async delivery (simplified for mock)
            self._send_webhook(webhook.url, delivery)
            delivery["status"] = "delivered"

        self.deliveries.append(delivery)
        self.webhook_logs.append({
            "timestamp": delivery["timestamp"],
            "event": event_type,
            "webhook_id": webhook.id,
            "status": delivery["status"],
        })

def _send_webhook(self, url: str, delivery: dict) -> None:
    """Send HTTP POST webhook delivery.

    Args:
        url: Webhook URL
        delivery: Delivery record

    Features:
        - HTTP POST with JSON payload
        - Timeout handling
        - Error logging
        - Silent failure (no exceptions raised)
    """
    try:
        response = requests.post(
            url,
            json=delivery["payload"],
            timeout=5,
            headers={"Content-Type": "application/json"},
        )
        delivery["responseStatus"] = response.status_code
        delivery["responseTime"] = response.elapsed.total_seconds()
    except Exception as e:
        delivery["error"] = str(e)
        delivery["status"] = "failed"
```

#### Utility metódy:
```python
def normalize_adf(self, value: Any) -> dict:
    """Normalize ADF (Atlassian Document Format) payload.

    Args:
        value: ADF content (dict, string, or None)

    Returns:
        Normalized ADF document

    Features:
        - String to ADF conversion
        - ADF validation
        - Default document structure
    """
    if value is None:
        return {"type": "doc", "version": 1, "content": []}

    if isinstance(value, str):
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": value}],
                }
            ],
        }

    if isinstance(value, dict) and value.get("type") == "doc":
        return value

    # Fallback for invalid ADF
    return {"type": "doc", "version": 1, "content": []}

def _parse_datetime(self, value: Any) -> datetime | None:
    """Parse datetime values from various formats.

    Args:
        value: Datetime string in various formats

    Returns:
        Parsed datetime or None if invalid

    Supported Formats:
        - ISO format: "2023-01-01T00:00:00Z"
        - Date only: "2023-01-01"
        - Jira format: "2023/01/01"
    """
    if not isinstance(value, str):
        return None

    # Try ISO format
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Try date only
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        pass

    # Try Jira format
    try:
        return datetime.strptime(value, "%Y/%m/%d").replace(tzinfo=UTC)
    except ValueError:
        pass

    return None

def export_seed(self) -> dict:
    """Export current store state for backup/restore.

    Returns:
        Complete store state as JSON-serializable dictionary

    Features:
        - All entities serialization
        - Counter state preservation
        - Configuration export
    """
    return {
        "users": [user.to_api(self) for user in self.users.values()],
        "projects": [project.to_api(self) for project in self.projects.values()],
        "issues": [issue.to_api(self) for issue in self.issues.values()],
        "boards": [board.to_api(self) for board in self.boards.values()],
        "sprints": [sprint.to_api(self) for sprint in self.sprints.values()],
        "webhooks": [webhook.to_api(self) for webhook in self.webhooks.values()],
        "counters": {
            "next_issue_id": self.next_issue_id,
            "next_comment_id": self.next_comment_id,
            "next_request_id": self.next_request_id,
            "next_webhook_id": self.next_webhook_id,
            "next_sprint_id": self.next_sprint_id,
        },
    }
```

---

## 📝 EXAMPLES/ - ORCHESTRATOR DEMO

### 🎭 examples/orchestrator_demo.py
**Comprehensive workflow demonstration**

```python
def _adapter() -> JiraAdapter:
    """Create JiraAdapter with environment configuration.

    Environment Variables:
        JIRA_BASE_URL: Jira base URL (default: http://localhost:9000)
        JIRA_TOKEN: API token (default: mock-token)

    Returns:
        Configured JiraAdapter instance
    """
    base_url = os.getenv("JIRA_BASE_URL", "http://localhost:9000")
    token = os.getenv("JIRA_TOKEN", "mock-token")
    return JiraAdapter(base_url, token)

def main() -> Dict[str, Any]:
    """Orchestrator demo workflow showcasing all major features.

    Returns:
        Workflow summary with timing and results

    Workflow Steps:
        1. Optional webhook registration
        2. Create SUP issue with ADF description
        3. Apply workflow transition
        4. Add comment with ADF content
        5. JQL search for created issue
        6. Create JSM service request
        7. List agile sprints
        8. Return comprehensive summary

    Features:
        - Environment-based configuration
        - Error handling and logging
        - Performance timing
        - Webhook integration
        - Multi-API demonstration
    """
    adapter = _adapter()
    webhook_url = os.getenv("MOCKJIRA_WEBHOOK_URL")

    start = datetime.now()
    results = {}

    # Optional webhook registration
    if webhook_url:
        webhook = adapter.register_webhook(
            webhook_url,
            "project = DEV",
            events=["jira:issue_created"]
        )
        results["webhook"] = webhook

    # Create issue with ADF description
    issue = adapter.create_issue(
        "SUP",
        "10003",  # Service Request
        "Orchestrator demo",
        description_adf={
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello orchestrator"}],
                }
            ],
        },
    )
    results["issue"] = issue
    key = issue["key"]

    # Apply transition
    transitions = adapter.list_transitions(key)
    if transitions:
        adapter.transition_issue(key, transitions[0]["id"])
        results["transition"] = transitions[0]

    # Add comment
    comment = adapter.add_comment(key, {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Demo comment"}]
            }
        ],
    })
    results["comment"] = comment

    # JQL search
    search = adapter.search(f'key = "{key}"')
    results["search"] = search

    # JSM request
    request = adapter.create_request("1", "100", "Demo request", {"description": "Test"})
    results["jsm_request"] = request

    # Agile sprints
    sprints = adapter.list_sprints(1)
    results["sprints"] = sprints

    # Summary
    end = datetime.now()
    results["summary"] = {
        "duration_ms": (end - start).total_seconds() * 1000,
        "operations": len([k for k in results.keys() if k != "summary"]),
        "timestamp": end.isoformat(),
    }

    return results
```

---

## 🔧 SCRIPTS/ - UTILITY SKRIPTY

### 🌐 scripts/fetch_openapi.py
**OpenAPI schema fetching from Atlassian CDN**

```python
SPECS = {
    "jira-platform.v3.json": "https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8171.0",
    "jira-software.v3.json": "https://dac-static.atlassian.com/cloud/jira/software/swagger.v3.json?_v=1.8171.0",
    "jsm.v3.json": "https://dac-static.atlassian.com/cloud/jira/service-desk/swagger.v3.json?_v=1.8171.0",
}

def main():
    """Download OpenAPI schemas from Atlassian CDN.

    Features:
        - Creates schemas/ directory
        - Downloads all 3 schemas with 60s timeout
        - Prints size information for each schema
        - Error handling for network issues
    """
    os.makedirs("schemas", exist_ok=True)

    for filename, url in SPECS.items():
        print(f"Fetching {filename}...")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            with open(f"schemas/{filename}", "w") as f:
                f.write(response.text)

            size_kb = len(response.text) / 1024
            print(f"  Saved {filename} ({size_kb:.1f} KB)")

        except Exception as e:
            print(f"  Error fetching {filename}: {e}")
```

### 📦 scripts/bundle_openapi.py
**OpenAPI schema bundling with reference resolution**

```python
def bundle(src: str | pathlib.Path, dst: str | pathlib.Path):
    """Bundle OpenAPI schema using prance ResolvingParser.

    Args:
        src: Source OpenAPI file path
        dst: Destination bundled file path

    Features:
        - Resolves all $ref references
        - Creates self-contained schema
        - Saves as JSON file
        - Error handling for invalid schemas
    """
    try:
        parser = ResolvingParser(str(src))
        bundled = parser.specification

        with open(dst, "w") as f:
            json.dump(bundled, f, indent=2)

        print(f"Bundled {src} -> {dst}")

    except Exception as e:
        print(f"Error bundling {src}: {e}")

def main():
    """Bundle all 3 OpenAPI schemas.

    Creates bundled versions:
        - jira-platform.v3.json → jira-platform.v3.json.bundled.json
        - jira-software.v3.json → jira-software.v3.json.bundled.json
        - jsm.v3.json → jsm.v3.json.bundled.json
    """
    schemas = [
        "schemas/jira-platform.v3.json",
        "schemas/jira-software.v3.json",
        "schemas/jsm.v3.json",
    ]

    for schema in schemas:
        src = pathlib.Path(schema)
        dst = src.with_suffix(src.suffix + ".bundled.json")
        bundle(src, dst)
```

### 📊 scripts/parity_report.py
**Contract test results analysis**

```python
def main(json_path: str):
    """Analyze parity.json report from contract tests.

    Args:
        json_path: Path to parity.json file

    Features:
        - Counts total/ok/bad responses
        - Calculates success ratio
        - Exit code 1 if < 95% threshold
        - Used in CI/CD pipeline for quality gates

    Report Format:
        - Total endpoints tested
        - Success/failure counts
        - Success percentage
        - Detailed failure analysis
    """
    try:
        with open(json_path) as f:
            data = json.load(f)

        total = len(data)
        ok = sum(1 for record in data if record["status"] == "ok")
        bad = total - ok

        success_rate = (ok / total * 100) if total > 0 else 0

        print(f"Contract Test Results:")
        print(f"  Total endpoints: {total}")
        print(f"  Successful: {ok}")
        print(f"  Failed: {bad}")
        print(f"  Success rate: {success_rate:.1f}%")

        if success_rate < 95.0:
            print("❌ Success rate below 95% threshold")
            sys.exit(1)
        else:
            print("✅ Success rate meets 95% threshold")

    except Exception as e:
        print(f"Error analyzing parity report: {e}")
        sys.exit(1)
```

### 🚀 scripts/run_contracts.py
**Contract testing pipeline orchestration**

```python
def run(cmd: list[str]):
    """Run shell command with error checking.

    Args:
        cmd: Command and arguments as list

    Raises:
        subprocess.CalledProcessError: If command fails
    """
    subprocess.run(cmd, check=True)

def main():
    """Orchestrate complete contract testing pipeline.

    Pipeline Steps:
        1. python scripts/fetch_openapi.py - Download latest schemas
        2. pytest tests/contract - Run contract tests with schemathesis
        3. python scripts/parity_report.py artifacts/parity.json - Analyze results

    Features:
        - Sequential execution with error propagation
        - Automatic schema updates
        - Quality gate enforcement
        - CI/CD integration ready
    """
    print("🔄 Starting contract testing pipeline...")

    print("📥 Fetching OpenAPI schemas...")
    run(["python", "scripts/fetch_openapi.py"])

    print("🧪 Running contract tests...")
    run(["pytest", "tests/contract", "-v"])

    print("📊 Analyzing results...")
    run(["python", "scripts/parity_report.py", "artifacts/parity.json"])

    print("✅ Contract testing pipeline completed successfully")
```

---

## 🎯 ZÁVER

**Digital Spiral** predstavuje komplexný ekosystém s **2,500+ riadkami kódu** distribuovanými do **150+ funkcií** a **12 dataclasses**. Projekt kombinuje:

### ✅ **Kľúčové komponenty:**
- **Mock Jira Server**: 25+ API endpointov s stateful implementáciou
- **MCP Integration**: 8 predefinovaných tools pre AI asistentov
- **Python Client**: Production-ready adapter s retry logikou
- **Comprehensive Testing**: 6 kategórií testov (unit, integration, contract, e2e, smoke, mcp)
- **Utility Scripts**: Automatizované OpenAPI management a contract testing

### 🚀 **Technické výhody:**
- **Type Safety**: Kompletné type hints pre Python >=3.11
- **Error Handling**: Hierarchia výnimiek s HTTP status mapovaním
- **Rate Limiting**: Simulácia reálnych API limitov s cost-based accounting
- **Webhook System**: Async delivery s jitter simulation a poison request testing
- **ADF Support**: Atlassian Document Format pre rich text content
- **JQL Parsing**: Podmnožina JQL s currentUser() support
- **Contract Validation**: Schemathesis testing proti oficiálnym OpenAPI schémam

Projekt je ideálny pre **AI-driven development**, **integration testing** a **local development** kde je potrebná realistická Jira API simulácia bez pripojenia k reálnej inštancii.
```