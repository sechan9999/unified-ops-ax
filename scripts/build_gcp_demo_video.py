"""
Build MP4 Demo Video with 7 Authentic Google Cloud Console Screenshots and Voiceover Narration Audio.
"""
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")
OUTPUT_VIDEO = os.path.join(REPO_ROOT, "unified_ops_ax_demo_video.mp4")
AUDIO_FILE = os.path.join(ASSETS_DIR, "narration.wav")

img1 = os.path.join(ASSETS_DIR, "gcp_console_1_observability.png")
img1b = os.path.join(ASSETS_DIR, "gcp_console_1b_observability.png")
img2 = os.path.join(ASSETS_DIR, "gcp_console_2_revisions.png")
img3 = os.path.join(ASSETS_DIR, "gcp_console_3_source.png")
img4 = os.path.join(ASSETS_DIR, "gcp_console_4_yaml.png")
img5 = os.path.join(ASSETS_DIR, "gcp_console_5_streamlit_map.png")
img6 = os.path.join(ASSETS_DIR, "streamlit_dashboard.png")

p1 = img1.replace("\\", "/")
p1b = img1b.replace("\\", "/")
p2 = img2.replace("\\", "/")
p3 = img3.replace("\\", "/")
p4 = img4.replace("\\", "/")
p5 = img5.replace("\\", "/")
p6 = img6.replace("\\", "/")
p_audio = AUDIO_FILE.replace("\\", "/")

print(f"Checking assets:\n Audio: {os.path.exists(AUDIO_FILE)}\n 1 (Observability 1): {os.path.exists(img1)}\n 1b (Observability 2): {os.path.exists(img1b)}\n 2 (Revisions): {os.path.exists(img2)}\n 3 (Source): {os.path.exists(img3)}\n 4 (YAML): {os.path.exists(img4)}\n 5 (Streamlit Map): {os.path.exists(img5)}\n 6 (3D PyDeck): {os.path.exists(img6)}")

concat_script = os.path.join(ASSETS_DIR, "video_inputs.txt")
with open(concat_script, "w", encoding="utf-8") as f:
    f.write(f"file '{p1}'\nduration 10\n")
    f.write(f"file '{p1b}'\nduration 10\n")
    f.write(f"file '{p2}'\nduration 10\n")
    f.write(f"file '{p3}'\nduration 10\n")
    f.write(f"file '{p4}'\nduration 10\n")
    f.write(f"file '{p5}'\nduration 10\n")
    f.write(f"file '{p6}'\nduration 12.5\n")
    f.write(f"file '{p6}'\n")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_script,
    "-i", p_audio,
    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
    "-c:v", "libx264",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    "-r", "30",
    "-preset", "fast",
    OUTPUT_VIDEO
]

print("Running ffmpeg build command for 7-slide narrated video...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg returncode:", res.returncode)
if res.returncode == 0:
    print(f"Successfully generated 72s narrated demo video at: {OUTPUT_VIDEO}")
    print(f"Video size: {os.path.getsize(OUTPUT_VIDEO)} bytes")
else:
    print("FFmpeg stderr:", res.stderr)
