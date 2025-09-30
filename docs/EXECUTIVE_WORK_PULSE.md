# 📊 Executive Work Pulse

**Jednopanelový dashboard pre top manažérov** - okamžitý prehľad o stave práce naprieč tímami/projektmi bez potreby otvárať Jiru.

---

## 🎯 Cieľ

Poskytnúť top manažérom **5 kľúčových metrik** na jednu obrazovku:

1. **Throughput** - koľko práce sa dokončilo vs. vytvorilo
2. **Lead Time** - ako dlho trvá dokončenie práce
3. **SLA Risk** - koľko ticketov je blízko porušenia SLA
4. **Work-in-Progress** - koľko práce je rozpracovanej
5. **Quality** - koľko ticketov sa znova otvorilo

Plus **Top 10 rizík** a **4-týždňové trendy**.

---

## 🏗️ Architektúra

### Dátový model

```
┌─────────────────┐
│  Jira Instance  │  ← Konfigurácia pripojení (multi-instance)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Work Item     │  ← Unified model (Jira/GitHub/Zendesk/PagerDuty)
└────────┬────────┘
         │
         ├──► WorkItemTransition  (status history)
         ├──► WorkItemSLA         (SLA tracking)
         └──► WorkItemMetricDaily (denné agregácie)
```

### Tok dát

```
Jira Cloud
    │
    ├──► Backfill (REST API)  ──┐
    │                            │
    └──► Webhooks (real-time) ──┤
                                 │
                                 ▼
                         ┌───────────────┐
                         │  Work Items   │
                         │   (staging)   │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │  Daily Rollup │  ← Cron job (03:00)
                         │     (mart)    │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │   Dashboard   │
                         │   (< 2s load) │
                         └───────────────┘
```

---

## 📊 Metriky (presné definície)

### 1. Throughput

```sql
-- Created: počet vytvorených work items v období
SELECT COUNT(*) FROM work_items 
WHERE created_at BETWEEN :start AND :end

-- Closed: počet uzavretých work items v období  
SELECT COUNT(*) FROM work_items
WHERE closed_at BETWEEN :start AND :end

-- Delta vs 4W avg: (týždeň - priemer posledných 4 týždňov) / priemer
```

### 2. Lead Time (P50/P90)

```sql
-- Pre každé uzavreté work item: first_time("In Progress") → closed_at v dňoch
-- Percentily počítané nad uzavretými v období

SELECT 
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lead_time_days) AS p50,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY lead_time_days) AS p90
FROM (
  SELECT 
    wi.id,
    EXTRACT(EPOCH FROM (wi.closed_at - wit.timestamp)) / 86400 AS lead_time_days
  FROM work_items wi
  JOIN work_item_transitions wit ON wi.id = wit.work_item_id
  WHERE wi.closed_at BETWEEN :start AND :end
    AND wit.to_status = 'In Progress'
    AND wit.timestamp = (
      SELECT MIN(timestamp) FROM work_item_transitions
      WHERE work_item_id = wi.id AND to_status = 'In Progress'
    )
) lead_times
```

### 3. SLA Risk (24h)

```sql
-- Počet work items s SLA due_at ≤ 24h a breached = false
SELECT COUNT(*) FROM work_item_slas
WHERE breached = false
  AND due_at <= NOW() + INTERVAL '24 hours'
```

### 4. WIP / No Assignee / Stuck

```sql
-- WIP: work items not in {Done, Closed}
SELECT COUNT(*) FROM work_items
WHERE status NOT IN ('Done', 'Closed')

-- No Assignee: WIP without assignee
SELECT COUNT(*) FROM work_items
WHERE status NOT IN ('Done', 'Closed')
  AND assignee IS NULL

-- Stuck: WIP with last_transition_at > X days ago
SELECT COUNT(*) FROM work_items
WHERE status NOT IN ('Done', 'Closed')
  AND last_transition_at < NOW() - INTERVAL '3 days'
```

### 5. Quality (Reopen Rate)

```sql
-- Reopened: počet prechodov to_status = 'Reopened' v období
SELECT COUNT(*) FROM work_item_transitions
WHERE to_status = 'Reopened'
  AND timestamp BETWEEN :start AND :end

-- Reopen rate: reopened / closed
```

---

## 🚀 Implementačný plán

### Week 1: Data Layer

- [x] **Day 1-2**: Dátové schémy (WorkItem, Transition, SLA, MetricDaily)
- [ ] **Day 3-4**: Backfill fetcher (JQL pagination + changelog)
- [ ] **Day 5**: Webhook receiver → staging → normalized tables

### Week 2: Aggregations & UI

- [ ] **Day 1-2**: Denné agregácie do MetricDaily + cron job
- [ ] **Day 3-4**: Web UI (5 kariet + risks tabuľka + 4 sparklines)
- [ ] **Day 5**: Slack/Email digest (HTML + PDF render)

### Week 3: Polish & Deploy

- [ ] **Day 1-2**: Forge Glance (read-only)
- [ ] **Day 3**: Exporty (CSV/PDF) + multi-tenant kontúry
- [ ] **Day 4-5**: Observability (Prometheus metriky) + testing

---

## 🔧 Konfigurácia

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"

# Pulse Configuration
PULSE_STUCK_THRESHOLD_DAYS=3
PULSE_SLA_RISK_WINDOW_HOURS=24
PULSE_WIP_WARNING=50
PULSE_REOPEN_RATE_WARNING=10.0

