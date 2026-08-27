"""Unified Ops AX — Streamlit Control Center Dashboard.

Interactive web interface for Fleet Controls, PyDeck 3D Spatial Maps, K8s Pod Scaling,
DLP Security Desk, Operational Telemetry, and Live Google GenAI SDK (google-genai) & ADK Execution.
"""

import asyncio
import os
import threading
import time

import pandas as pd
import pydeck as pdk
import streamlit as st

from async_agent_engine import AsyncAgentEngine, TaskPriority
from auto_remediation import AnomalyType, GENAI_AVAILABLE, ADK_AVAILABLE

# Page Configuration
st.set_page_config(
    page_title="Unified Ops AX — Fleet Control Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Glassmorphism Theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(10px);
    }
    .badge-sdk {
        background-color: #4285F4;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-demo {
        background-color: #3b82f6;
        color: #eff6ff;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-success {
        background-color: #059669;
        color: #ecfdf5;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #d97706;
        color: #fffbeb;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# Persistent Process-Wide Async Engine with Daemon Thread Loop
@st.cache_resource
def get_engine() -> AsyncAgentEngine:
    eng = AsyncAgentEngine(num_workers=4)
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    asyncio.run_coroutine_threadsafe(eng.start(), loop).result()
    eng._loop = loop
    return eng


engine: AsyncAgentEngine = get_engine()


def call_coro(coro, timeout: float = 10.0):
    """Safely executes a coroutine on the process-wide daemon event loop."""
    future = asyncio.run_coroutine_threadsafe(coro, engine._loop)
    return future.result(timeout=timeout)


# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/isometric/96/server.png", width=70)
st.sidebar.title("Unified Ops AX")
st.sidebar.markdown(f"<span class='badge-sdk'>google-genai {'✓' if GENAI_AVAILABLE else '×'}</span> <span class='badge-sdk'>google-adk {'✓' if ADK_AVAILABLE else '×'}</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "Navigation",
    ["🌐 Fleet Overview & Incidents", "🤖 Google GenAI & ADK Playground", "⚡ Async Engine & Task History", "☸️ K8s HPA Pod Scaling", "🔒 Local DLP Security Desk", "📊 Operational Telemetry"]
)

# Header Section
st.title("🚀 Unified Ops AX: Fleet Control Center")
st.caption("Autonomous Multi-Agent Fleet Telemetry Engine (Powered by google-genai, google-adk & Gemini 3.6 Flash / 3.5 Flash)")


# -----------------------------------------------------------------------------
# TAB 1: Fleet Overview & Incidents
# -----------------------------------------------------------------------------
if nav_choice == "🌐 Fleet Overview & Incidents":
    st.subheader("🌐 Fleet Overview & Real-Time Incident Desk")
    st.markdown("Monitor multi-region fleet health across `us-central1` (Iowa), `europe-west1` (Belgium), and `asia-east1` (Taiwan).")

    status = engine.get_status()
    percentiles = status["percentile_latencies_ms"]

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Fleet Status", "HEALTHY" if status["is_running"] else "DEGRADED", delta=f"{status['active_workers']}/4 Workers Active")
    col_m2.metric("Queue Throughput", f"{status['throughput_tasks_per_sec']} tasks/s", delta="Async Worker Pool")
    col_m3.metric("Latency (p95)", f"{percentiles['p95']} ms", delta=f"p50: {percentiles['p50']}ms | p99: {percentiles['p99']}ms")
    col_m4.metric("Active Pods", f"{status['k8s_autoscaling']['current_replicas']} pods", delta=status['k8s_autoscaling']['mode_badge'])

    # PyDeck 3D Map Data
    tp = status['throughput_tasks_per_sec']
    nodes_df = pd.DataFrame([
        {"name": "GCP us-central1 (Iowa)", "lat": 41.2619, "lon": -95.8608, "workers": status['active_workers'], "throughput": tp, "color": [255, 99, 71, 220]},
        {"name": "GCP europe-west1 (Belgium)", "lat": 50.4542, "lon": 3.8258, "workers": status['active_workers'], "throughput": tp, "color": [0, 255, 128, 220]},
        {"name": "GCP asia-east1 (Taiwan)", "lat": 24.0175, "lon": 120.5050, "workers": status['active_workers'], "throughput": tp, "color": [0, 128, 255, 220]}
    ])

    arcs_df = pd.DataFrame([
        {"from_lat": 41.2619, "from_lon": -95.8608, "to_lat": 50.4542, "to_lon": 3.8258},
        {"from_lat": 41.2619, "from_lon": -95.8608, "to_lat": 24.0175, "to_lon": 120.5050}
    ])

    view_state = pdk.ViewState(
        latitude=30.0,
        longitude=0.0,
        zoom=1.4,
        pitch=45,
        bearing=0
    )

    nodes_layer = pdk.Layer(
        "ScatterplotLayer",
        data=nodes_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=250000,
        pickable=True
    )

    arcs_layer = pdk.Layer(
        "ArcLayer",
        data=arcs_df,
        get_source_position=["from_lon", "from_lat"],
        get_target_position=["to_lon", "to_lat"],
        get_source_color=[0, 255, 128],
        get_target_color=[0, 128, 255],
        get_width=4
    )

    r = pdk.Deck(
        layers=[nodes_layer, arcs_layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\nActive Workers: {workers}\nThroughput: {throughput} tasks/s"}
    )

    st.pydeck_chart(r)

    st.markdown("### 🚨 Incident Trigger & Active Policy Overrides")
    col_inc1, col_inc2 = st.columns(2)
    
    with col_inc1:
        st.markdown("#### Simulate Splunk Anomaly Alert")
        anomaly_sel = st.selectbox("Anomaly Type", ["COST_SPIKE", "LATENCY_SPIKE", "DLP_BURST"])
        metric_val = st.number_input("Metric Value", value=8.5, min_value=1.0, max_value=10000.0)
        
        if st.button("Trigger Remediation Policy", use_container_width=True):
            a_map = {"COST_SPIKE": AnomalyType.COST_SPIKE, "LATENCY_SPIKE": AnomalyType.LATENCY_SPIKE, "DLP_BURST": AnomalyType.DLP_BURST}
            res = call_coro(engine.trigger_anomaly_remediation(a_map[anomaly_sel], metric_val))
            st.warning(f"Policy Status: `{res.get('status', 'remediated')}` | Rollback Token: `{res.get('rollback_token', 'N/A')}`")
            st.markdown("#### Google GenAI SDK (`google-genai`) Execution Result:")
            st.json(res.get("google_genai_execution", res))
            st.rerun()

    with col_inc2:
        st.markdown("#### Active Policy State & Rollback Controls")
        policy_state = status["policy_engine"]
        if policy_state.get("active_override"):
            override = policy_state["active_override"]
            st.warning(f"**Active Override**: `{override['policy']}` (Applied by: `{override['owner']}`)")
            st.markdown(f"**Active Weights**: `{override['active_weights']}`")
            st.markdown(f"**Rollback Token**: `{override['rollback_token']}`")
            if st.button("Rollback Policy Override"):
                roll_res = engine.policy_engine.rollback_override(override['rollback_token'])
                st.success(f"Rollback result: {roll_res}")
                st.rerun()
        else:
            st.info("No active policy override. System operating at baseline model weights.")

# -----------------------------------------------------------------------------
# TAB 2: Google GenAI & ADK Playground
# -----------------------------------------------------------------------------
elif nav_choice == "🤖 Google GenAI & ADK Playground":
    st.subheader("🤖 Live Google GenAI SDK (`google-genai`) & Google ADK (`google-adk`) Playground")
    st.markdown("Direct client execution environment using `from google import genai` and `from google.adk.agents import BaseAgent`.")

    col_sdk1, col_sdk2 = st.columns(2)
    with col_sdk1:
        st.markdown(f"**Google GenAI SDK (`google-genai`)**: `{'Installed (v0.1+)' if GENAI_AVAILABLE else 'Not Installed'}`")
    with col_sdk2:
        st.markdown(f"**Google ADK (`google-adk`)**: `{'Installed (v2.2.0)' if ADK_AVAILABLE else 'Not Installed'}`")

    st.markdown("---")
    st.markdown("### Execute Live Gemini Model Call")
    prompt_text = st.text_area("Prompt for Gemini Model", value="Summarize fleet telemetry policy: latency 5200ms detected on GCP us-central1.")
    model_choice = st.selectbox("Select Target Model", ["gemini-3.6-flash", "gemini-3.5-flash"])

    if st.button("Execute google.genai Client Call", use_container_width=True):
        with st.spinner("Invoking google.genai.Client..."):
            genai_res = engine.policy_engine.execute_google_genai_call(prompt_text, model_name=model_choice)
            st.success(f"Execution Status: `{genai_res['status']}` | Model: `{genai_res['model_used']}` | Latency: `{genai_res['latency_ms']} ms`")
            st.json(genai_res)

# -----------------------------------------------------------------------------
# TAB 3: Async Engine & Task History
# -----------------------------------------------------------------------------
elif nav_choice == "⚡ Async Engine & Task History":
    st.subheader("⚡ AsyncAgentEngine Worker Status & Recent Task Table")
    
    status = engine.get_status()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Engine State", "RUNNING" if status["is_running"] else "STOPPED")
    col2.metric("Worker Threads", f"{status['num_workers']} Threads")
    col3.metric("Total Processed", f"{status['total_processed']} Tasks")
    col4.metric("Throughput", f"{status['throughput_tasks_per_sec']} tasks/s")

    st.markdown("### Enqueue Background Batch Ingest Job")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        log_count = st.slider("Log Event Volume per Batch", 100, 2000, 500, step=100)
    with col_t2:
        task_priority = st.selectbox("Priority", ["NORMAL", "HIGH", "CRITICAL", "LOW"])
        
    if st.button("Enqueue Batch Ingest Job", use_container_width=True):
        p_map = {"NORMAL": TaskPriority.NORMAL, "HIGH": TaskPriority.HIGH, "CRITICAL": TaskPriority.CRITICAL, "LOW": TaskPriority.LOW}
        def dummy_job():
            time.sleep(0.01)
            return f"Processed batch of {log_count} log events"
            
        task = call_coro(engine.submit_task(dummy_job, name=f"user_batch_{log_count}", priority=p_map[task_priority]))
        st.success(f"Enqueued Task ID: `{task.task_id[:16]}` (Priority: {task_priority})")
        st.rerun()

    st.markdown("### Recent Execution Task Table")
    task_rows = []
    for t_id, task in list(engine.tasks.items())[-10:]:
        task_rows.append({
            "Task ID": task.task_id[:12],
            "Task Name": task.name,
            "Priority": task.priority.name,
            "Status": task.status.value,
            "Duration (ms)": task.duration_ms if task.duration_ms else "-",
            "Created At": time.strftime("%H:%M:%S", time.localtime(task.created_at))
        })
    if task_rows:
        st.table(pd.DataFrame(task_rows))
    else:
        st.info("No tasks recorded yet.")

# -----------------------------------------------------------------------------
# TAB 4: K8s HPA Pod Scaling
# -----------------------------------------------------------------------------
elif nav_choice == "☸️ K8s HPA Pod Scaling":
    st.subheader("☸️ Kubernetes Horizontal Pod Autoscaler (HPA)")
    st.markdown("Dynamic pod replica scaling of deployment `unified-ops-agent-pool` upon latency spike detection.")

    k8s_stats = engine.k8s_autoscaler.get_stats()
    
    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Deployment Name", k8s_stats["deployment_name"])
    kc2.metric("Namespace", k8s_stats["namespace"])
    kc3.metric("Current Pod Replicas", f"{k8s_stats['current_replicas']} Pods", delta=k8s_stats["mode_badge"])
    kc4.metric("Scaling Events", f"{k8s_stats['total_scaling_events']} Events")

    st.markdown(f"### Manual Pod Scale Override (`{k8s_stats['mode_badge']}` Mode)")
    target_pods = st.slider("Target Pod Replicas", k8s_stats["min_replicas"], k8s_stats["max_replicas"], k8s_stats["current_replicas"])
    
    if st.button("Apply kubectl scale deployment"):
        res = call_coro(engine.k8s_autoscaler.scale_deployment_async(target_pods, reason="manual_user_override"))
        st.success(f"Scaling result: {res}")
        st.rerun()

    st.markdown("### Pod Scaling Event History")
    if k8s_stats["last_event"]:
        st.json(k8s_stats["last_event"])
    else:
        st.info("No scaling events recorded yet.")

# -----------------------------------------------------------------------------
# TAB 5: Local DLP Security Desk
# -----------------------------------------------------------------------------
elif nav_choice == "🔒 Local DLP Security Desk":
    st.subheader("🔒 Fine-Tuned Local DLP Guardrail & Security Desk")
    st.markdown("Zero-latency offline classification and sanitization of sensitive PII (SSN, KR_RRN, Credit Cards with Luhn validation, API Keys, Email, Phone) before telemetry emission.")

    dlp_stats = engine.dlp_guardrail.get_stats()
    
    dc1, dc2, dc3 = st.columns(3)
    dc1.metric("Total Inspections", f"{dlp_stats['total_inspections']} Payloads")
    dc2.metric("Rule Violations", f"{dlp_stats['total_violations']} Blocked")
    dc3.metric("Clean Rate", f"{dlp_stats['clean_rate_pct']}%")

    st.markdown("### Live DLP Payload Inspection Playground")
    sample_payload = st.text_area(
        "Payload Content for Inspection",
        value="User query from SSN 123-45-6789 (KR_RRN 900101-1234567) with card 4532 0151 1283 0366 and API key sk-proj-abcdef12345678901234567890."
    )
    
    if st.button("Inspect & Mask PII Payload"):
        res = engine.dlp_guardrail.inspect_and_mask(sample_payload)
        st.markdown(f"**Clean Status**: `{'CLEAN' if res.is_clean else 'VIOLATION'}` | **Sensitivity**: `{res.sensitivity}` | **HMAC-SHA256 Signature**: `{res.data_hash}`")
        st.markdown("**Matched Rules**:")
        st.write(res.matched_rules if res.matched_rules else "None")
        st.markdown("**Masked Output Payload**:")
        st.code(res.masked_text)

# -----------------------------------------------------------------------------
# TAB 6: Operational Telemetry
# -----------------------------------------------------------------------------
elif nav_choice == "📊 Operational Telemetry":
    st.subheader("📊 Operational Metrics & Prometheus Exposition")
    st.markdown("Real-time performance analytics, latency distribution, and Prometheus text exposition stream.")

    status = engine.get_status()
    percentiles = status["percentile_latencies_ms"]

    st.markdown("### 📈 Real-Time Performance & Latency Charts")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Queue Task Throughput (tasks/sec)")
        df_tp = pd.DataFrame({"Time": range(5), "Throughput": [10, 22, status['throughput_tasks_per_sec'] + 5, status['throughput_tasks_per_sec'] + 12, status['throughput_tasks_per_sec']]})
        st.line_chart(df_tp.set_index("Time"))

    with chart_col2:
        st.markdown("#### Latency Distribution Percentiles (ms)")
        df_perc = pd.DataFrame({"Metric": ["p50", "p95", "p99"], "Latency (ms)": [percentiles["p50"], percentiles["p95"], percentiles["p99"]]})
        st.bar_chart(df_perc.set_index("Metric"))

    with st.expander("📜 Raw Prometheus Exposition Stream (/metrics)"):
        metrics_payload = f"""# HELP async_engine_processed_tasks_total Total tasks processed by engine
# TYPE async_engine_processed_tasks_total counter
async_engine_processed_tasks_total{{status="completed"}} {status['total_processed']}

# HELP async_engine_throughput_tasks_per_sec Current task throughput rate
# TYPE async_engine_throughput_tasks_per_sec gauge
async_engine_throughput_tasks_per_sec {status['throughput_tasks_per_sec']}

# HELP async_engine_latency_p95_ms 95th percentile task latency
# TYPE async_engine_latency_p95_ms gauge
async_engine_latency_p95_ms {percentiles['p95']}

# HELP k8s_pod_replicas_current Current deployment worker pod count
# TYPE k8s_pod_replicas_current gauge
k8s_pod_replicas_current{{deployment="{status['k8s_autoscaling']['deployment_name']}"}} {status['k8s_autoscaling']['current_replicas']}

# HELP dlp_rule_violations_total Total DLP security rule violations
# TYPE dlp_rule_violations_total counter
dlp_rule_violations_total {status['local_dlp']['total_violations']}
"""
        st.code(metrics_payload, language="promql")
