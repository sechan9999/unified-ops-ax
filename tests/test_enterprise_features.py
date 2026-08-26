"""Test suite for K8s HPA Autoscaler, Local DLP Guardrail, PyDeck Spatial Mapper, and Grafana Metrics.
"""

import asyncio
import threading
import time
import pytest
from async_agent_engine import AsyncAgentEngine, TaskPriority
from auto_remediation import AnomalyType, DurablePolicyEngine, PolicyPriority
from k8s_hpa_autoscaler import K8sHPAAutoscaler
from local_dlp_guardrail import LocalDLPGuardrail
from extended_enterprise_dashboard import PyDeckFleetMapper, GrafanaMetricsExporter


def test_durable_policy_precedence_and_rollback():
    """Test atomic policy overrides, precedence ordering (DLP > Cost), idempotency, and rollback tokens."""
    engine = DurablePolicyEngine()

    # 1. Apply Normal Priority policy (COST_SPIKE)
    res_cost = engine.apply_remediation(AnomalyType.COST_SPIKE, 8.5, alert_id="alert_cost_101", timestamp=time.time())
    assert res_cost["success"] is True
    assert res_cost["status"] == "policy_applied"
    assert res_cost["priority"] == "NORMAL"
    rollback_token = res_cost["rollback_token"]

    # 2. Attempt duplicate alert_id -> Should be rejected by Idempotency check
    res_dup = engine.apply_remediation(AnomalyType.COST_SPIKE, 8.5, alert_id="alert_cost_101", timestamp=time.time())
    assert res_dup["success"] is False
    assert res_dup["status"] == "rejected"
    assert "Idempotency rejected" in res_dup["reason"]

    # 3. Apply Higher Priority policy (DLP_BURST) -> Should override COST_SPIKE
    res_dlp = engine.apply_remediation(AnomalyType.DLP_BURST, 15.0, alert_id="alert_dlp_102", timestamp=time.time())
    assert res_dlp["success"] is True
    assert res_dlp["priority"] == "CRITICAL"

    # 4. Attempt Lower Priority policy while Critical policy is active -> Should be blocked by Precedence check
    res_cost_blocked = engine.apply_remediation(AnomalyType.COST_SPIKE, 9.0, alert_id="alert_cost_103", timestamp=time.time())
    assert res_cost_blocked["success"] is False
    assert res_cost_blocked["status"] == "precedence_blocked"

    # 5. Rollback active policy using rollback token
    res_rollback = engine.rollback_override(res_dlp["rollback_token"])
    assert res_rollback["success"] is True
    assert res_rollback["status"] == "rolled_back"


def test_percentile_latency_calculation():
    """Test p50, p95, and p99 latency percentile calculations in AsyncAgentEngine."""
    eng = AsyncAgentEngine(num_workers=2)
    eng.latencies_ms = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0, 200.0, 300.0, 400.0, 500.0]
    
    status = eng.get_status()
    percentiles = status["percentile_latencies_ms"]
    
    assert percentiles["p50"] > 0.0
    assert percentiles["p95"] >= percentiles["p50"]
    assert percentiles["p99"] >= percentiles["p95"]


def test_k8s_hpa_autoscaler():
    """Test Kubernetes deployment replica scaling and latency triggers."""
    scaler = K8sHPAAutoscaler(min_replicas=2, max_replicas=10)
    assert scaler.current_replicas == 2

    # Scale out on latency spike
    res = scaler.trigger_latency_scaleout(6200.0)
    assert res["scaled"] is True
    assert res["new_replicas"] == 8

    stats = scaler.get_stats()
    assert stats["current_replicas"] == 8
    assert stats["total_scaling_events"] == 1


