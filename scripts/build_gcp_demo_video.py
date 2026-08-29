"""Build MP4 Demo Video with Proof of Google Cloud Agent Platform Execution using FFmpeg."""
import os
import subprocess

ARTIFACT_DIR = r"C:\Users\secha\.gemini\antigravity-ide\brain\d4a31867-b534-4186-9222-9f0169725b19"
OUTPUT_VIDEO_ROOT = r"c:\Users\secha\.gemini\antigravity-ide\scratch\unified-ops-ax\unified-ops-ax\unified_ops_ax_demo_video.mp4"

img1 = os.path.join(ARTIFACT_DIR, "gcp_cloud_run_console_proof_1787970415715.jpg")
img2 = os.path.join(ARTIFACT_DIR, "gcp_agent_platform_console_proof_1787970923915.jpg")
img3 = os.path.join(ARTIFACT_DIR, "gcp_vertex_ai_logs_proof_1787970427727.jpg")
img4 = os.path.join(ARTIFACT_DIR, "streamlit_carto_fleet_control_center_proof_1787973016857.jpg")

print(f"Checking images:\n 1: {os.path.exists(img1)}\n 2: {os.path.exists(img2)}\n 3: {os.path.exists(img3)}\n 4: {os.path.exists(img4)}")

# Build a smooth 20-second MP4 video stitching 4 proof screenshots (5s each)
# Slide 1: Cloud Run Console Proof
# Slide 2: Agent Platform Console (project agentichackathon-506620)
# Slide 3: Vertex AI & Cloud Logging Traces
# Slide 4: Streamlit Live CARTO Fleet Control Center (unified-ops.streamlit.app)
concat_script = os.path.join(ARTIFACT_DIR, "video_inputs.txt")
with open(concat_script, "w", encoding="utf-8") as f:
    f.write(f"file '{img1}'\nduration 5\n")
    f.write(f"file '{img2}'\nduration 5\n")
    f.write(f"file '{img3}'\nduration 5\n")
    f.write(f"file '{img4}'\nduration 5\n")
    f.write(f"file '{img4}'\n")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_script,
    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
    "-c:v", "libx264",
    "-r", "30",
    "-preset", "fast",
    OUTPUT_VIDEO_ROOT
]

print("Running ffmpeg command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg returncode:", res.returncode)
if res.returncode == 0:
    print(f"Successfully generated demo video at: {OUTPUT_VIDEO_ROOT}")
    print(f"Video size: {os.path.getsize(OUTPUT_VIDEO_ROOT)} bytes")
else:
    print("FFmpeg stderr:", res.stderr)
