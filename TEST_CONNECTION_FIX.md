# 🔧 Test Connection - Opravené!

## ✅ Test Connection endpoint je teraz funkčný!

---

## 🐛 Problém

**Chyba**: `Request failed with status 422`

**Príčina**: 
- Frontend posiela dáta v camelCase formáte (`baseUrl`, `apiToken`, `authMethod`)
- Backend očakával snake_case formát (`base_url`, `api_token`, `auth_method`)
- Pydantic model nemal aliasy pre camelCase

---

## 🔧 Riešenie

### 1. Aktualizovaný Pydantic model

**Súbor**: `src/interfaces/rest/routers/instances.py`

```python
class TestConnectionRequest(BaseModel):
    """Model for test connection request"""
    base_url: str = Field(..., alias="baseUrl")
    email: str
    api_token: str = Field(..., alias="apiToken")
    auth_method: Optional[str] = Field(None, alias="authMethod")
    name: Optional[str] = None
    project_filter: Optional[str] = Field(None, alias="projectFilter")
    
    class Config:
        populate_by_name = True
```

**Zmeny**:
- ✅ Pridané `alias="baseUrl"` pre `base_url`
- ✅ Pridané `alias="apiToken"` pre `api_token`
- ✅ Pridané `alias="authMethod"` pre `auth_method`
- ✅ Pridané `alias="projectFilter"` pre `project_filter`
- ✅ Pridané `populate_by_name = True` v Config

### 2. Implementované skutočné testovanie

**Pred**:
```python
# For now, return mock response
return {
    "success": True,
    "message": "Connection successful",
    "details": {
        "jira_version": "9.4.0",
        "projects_found": 5,
        "user": request.email,
    }
}
```

**Po**:
```python
try:
    from clients.python.jira_cloud_adapter import JiraCloudAdapter
    
    # Create adapter with provided credentials
    adapter = JiraCloudAdapter(
        base_url=request.base_url,
        email=request.email,
        api_token=request.api_token,
    )
    
    # Test connection by getting current user
    user_info = adapter.get_myself()
    
    return {
        "success": True,
        "message": "Connection successful",
        "details": {
            "user": user_info.get("displayName", request.email),
            "account_id": user_info.get("accountId"),
            "email": user_info.get("emailAddress", request.email),
        }
    }
except Exception as e:
    return {
        "success": False,
        "message": f"Connection failed: {str(e)}",
        "details": None
    }
```

**Zmeny**:
- ✅ Importovaný `JiraCloudAdapter`
- ✅ Vytvorený adapter s poskytnutými credentials
- ✅ Zavolaný `get_myself()` na testovanie pripojenia
- ✅ Vrátené skutočné user info z Jira
- ✅ Pridaný error handling

---

## 🧪 Testovanie

### 1. Test cez Swagger UI

```bash
# Open Swagger UI
open http://localhost:8000/docs#/instances/test_connection_direct_api_instances_test_connection_post
```

**Request Body**:
```json
{
  "baseUrl": "https://insight-bridge.atlassian.net",
  "email": "slavomir.seman@hotovo.com",
  "apiToken": "your-api-token-here",
  "authMethod": "api_token"
}
```

**Expected Response (Success)**:
```json
{
  "success": true,
  "message": "Connection successful",
  "details": {
    "user": "Slavomir Seman",
    "account_id": "5f8a1234567890abcdef1234",
    "email": "slavomir.seman@hotovo.com"
  }
}
```

**Expected Response (Failure)**:
```json
{
  "success": false,
  "message": "Connection failed: 401 Unauthorized",
  "details": null
}
```

### 2. Test cez Admin UI

```bash
# Open Add Instance page
open http://localhost:3002/admin/instances/new
```

**Steps**:
1. Vyplňte formulár:
   - **Name**: Test Instance
   - **Base URL**: https://insight-bridge.atlassian.net
   - **Auth Method**: API Token
   - **Email**: slavomir.seman@hotovo.com
   - **API Token**: your-api-token-here

2. Kliknite na **Test Connection**

3. Očakávaný výsledok:
   - ✅ "Connection successful"
   - ✅ Zobrazí sa user info
   - ✅ Zelená ikona

### 3. Test cez cURL

