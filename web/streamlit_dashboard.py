"""
Streamlit entrypoint wrapper for Unified Ops AX Live Control Center.
Deployed at: https://unified-ops.streamlit.app/
Connected to Google Cloud Run backend at: https://unified-ops-ax-652787573242.us-central1.run.app
Project ID: agentichackathon-506620
"""
from pathlib import Path
import sys

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import main app logic
import app  # noqa: F401