# Digest
PULSE_DIGEST_ENABLED=true
PULSE_DIGEST_DAY=1  # Monday
PULSE_DIGEST_HOUR=8  # 8 AM
```

### Per-Tenant Configuration

```python
# Via API or database
pulse_config = PulseConfig(
    tenant_id="company-xyz",
    sla_risk_window_hours=24,
    stuck_threshold_days=3,
    wip_warning_threshold=50,
    reopen_rate_warning_pct=10.0,
    weekly_digest_enabled=True,
    digest_recipients=["ceo@company.com", "cto@company.com"],
    digest_slack_webhook="https://hooks.slack.com/...",
    digest_day_of_week=1,  # Monday
    digest_hour=8,  # 8 AM
)
```

---

## 📱 UI Mockup

```
┌─────────────────────────────────────────────────────────────┐
│  Executive Work Pulse                    [Export PDF] [⚙️]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Throughput│  │Lead Time │  │ SLA Risk │  │   WIP    │   │
│  │          │  │          │  │          │  │          │   │
│  │ 45 / 52  │  │ P50: 3d  │  │    12    │  │   127    │   │
│  │  ↑ +8%   │  │ P90: 7d  │  │  ⚠️ HIGH │  │  23 stuck│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  ┌──────────┐                                                │
│  │ Quality  │                                                │
│  │          │                                                │
│  │  8.2%    │                                                │
│  │  ↓ -2%   │                                                │
│  └──────────┘                                                │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  🚨 Top 10 Risks & Exceptions                                │
├─────────────────────────────────────────────────────────────┤
│  1. SCRUM-123  SLA breach in 2h    [View]                   │
│  2. SCRUM-456  Stuck 14 days       [View]                   │
│  3. SCRUM-789  Reopened 3x         [View]                   │
│  ...                                                          │
├─────────────────────────────────────────────────────────────┤
│  📈 4-Week Trends                                            │
├─────────────────────────────────────────────────────────────┤
│  Throughput:  ▁▂▃▅▆▇█▇  (sparkline)                         │
│  Lead Time:   ▇▆▅▄▃▂▁▂  (sparkline)                         │
│  WIP:         ▃▄▅▆▇▇▆▅  (sparkline)                         │
│  Reopen Rate: ▂▂▃▂▁▁▂▃  (sparkline)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Bezpečnosť

### Multi-Tenant Isolation

- Všetky tabuľky majú `tenant_id` column
- Row-Level Security (RLS) v PostgreSQL
- API endpointy vyžadujú `X-Tenant-Id` header

### Jira Credentials

- API tokeny šifrované v databáze (AES-256)
- Least-privilege scopes (read-only pre MVP)
- OAuth 3LO pre produkciu

### Audit Log

- Všetky prístupy k dashboardu logované
- Kto otvoril, kedy, ktoré projekty

---

## 📊 API Endpoints

### Dashboard Data

```bash
GET /v1/pulse?tenant=company-xyz&since=2025-09-01
```

Response:
```json
{
  "throughput": {
    "created": 52,
    "closed": 45,
    "delta_vs_4w_avg": 0.08
  },
  "leadTime": {
    "p50Days": 3.2,
    "p90Days": 7.1
  },
  "slaRisk": {
    "count": 12,
    "severity": "high"
  },
  "wip": {
    "total": 127,
    "noAssignee": 15,
    "stuck": 23
  },
  "quality": {
    "reopenRate": 0.082,
    "delta_vs_4w_avg": -0.02
  },
  "risks": [
    {
      "issueKey": "SCRUM-123",
      "reason": "SLA breach in 2h",
      "severity": "critical"
    }
  ],
  "trends": {
    "throughput": [45, 48, 51, 55, 58, 62, 67, 65],
    "leadTimeP50": [7.2, 6.8, 6.5, 6.0, 5.5, 4.8, 4.2, 3.2]
  }
}
```

### Project Detail

```bash
GET /v1/pulse/projects/SCRUM?tenant=company-xyz
```

### Send Digest

```bash
POST /v1/pulse/digest/send?tenant=company-xyz
```

---

## 🎯 Akceptačné kritériá MVP

- [x] Dashboard sa načíta < 2s na dataset do 50k ticketov
- [ ] Inkrem. update po webhooku viditeľný < 60s
- [ ] Čísla v dashboarde validované na 3 vybraných projektoch voči JQL výstupom (±1%)
- [ ] Týždenný digest odchádza v pondelok 8:00 lokálneho času tenantu

---

## 💰 Pricing (signál)

- **Starter (Free)** - 1 projekt, dashboard + weekly e-mail
- **Pro (199 €/tím/mes.)** - neobmedzené projekty, PDF exporty, Slack digest, multi-tenant
- **Enterprise** - vlastná DB, SSO, SLA, privátny deployment

---

## 🚀 Ďalšie kroky (Phase 2)

1. **GitHub Issues** mapper → WorkItem (source=github)
2. **Zendesk** mapper (typ=question/incident, SLA z ich polí)
3. **PagerDuty** mapper (incidenty → WorkItem type=incident)
4. **Mini-LLM** digest summary (80 slov, bez floskúl)
5. **Forge Glance** per project

---

## 📚 Dokumentácia

- [Dátový model](./PULSE_DATA_MODEL.md)
- [API Reference](./PULSE_API.md)
- [Deployment Guide](./PULSE_DEPLOYMENT.md)
- [Troubleshooting](./PULSE_TROUBLESHOOTING.md)

