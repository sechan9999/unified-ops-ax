Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$wavPath = "c:\Users\secha\.gemini\antigravity-ide\scratch\unified-ops-ax\unified-ops-ax\assets\narration.wav"
$synth.SetOutputToWaveFile($wavPath)

$script = "Welcome to Unified Ops AX: Fleet Control Center. Our application runs serverless on Google Cloud Run under project AgenticHackathon. Here in the Google Cloud Console, we see live service revisions serving 100 percent of traffic at unified-ops-ax-652787573242.us-central1.run.app. Under source code, our 5 Governed Agents are deployed alongside Vertex AI Gemini 3.5 Flash, Pub Sub event bus, Firestore audit logs, and Cloud SQL. Here on the live Streamlit dashboard, real-time 3D spatial fleet maps, unit telemetry, and Evolve Agent diagnostic audits are orchestrating operations seamlessly."

$synth.Speak($script)
$synth.Dispose()
Write-Host "Audio narration generated successfully at: $wavPath"