def test_local_dlp_guardrail_masking():
    """Test local offline PII masking and sensitivity classification."""
    dlp = LocalDLPGuardrail()
    
    clean_res = dlp.inspect_and_mask("System operational log payload")
    assert clean_res.is_clean is True
    assert clean_res.sensitivity == "PUBLIC"

    pii_text = "User SSN 123-45-6789 and Card 4532-0151-1283-0366 email dev@google.com key sk-proj-1234567890123456789020"
    masked_res = dlp.inspect_and_mask(pii_text)
    
    assert masked_res.is_clean is False
    assert "SSN" in masked_res.matched_rules
    assert "CREDIT_CARD" in masked_res.matched_rules
    assert "EMAIL" in masked_res.matched_rules
    assert "API_KEY" in masked_res.matched_rules
    assert "[PII_MASKED:SSN]" in masked_res.masked_text
    assert "[PII_MASKED:CREDIT_CARD]" in masked_res.masked_text
    assert masked_res.sensitivity == "RESTRICTED"
    assert len(masked_res.data_hash) == 16


def test_dlp_luhn_and_kr_rrn():
    """Test Luhn algorithm card validation and Korean RRN classification."""
    dlp = LocalDLPGuardrail()

    # Korean RRN (900101-1234567) should be masked under KR_RRN
    rrn_text = "Customer ID 900101-1234567"
    res_rrn = dlp.inspect_and_mask(rrn_text)
    assert "KR_RRN" in res_rrn.matched_rules
    assert "[PII_MASKED:KR_RRN]" in res_rrn.masked_text


def test_pydeck_spatial_mapper():
    """Test PyDeck 3D spatial map JSON configuration generation."""
    mapper = PyDeckFleetMapper()
    config = mapper.generate_spatial_deck_config({"active_workers": 4, "throughput_tasks_per_sec": 38.5})
    
    assert "initialViewState" in config
    assert len(config["layers"]) == 2


def test_grafana_metrics_exporter():
    """Test Prometheus / Grafana text format metric exposition."""
    exporter = GrafanaMetricsExporter()
    prom_text = exporter.format_prometheus_metrics(
        engine_stats={"total_tasks": 15, "throughput_tasks_per_sec": 38.7, "total_remediations": 4},
        k8s_stats={"current_replicas": 8},
        dlp_stats={"total_violations": 2}
    )
    
    assert "unified_ops_tasks_total 15" in prom_text
    assert "unified_ops_k8s_replicas 8" in prom_text
    assert "unified_ops_dlp_violations_total 2" in prom_text


def test_streamlit_persistent_engine_lifecycle():
    """Test process-wide background event loop thread engine lifecycle."""
    eng = AsyncAgentEngine(num_workers=4)
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=loop.run_forever, daemon=True)
    t.start()
    
    asyncio.run_coroutine_threadsafe(eng.start(), loop).result(timeout=5)
    eng._loop = loop

    def dummy_work():
        time.sleep(0.01)
        return "done"

    future = asyncio.run_coroutine_threadsafe(eng.submit_task(dummy_work, name="test_job", priority=TaskPriority.HIGH), loop)
    task = future.result(timeout=5)

    time.sleep(0.1)

    status = eng.get_status()
    assert status["is_running"] is True
    assert status["active_workers"] > 0
    assert status["total_processed"] > 0

    asyncio.run_coroutine_threadsafe(eng.stop(), loop).result(timeout=5)
    loop.call_soon_threadsafe(loop.stop)
    t.join(timeout=2)


@pytest.mark.asyncio
async def test_engine_k8s_and_dlp_integration():
    """Test AsyncAgentEngine automatically triggering K8s autoscaling and local DLP stats."""
    engine = AsyncAgentEngine(num_workers=2)
    await engine.start()

    res = await engine.trigger_anomaly_remediation(AnomalyType.LATENCY_SPIKE, 6500.0)
    assert "k8s_autoscaling" in res
    assert res["k8s_autoscaling"]["new_replicas"] == 8

    dlp_res = engine.dlp_guardrail.inspect_and_mask("Confidential API Key sk-proj-1234567890123456789020")
    assert dlp_res.is_clean is False

    status = engine.get_status()
    assert status["k8s_autoscaling"]["current_replicas"] == 8
    assert status["local_dlp"]["total_violations"] == 1

    await engine.stop()