```bash
curl -X POST http://localhost:8000/api/instances/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "baseUrl": "https://insight-bridge.atlassian.net",
    "email": "slavomir.seman@hotovo.com",
    "apiToken": "your-api-token-here",
    "authMethod": "api_token"
  }'
```

---

## 📊 API Endpoint

### POST /api/instances/test-connection

**Request Body**:
```typescript
{
  baseUrl: string;      // Jira base URL (e.g., https://company.atlassian.net)
  email: string;        // Email for authentication
  apiToken: string;     // API token
  authMethod?: string;  // Optional: 'api_token' or 'oauth'
  name?: string;        // Optional: Instance name
  projectFilter?: string; // Optional: Comma-separated project keys
}
```

**Response**:
```typescript
{
  success: boolean;
  message: string;
  details?: {
    user: string;       // Display name
    account_id: string; // Jira account ID
    email: string;      // Email address
  } | null;
}
```

**Status Codes**:
- `200 OK` - Test completed (check `success` field)
- `422 Unprocessable Entity` - Invalid request body
- `500 Internal Server Error` - Server error

---

## 🔑 Ako získať Jira API Token

### 1. Prihláste sa do Atlassian

```bash
open https://id.atlassian.com/manage-profile/security/api-tokens
```

### 2. Vytvorte nový API token

1. Kliknite na **Create API token**
2. Zadajte label (napr. "Digital Spiral")
3. Kliknite na **Create**
4. **Skopírujte token** (zobrazí sa len raz!)

### 3. Použite token v Admin UI

1. Otvorte Add Instance page
2. Vyplňte:
   - **Email**: Váš Atlassian email
   - **API Token**: Skopírovaný token
3. Kliknite na **Test Connection**

---

## 🛠️ Troubleshooting

### Error: "401 Unauthorized"

**Príčina**: Nesprávny email alebo API token

**Riešenie**:
1. Overte, že email je správny
2. Vytvorte nový API token
3. Skúste znova

### Error: "404 Not Found"

**Príčina**: Nesprávna base URL

**Riešenie**:
1. Overte, že base URL je správna (napr. `https://company.atlassian.net`)
2. Nepoužívajte `/` na konci URL
3. Skúste znova

### Error: "Connection timeout"

**Príčina**: Sieťový problém alebo firewall

**Riešenie**:
1. Overte internetové pripojenie
2. Skontrolujte firewall nastavenia
3. Skúste iný network

### Error: "422 Unprocessable Entity"

**Príčina**: Nesprávny formát request body

**Riešenie**:
1. Overte, že používate camelCase (`baseUrl`, `apiToken`)
2. Overte, že všetky required fields sú vyplnené
3. Skontrolujte Swagger UI pre správny formát

---

## 📁 Zmenené súbory

### Backend
1. ✅ `src/interfaces/rest/routers/instances.py`
   - Pridané aliasy pre camelCase
   - Implementované skutočné testovanie s JiraCloudAdapter
   - Pridaný error handling

---

## ✅ Status

```
✅ Pydantic model - Updated with aliases
✅ Test connection - Implemented with JiraCloudAdapter
✅ Error handling - Added
✅ Backend API - Reloaded
✅ Swagger UI - Updated
✅ Admin UI - Ready to test
```

---

## 🎯 Ďalšie kroky

### 1. Otestujte pripojenie

```bash
open http://localhost:3002/admin/instances/new
```

### 2. Vytvorte inštanciu

Po úspešnom teste:
1. Kliknite na **Save**
2. Inštancia sa uloží do databázy
3. Môžete začať používať AI Assistant

### 3. Použite AI Assistant

```bash
open http://localhost:3002/admin/assistant
```

Príkazy:
```
Vyhľadaj všetky issues v projekte SCRUM
```

```
Pridaj komentár do /SCRUM-229 že pracujem na tom
```

---

## 📚 Dokumentácia

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[AI_ASSISTANT_INTEGRATED.md](AI_ASSISTANT_INTEGRATED.md)** - AI Assistant integration
- **[AI_ASSISTANT_FIXED.md](AI_ASSISTANT_FIXED.md)** - AI Assistant fixes
- **[TEST_CONNECTION_FIX.md](TEST_CONNECTION_FIX.md)** - This file

---

**Test Connection je teraz funkčný! 🎉**

Môžete otestovať pripojenie k Jira a vytvoriť novú inštanciu!

---

**Happy testing! 🚀**

