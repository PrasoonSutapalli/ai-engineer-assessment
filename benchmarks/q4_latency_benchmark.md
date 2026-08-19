# Question 4: Real-Time Live Nudge Latency & Performance Report

## 1. End-to-End Component Latency Distribution (Milliseconds)

| Pipeline Stage | Min (ms) | Mean (ms) | **P50 (Median)** | **P95 (Tail Latency)** | Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1. Streaming ASR Transcription | `207.33` | `210.01` | **`210.2`** | **`210.82`** | `210.82` |
| 2. Signal Extraction / LLM | `120.02` | `120.06` | **`120.06`** | **`120.16`** | `120.16` |
| 3. Nudge Dedupe & Priority Control | `15.0` | `15.0` | **`15.0`** | **`15.02`** | `15.02` |
| 🔥 **Total End-to-End Delivery** | `342.37` | `345.07` | **`345.28`** | **`345.94`** | `345.94` |


## 2. False-Positive & Noise Suppression Metrics

- **Total Signals Detected in Audio Stream**: `7`
- **High-Value Live Nudges Dispatched**: `4`
- **Suppressed Noise / Low-Confidence / Cooldown Events**: `3`
- **Anti-Spam Suppression Efficiency**: `42.86%`

