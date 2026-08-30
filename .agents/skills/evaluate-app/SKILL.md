---
name: evaluate-app
description: Thoroughly evaluates the application architecture, UX, security, performance, and test integrity, and generates a prioritized improvement roadmap.
---

# App Evaluation & Improvement Roadmap Skill

This skill provides a systematic procedure for evaluating agentic web applications and microservices (specifically **Unified Ops AX** and similar multi-agent systems). It guides the agent to inspect source code, security boundaries, performance telemetry, test suites, and UI experience, generating an actionable, prioritized improvement report.

---

## Evaluation Workflow

When executing this skill, follow these 5 assessment phases:

### Phase 1: Architecture & Data Flow Audit
1. **Layer Separation**: Check that the application follows clean modular architecture (e.g. 5-Layer Monolith: L1 Connectors, L2 Orchestration, L3 Data Hub/RAG, L4 Intelligence/Agents, L5 Experience).
2. **Event Stream Integrity**: Verify that business state changes emit to a Single Source of Truth (`Activity` event store) via a transactional outbox pattern.
3. **Dual-Environment Resiliency**: Verify seamless fallback between local offline development (SQLite, keyless Ollama embeddings) and cloud production (Google Cloud SQL Postgres, Vertex AI Gemini).

### Phase 2: Security & Governance Audit
1. **Server-Derived Identity**: Verify that agent tools derive user role/principal on the server side—never accepting user/role arguments from prompt inputs.
2. **SQL-Level Security Trimming**: Confirm that security filters (Row-Level Security / RLS) are applied in SQL `WHERE` predicates *before* vector similarity ranking or data return.
3. **Human-in-the-Loop (HITL) Gates**: Confirm that high-risk actions (e.g. sending customer follow-ups) require human sign-off via HTTP endpoints, returning deterministic `HTTP 409 Conflict` if unapproved.
4. **Data Protection & PII Masking**: Verify HMAC-SHA256 PII masking at-rest (`enc:v1:...`) prior to DB storage.

### Phase 3: Performance & Telemetry Probe
1. **Queue Throughput**: Benchmark worker queue processing rate (target: $> 31 \text{ tasks/sec}$).
2. **Latency Percentiles**: Measure $P_{50}, P_{95}, P_{99}$ latencies rather than raw averages.
3. **OpenTelemetry & Prometheus Exposition**: Verify that `/metrics` text exposition and health preflight probes (`/ops/preflight`) return accurate telemetry.
4. **Autoscaling Mechanics**: Verify Kubernetes HPA scaling policies and resource limits under simulated/live traffic spikes.

### Phase 4: UX & Control Desk Review
1. **Clarity of Demo Boundaries**: Ensure badges clearly distinguish between `LIVE` cloud execution and `SIMULATED` sandboxes.
2. **Context & Role Explanations**: Verify that every tab/view includes a clear **Architecture Role** card and **Key Subsystem Breakdown** card so users understand system mechanics.
3. **Alert & Incident Response**: Ensure anomaly alerts (`COST_SPIKE`, `LATENCY_BURST`, `DLP_VIOLATION`) trigger clear toast notifications and circuit-breaker feedback.

### Phase 5: Verification & Test Suite Execution
1. Run the local verification command (e.g. `.venv\Scripts\python verify.py` or `pytest -v`).
2. Reconcile test claims across documentation (`README.md`, Devpost, codebase) to ensure exact count consistency.

---

## Output Template for Improvement Report

After completing the evaluation, generate a report using the following structure:

```markdown
# 🔬 Application Evaluation Report & Improvement Roadmap

## 📊 Executive Summary
[Brief overview of application health, strengths, and primary focus areas]

## 🛡️ Security & Governance Status
- [ ] Server-Derived Principal Roles: [VERIFIED / NEEDS FIX]
- [ ] SQL Security Trimming (RLS): [VERIFIED / NEEDS FIX]
- [ ] HITL HTTP 409 Enforcement: [VERIFIED / NEEDS FIX]
- [ ] HMAC-SHA256 PII Masking: [VERIFIED / NEEDS FIX]

## ⚡ Performance & Telemetry Summary
- Throughput: [X tasks/sec]
- Latency P95: [X ms]
- Verification Suite Pass Rate: [X/X PASS]

## 🚀 Prioritized Improvement Roadmap

### 🔴 P0: Critical Safety, Security & Bug Fixes
1. **[Issue Title]**: [Description, location, and recommended fix]

### 🟡 P1: Operational Stability & Performance Optimizations
1. **[Issue Title]**: [Description, location, and recommended fix]

### 🔵 P2: Feature Polish, UX & Observability Enhancements
1. **[Issue Title]**: [Description, location, and recommended fix]
```
