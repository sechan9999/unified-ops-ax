"""Build MP4 Demo Video with Authentic Proof of Google Cloud Run Execution using FFmpeg."""
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")
OUTPUT_VIDEO_ROOT = os.path.join(REPO_ROOT, "unified_ops_ax_demo_video.mp4")

# Real Google Cloud Console & Telemetry Screenshots
img1 = os.path.join(ASSETS_DIR, "real_gcp_cloud_run_console.png")
img2 = os.path.join(ASSETS_DIR, "gcp_cloud_run_dashboard.png")
img3 = os.path.join(ASSETS_DIR, "streamlit_dashboard.png")

print(f"Checking images:\n 1 (Real Cloud Run Console): {os.path.exists(img1)}\n 2 (Multi-Region Fleet Map): {os.path.exists(img2)}\n 3 (3D PyDeck Control Desk): {os.path.exists(img3)}")

# Build a smooth 15-second MP4 video stitching 3 authentic proof screenshots (5s each)
# Slide 1: Real Google Cloud Console Cloud Run Dashboard (service unified-ops-ax on us-central1)
# Slide 2: Real Multi-Region Fleet Map with Agent Platform & Cloud Run Endpoint badges
# Slide 3: Real Streamlit Fleet Control Desk (PyDeck 3D map, metrics, and pod scaling controls)
p1 = img1.replace("\\", "/")
p2 = img2.replace("\\", "/")
p3 = img3.replace("\\", "/")
concat_script = os.path.join(ASSETS_DIR, "video_inputs.txt")
with open(concat_script, "w", encoding="utf-8") as f:
    f.write(f"file '{p1}'\nduration 5\n")
    f.write(f"file '{p2}'\nduration 5\n")
    f.write(f"file '{p3}'\nduration 5\n")
    f.write(f"file '{p3}'\n")

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
    print(f"Successfully generated authentic demo video at: {OUTPUT_VIDEO_ROOT}")
    print(f"Video size: {os.path.getsize(OUTPUT_VIDEO_ROOT)} bytes")
else:
    print("FFmpeg stderr:", res.stderr)
