"""Streamlit wrapper for Unified Ops AX Live Control Center.
Deployed at: https://unified-ops.streamlit.app/
Connected to Google Cloud Run backend at: https://unified-ops-ax-506620-uc.a.run.app
Project ID: agentichackathon-506620"""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Unified Ops AX — Google Cloud Agentic Control Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Top Google Cloud Infrastructure Status Banner
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #1e293b, #0f172a); border: 1px solid #3b82f6; border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">☁️ Unified Ops AX — Google Cloud Agent Platform Backend (agentichackathon-506620)</span>
            <br>
            <span style="font-size: 0.85rem; color: #94a3b8;">
                Backend Service running on <strong>Google Cloud Run</strong> | Agent Platform: <strong>Vertex AI (Gemini 1.5/2.5 Flash)</strong>
            </span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
            <a href="https://console.cloud.google.com/agent-platform/overview?project=agentichackathon-506620" target="_blank" style="background: #10b981; color: #ffffff; text-decoration: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; font-size: 0.85rem;">
                🤖 Agent Platform Console
            </a>
            <a href="https://unified-ops-ax-506620-uc.a.run.app/ops/preflight" target="_blank" style="background: #2563eb; color: #ffffff; text-decoration: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; font-size: 0.85rem;">
                ⚡ Cloud Run Endpoint (.run.app)
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
components.html(html, height=1600, scrolling=True)
