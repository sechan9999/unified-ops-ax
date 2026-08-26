# Unified Ops AX — Technical Recommendations & Architectural Roadmap

> **Comprehensive Architectural Review, Priority Matrix, 90-Second Demo Script, and Production Implementation Plan**  
> **Repository**: [https://github.com/sechan9999/unified-ops-ax](https://github.com/sechan9999/unified-ops-ax)  
> **Hosted App**: [https://unified-ops.streamlit.app/](https://unified-ops.streamlit.app/)  

---

## 📋 Priority Recommendation Matrix

| Priority | Recommendation | Benefit | Suggested Evidence / Implementation | Status |
|---|---|---|---|---|
| **P0** | **Authentication, RBAC & Scoped Permissions** | Prevents unauthorized operational mutations. | Shared secret auth (`X-MCP-Token`), role scopes (`operator`, `security`, `read_only`). | ✅ Implemented |
| **P0** | **Webhook Security, Idempotency & Replay Protection** | Prevents duplicate alert executions and replay attacks. | Timestamp window validation (<300s), duplicate `alert_id` hash deduplication, structured audit log. | ✅ Implemented |
| **P0** | **Durable Policy State Machine & Atomic Precedence** | Replaces transient daemon dicts with atomic precedence (`DLP` > `Latency` > `Cost`). | Baseline weight backups, active override expiry, rollback token generation (`DurablePolicyEngine`). | ✅ Implemented |
| **P0** | **Explicit DEMO / LIVE Mode Badges** | Aligns claims with actual runtime capability. | `LIVE K8s` vs `SIMULATED HPA` status badges based on `shutil.which("kubectl")`. | ✅ Implemented |
| **P1** | **Shared Service Layer & Canonical Entry Point** | Eliminates drift between Streamlit, FastAPI, and CLI. | Shared `AsyncAgentEngine` & `DurablePolicyEngine` single source of truth across entry points. | ✅ Implemented |
| **P1** | **Percentile Latency Metrics (p50, p95, p99)** | Replaces single timings with true latency distribution statistics. | Percentile calculations (`_calc_percentile`) exported to Prometheus exposition `/metrics`. | ✅ Implemented |
| **P1** | **Recent Task History Table with Execution Details** | Provides visibility into queue execution details. | Streamlit Task Table displaying Task ID, Priority, Status, Duration (ms), and Input Size. | ✅ Implemented |
| **P1** | **Automated Contract & Integration Test Suite** | Protects integration boundaries across subsystems. | 29 automated pytest test cases (`pytest tests/ -v`). | ✅ Implemented (29/29 Pass) |

---

## 🎙️ 90-Second Operational Demo Script

1. **0:00 - 0:15 | Overview & Baseline**:
   - Start on **`🌐 Fleet Overview & Incidents`** (`https://unified-ops.streamlit.app/`).
   - Highlight the **`DEMO MODE`** badge and baseline model routing weights (`quality: 0.5`, `cost: 0.3`, `latency: 0.2`).
2. **0:15 - 0:45 | Incident Trigger & Precedence Matrix**:
   - Trigger a **`COST_SPIKE`** ($8.50 > $5.00). Point out the active policy override, fallback to **Gemini 3.5 Flash**, and generated **Rollback Token**.
   - Trigger a **`DLP_BURST`** alert. Show atomic precedence overriding the cost policy due to higher security priority (`CRITICAL` > `NORMAL`).
3. **0:45 - 1:15 | Action Execution & Rollback**:
   - Demonstrate policy rollback using the rollback token, restoring baseline model weights instantly.
   - Switch to **`☸️ K8s HPA Pod Scaling`** and execute pod scale-out (2 -> 8 pods). Point out the transparent **`SIMULATED HPA`** / **`LIVE K8s`** badge.
4. **1:15 - 1:30 | Security DLP & HMAC Signatures**:
   - Switch to **`🔒 Local DLP Security Desk`**. Submit a PII payload (SSN, KR_RRN, Credit Card with Luhn validation). Show zero-latency redaction and **HMAC-SHA256 data hash**.

---

## 🗓️ Recommended Implementation Order

### Week 1: Credibility, Focus & UX Re-organization
- Re-organize Streamlit tabs with **`🌐 Fleet Overview & Incidents`** as primary entry point.
- Add transparent **`DEMO MODE`** and **`SIMULATED` / `LIVE`** badging across all panels.
- Reconcile test suite claims across README and Devpost story (**29 passed pytest cases**).

### Weeks 2–3: Operational UX & Policy Semantics
- Implement **`DurablePolicyEngine`** with atomic precedence ordering (`DLP_BURST` > `LATENCY_SPIKE` > `COST_SPIKE`).
- Add timestamp replay protection (<300s) and duplicate `alert_id` hash deduplication.
- Implement rollback tokens for explicit policy override cancellation.

### Weeks 4–5: Production Foundations & Observability
- Export percentile latency metrics (`p50`, `p95`, `p99`) to Prometheus `/metrics` exposition endpoints.
- Build recent execution task history table displaying status, priority, duration, and worker thread ID.

### Weeks 6–8: Integration Proof & Scale
- Connect live GCP Cloud Pub/Sub, GCP Eventarc, and Apache Kafka topics.
- Run continuous benchmark stress tests verifying > 28 tasks/sec throughput under high concurrency.
