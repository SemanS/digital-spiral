# Spec-Driven Development for Digital Spiral

This directory contains all specifications, plans, and tasks for features developed using the **Spec-Driven Development** methodology based on [GitHub Spec-Kit](https://github.com/github/spec-kit).

---

## 📁 Directory Structure

```
.specify/
├── features/                       # Feature specifications
│   ├── 001-architecture-refactoring/
│   ├── 002-admin-ui/
│   ├── 003-mcp-sql-enhancement/
│   └── 004-llm-sql-analytics/      # Current feature
│       ├── constitution.md         # Project principles
│       ├── spec.md                 # Requirements & user stories
│       ├── plan.md                 # Implementation plan
│       ├── tasks.md                # Task breakdown
│       ├── AUGGIE_GUIDE.md         # Auggie implementation guide
│       └── README.md               # Feature overview
├── memory/
│   └── constitution.md             # Global project constitution
├── scripts/
│   └── bash/                       # Automation scripts
│       ├── common.sh
│       ├── create-new-feature.sh
│       ├── setup-plan.sh
│       ├── implement.sh            # Implementation orchestrator
│       └── update-agent-context.sh
├── templates/                      # Document templates
│   ├── agent-file-template.md
│   ├── plan-template.md
│   ├── spec-template.md
│   └── tasks-template.md
└── README.md                       # This file
```

---

## 🚀 Quick Start

### For Auggie (AI Assistant)

```bash
# Read the main guide
cat AUGGIE.md

# Read feature documentation
cat .specify/features/004-llm-sql-analytics/constitution.md
cat .specify/features/004-llm-sql-analytics/spec.md
cat .specify/features/004-llm-sql-analytics/plan.md
cat .specify/features/004-llm-sql-analytics/tasks.md

# Implement feature
/implement
```

### For Developers

```bash
# 1. Create new feature
.specify/scripts/bash/create-new-feature.sh "Feature Name"

# 2. Write constitution (principles)
# Edit: .specify/features/00X-feature-name/constitution.md

# 3. Write specification (requirements)
# Edit: .specify/features/00X-feature-name/spec.md

# 4. Create implementation plan
# Edit: .specify/features/00X-feature-name/plan.md

# 5. Break down into tasks
# Edit: .specify/features/00X-feature-name/tasks.md

# 6. Implement with Auggie
/implement
```

---

## 📋 Slash Commands

### Available Commands

| Command | Description |
|---------|-------------|
| `/constitution` | Create or update project principles |
| `/specify` | Define requirements and user stories |
| `/clarify` | Clarify underspecified areas |
| `/plan` | Create technical implementation plan |
| `/tasks` | Generate task breakdown |
| `/analyze` | Validate consistency |
| `/implement` | Execute implementation |

### Workflow

1. **`/constitution`** - Establish project principles
2. **`/specify`** - Define what you want to build
3. **`/clarify`** - Clarify underspecified areas (required before `/plan`)
4. **`/plan`** - Create technical implementation plan
5. **`/tasks`** - Generate actionable task list
6. **`/analyze`** - Validate consistency (optional, recommended)
7. **`/implement`** - Execute all tasks

---

## 📚 Methodology

### Spec-Driven Development

Spec-Driven Development flips the script on traditional software development. Specifications become **executable**, directly generating working implementations rather than just guiding them.

**Key Principles**:
- **Intent-driven development** - Define "what" before "how"
- **Rich specification creation** - Use guardrails and organizational principles
- **Multi-step refinement** - Not one-shot code generation
- **AI-powered interpretation** - Heavy reliance on advanced AI models

### Document Types

#### 1. Constitution (`constitution.md`)
**Purpose**: Define project principles and development guidelines

**Contents**:
- Architecture philosophy
- Technology stack
- Code quality standards
- Security requirements
- Performance requirements
- Non-negotiables

**Example**:
```markdown
# Constitution: LLM + SQL Analytics System

## Architecture Philosophy
1. **Deterministic over Flexible** - Whitelisted metrics, no raw SQL from LLM
2. **Security First** - RLS, parameterized queries, rate limiting
3. **Multi-tenant Native** - Tenant isolation at all layers
```

#### 2. Specification (`spec.md`)
**Purpose**: Define requirements and user stories

**Contents**:
- User stories (10+)
- Functional requirements
- Technical requirements
- API endpoints
- Success metrics

**Example**:
```markdown
# Specification: LLM + SQL Analytics System

## User Stories

### US1: Natural Language Querying
**As a** product manager  
**I want to** query analytics using natural language  
**So that** I can get insights without writing SQL
```

#### 3. Plan (`plan.md`)
**Purpose**: Create technical implementation plan

**Contents**:
- Implementation phases (6+)
- Database schema
- File structure
- Testing strategy
- Deployment plan

**Example**:
```markdown
# Implementation Plan: LLM + SQL Analytics System

## Phase 1: Foundation (Week 1-2)
- Database schema & models
- Metrics catalog (25+ metrics)
- Materialized views
```

#### 4. Tasks (`tasks.md`)
**Purpose**: Break down plan into actionable tasks

**Contents**:
- Task breakdown (30+ tasks)
- Acceptance criteria
- Dependencies
- Estimated effort
- Priority

**Example**:
```markdown
# Tasks: LLM + SQL Analytics System

## Phase 1: Foundation (Week 1-2)

### Task 1.1: Create Migration for Analytics Tables
**Effort**: 4 hours  
**Dependencies**: None  
**Priority**: P0 (Blocker)

**Acceptance Criteria**:
- [ ] Migration file created
- [ ] All 5 tables created
- [ ] Foreign keys added
```

---

## 🎯 Current Feature: 004-llm-sql-analytics

### Overview
**LLM + SQL Analytics System** - AI-powered analytics platform that combines Large Language Models with SQL querying capabilities for Jira data analysis.

### Status
🚧 **In Progress** - Phase 1: Foundation

### Quick Links
- [Constitution](.specify/features/004-llm-sql-analytics/constitution.md)
- [Specification](.specify/features/004-llm-sql-analytics/spec.md)
- [Plan](.specify/features/004-llm-sql-analytics/plan.md)
- [Tasks](.specify/features/004-llm-sql-analytics/tasks.md)
- [Auggie Guide](.specify/features/004-llm-sql-analytics/AUGGIE_GUIDE.md)

### Implementation Timeline
- **Week 1-2**: Foundation (Database, Models, Metrics Catalog)
- **Week 3-4**: Query Builder (AnalyticsSpec DSL, Query Executor)
- **Week 5-6**: LLM Integration (NL → Spec, Semantic Search)
- **Week 7-8**: Job Orchestration (Celery, Job Manager)
- **Week 9-10**: Analytics API (Endpoints, Charts, Export)
- **Week 11-12**: Frontend (Chat Interface, Results Viewer)

---

## 🧪 Testing

### Test Coverage Requirements
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All critical paths
- **Contract Tests**: All metrics catalog
- **E2E Tests**: All user stories

### Running Tests
```bash
# Unit tests
pytest tests/unit/ -v --cov=src/

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v

# E2E tests
pytest tests/e2e/ -v

# All tests
pytest tests/ -v --cov=src/ --cov-report=html
```

---

## 📖 Resources

### Documentation
- [GitHub Spec-Kit](https://github.com/github/spec-kit) - Official methodology
- [AUGGIE.md](../AUGGIE.md) - Auggie development guidelines
- [Spec-Driven Development Guide](https://github.com/github/spec-kit/blob/main/spec-driven.md)

### Examples
- [Feature 001: Architecture Refactoring](features/001-architecture-refactoring/)
- [Feature 002: Admin UI](features/002-admin-ui/)
- [Feature 003: MCP SQL Enhancement](features/003-mcp-sql-enhancement/)
- [Feature 004: LLM + SQL Analytics](features/004-llm-sql-analytics/)

---

## 🤝 Contributing

### Adding a New Feature

1. **Create feature branch**:
   ```bash
   git checkout -b 005-feature-name
   ```

2. **Create feature directory**:
   ```bash
   .specify/scripts/bash/create-new-feature.sh "Feature Name"
   ```

3. **Write documents** (in order):
   - `constitution.md` - Project principles
   - `spec.md` - Requirements & user stories
   - `plan.md` - Implementation plan
   - `tasks.md` - Task breakdown

4. **Implement with Auggie**:
   ```bash
   /implement
   ```

5. **Create PR**:
   ```bash
   gh pr create --title "Feature 005: Feature Name" --body "$(cat .specify/features/005-feature-name/README.md)"
   ```

---

## 📞 Support

- **Documentation**: `.specify/features/`
- **GitHub Issues**: https://github.com/SemanS/digital-spiral/issues
- **Email**: slavomir.seman@hotovo.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Methodology**: [GitHub Spec-Kit](https://github.com/github/spec-kit)

