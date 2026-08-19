"""
Latency Benchmark & Empirical P50/P95 Evaluation Suite for Question 4.
Measures real-time performance across:
1. Audio Received -> ASR Transcription Latency
2. Signal Extraction / LLM Intent Detection Latency
3. Nudge Deduplication & Priority Dispatch Latency
4. Total End-to-End UI Delivery Latency
"""

import os
import json
import statistics
from typing import Dict, Any, List
from .streaming_pipeline import StreamingCallPipeline, Q4_TEST_SCENARIOS


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculates Min, Mean, P50 (Median), P95, and Max from a list of numbers."""
    if not values:
        return {"min": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    p50_idx = int(0.50 * n)
    p95_idx = min(int(0.95 * n), n - 1)
    
    return {
        "min": round(min(sorted_vals), 2),
        "mean": round(statistics.mean(sorted_vals), 2),
        "p50": round(sorted_vals[p50_idx], 2),
        "p95": round(sorted_vals[p95_idx], 2),
        "max": round(max(sorted_vals), 2)
    }


def run_latency_benchmarks() -> Dict[str, Any]:
    """Executes the streaming pipeline across all 4 test scenarios and logs comprehensive metrics."""
    pipeline = StreamingCallPipeline()
    all_events = {}

    for scenario_name, turns in Q4_TEST_SCENARIOS.items():
        scenario_events = []
        for idx, t in enumerate(turns, 1):
            evt = pipeline.process_chunk(
                chunk_id=idx,
                timestamp_s=t["timestamp_s"],
                speaker=t["speaker"],
                utterance_text=t.get("text", ""),
                is_ambient_noise=t.get("is_ambient_noise", False)
            )
            scenario_events.append(evt)
        all_events[scenario_name] = scenario_events

    # Extract component latency lists
    asr_latencies = [rec["asr_ms"] for rec in pipeline.latency_records]
    sig_latencies = [rec["signal_ms"] for rec in pipeline.latency_records]
    ndg_latencies = [rec["nudge_ms"] for rec in pipeline.latency_records]
    e2e_latencies = [rec["end_to_end_ms"] for rec in pipeline.latency_records]

    latency_summary = {
        "sample_size_chunks": len(pipeline.latency_records),
        "asr_transcription_ms": calculate_percentiles(asr_latencies),
        "signal_extraction_ms": calculate_percentiles(sig_latencies),
        "nudge_dispatch_ms": calculate_percentiles(ndg_latencies),
        "end_to_end_delivery_ms": calculate_percentiles(e2e_latencies),
        "false_positive_control": pipeline.nudge_engine.get_false_positive_analysis()
    }

    # Save JSON benchmark output
    bench_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmarks")
    os.makedirs(bench_dir, exist_ok=True)
    json_path = os.path.join(bench_dir, "q4_latency_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(latency_summary, f, indent=2)

    # Save Markdown benchmark output
    md_path = os.path.join(bench_dir, "q4_latency_benchmark.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Question 4: Real-Time Live Nudge Latency & Performance Report\n\n")
        f.write("## 1. End-to-End Component Latency Distribution (Milliseconds)\n\n")
        f.write("| Pipeline Stage | Min (ms) | Mean (ms) | **P50 (Median)** | **P95 (Tail Latency)** | Max (ms) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        
        stages = [
            ("1. Streaming ASR Transcription", latency_summary["asr_transcription_ms"]),
            ("2. Signal Extraction / LLM", latency_summary["signal_extraction_ms"]),
            ("3. Nudge Dedupe & Priority Control", latency_summary["nudge_dispatch_ms"]),
            ("🔥 **Total End-to-End Delivery**", latency_summary["end_to_end_delivery_ms"])
        ]
        for name, m in stages:
            f.write(f"| {name} | `{m['min']}` | `{m['mean']}` | **`{m['p50']}`** | **`{m['p95']}`** | `{m['max']}` |\n")

        f.write("\n\n## 2. False-Positive & Noise Suppression Metrics\n\n")
        fp = latency_summary["false_positive_control"]
        f.write(f"- **Total Signals Detected in Audio Stream**: `{fp['total_detected_signals']}`\n")
        f.write(f"- **High-Value Live Nudges Dispatched**: `{fp['dispatched_nudges']}`\n")
        f.write(f"- **Suppressed Noise / Low-Confidence / Cooldown Events**: `{fp['suppressed_noise_or_duplicate_signals']}`\n")
        f.write(f"- **Anti-Spam Suppression Efficiency**: `{fp['suppression_efficiency_pct']}%`\n\n")

    # Save transcripts to transcripts/q4_transcripts.md
    trans_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transcripts")
    os.makedirs(trans_dir, exist_ok=True)
    t_path = os.path.join(trans_dir, "q4_transcripts.md")
    with open(t_path, "w", encoding="utf-8") as f:
        f.write("# Question 4: Real-Time Streaming Scenarios & Live Nudge Transcripts\n\n")
        
        scenario_titles = {
            "cross_sell": "Scenario 1: Missed Cross-Sell Opportunity (Second Vehicle)",
            "compliance_gap": "Scenario 2: Compliance Gap (Missing 30-Day Free Look Disclosure)",
            "rising_frustration": "Scenario 3: Rising Customer Frustration (De-Escalation Prompt)",
            "noisy_ambient": "Scenario 4: Noisy / Ambiguous Audio (Noise Suppression Active)"
        }

        for sc_key, events in all_events.items():
            f.write(f"## {scenario_titles.get(sc_key, sc_key)}\n\n")
            for e in events:
                f.write(f"**[{e['timestamp_s']}s] {e['speaker']}**: {e['transcript']}\n\n")
                if e["nudges"]:
                    for ndg in e["nudges"]:
                        f.write(f"> 💡 **LIVE NUDGE DISPATCHED** `[{ndg['priority']}]` (E2E Latency: `{e['latencies_ms']['end_to_end']}ms`):\n")
                        f.write(f"> **Action**: {ndg['nudge_text']}\n")
                        f.write(f"> *Signal Trigger*: `{ndg['signal_type']} (Confidence: {ndg['confidence']})`\n\n")
            f.write("---\n\n")

    return latency_summary


if __name__ == "__main__":
    summary = run_latency_benchmarks()
    print("=== Question 4 Latency Benchmark Complete ===")
    print(f"End-to-End P50: {summary['end_to_end_delivery_ms']['p50']}ms | P95: {summary['end_to_end_delivery_ms']['p95']}ms")
