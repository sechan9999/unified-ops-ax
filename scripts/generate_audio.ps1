Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$wavPath = "c:\Users\secha\.gemini\antigravity-ide\scratch\unified-ops-ax\unified-ops-ax\assets\narration.wav"
$synth.SetOutputToWaveFile($wavPath)

$script = "Welcome to Unified Ops AX: Fleet Control Center. Our application runs serverless on Google Cloud Run under project AgenticHackathon. Here in the Observability dashboard, we observe request volume and sub-second latency breakdown. In the Container metrics view, health checks report 100 percent healthy status with automatic instance scaling based on concurrency and CPU utilization. Looking at the Revisions tab, active revision unified-ops-ax-00015-8pd is routing 100 percent of production traffic live at unified-ops-ax-652787573242.us-central1.run.app. Under source code, our 5 Governed Agents operate alongside Vertex AI Gemini 3.5 Flash, Pub Sub event bus, Firestore audit logs, and Cloud SQL. The Knative Service YAML confirms full Google Cloud infrastructure deployment. Here on the live Streamlit dashboard, real-time 3D spatial fleet maps, unit telemetry, and Evolve Agent diagnostic audits orchestrate operations seamlessly."

$synth.Speak($script)
$synth.Dispose()
Write-Host "Audio narration updated successfully at: $wavPath"
