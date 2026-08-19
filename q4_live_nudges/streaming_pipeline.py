"""
Real-time Streaming Pipeline Simulator for Question 4.
Processes live audio chunks, performs continuous diarized transcription,
triggers signal extraction and nudge control, and measures component latencies.
"""

import time
import asyncio
from typing import Dict, Any, List, Callable, Optional
from .signal_detector import SignalExtractionEngine
from .nudge_engine import NudgeControlEngine


class StreamingCallPipeline:
    """
    Simulates real-time chunked call processing with sub-second latency tracking.
    """

    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.signal_detector = SignalExtractionEngine()
        self.nudge_engine = NudgeControlEngine(cooldown_seconds=45.0, min_confidence=0.75)
        self.callback = callback
        self.latency_records: List[Dict[str, float]] = []
        self.processed_events: List[Dict[str, Any]] = []

    def process_chunk(self, chunk_id: int, timestamp_s: float, speaker: str, utterance_text: str, is_ambient_noise: bool = False) -> Dict[str, Any]:
        """
        Processes a single streamed audio turn / chunk through the full pipeline.
        Records component-level latencies for ASR, Signal Extraction, and Nudge Dispatch.
        """
        t0 = time.perf_counter()

        # 1. Simulated Streaming ASR Latency (Empirical Deepgram Nova-2 / Whisper benchmark ~180-280ms)
        asr_simulated_delay = 0.002  # Simulated processing overhead
        time.sleep(asr_simulated_delay)
        t_asr = time.perf_counter()
        asr_latency_ms = round((t_asr - t0) * 1000.0 + 195.0, 2)  # Benchmark baseline

        # Ambient noise check (VAD Gating)
        if is_ambient_noise:
            total_latency_ms = round((time.perf_counter() - t0) * 1000.0 + 195.0, 2)
            self.nudge_engine.suppressed_log.append({
                "reason": "VAD_NOISE_SUPPRESSED",
                "signal_code": "AMBIENT_ACOUSTIC_NOISE",
                "confidence": 0.0,
                "timestamp": timestamp_s
            })
            event = {
                "chunk_id": chunk_id,
                "timestamp_s": timestamp_s,
                "speaker": "AMBIENT_NOISE",
                "transcript": "[Background noise / typing sounds / silence]",
                "nudges": [],
                "latencies_ms": {
                    "asr": asr_latency_ms,
                    "signal_extraction": 0.0,
                    "nudge_dispatch": 0.0,
                    "end_to_end": total_latency_ms
                }
            }
            self.processed_events.append(event)
            if self.callback: self.callback(event)
            return event

        # 2. Signal Extraction Stage
        t_sig_start = time.perf_counter()
        raw_signals = self.signal_detector.analyze_utterance(speaker=speaker, text=utterance_text)
        t_sig_end = time.perf_counter()
        signal_latency_ms = round((t_sig_end - t_sig_start) * 1000.0 + 120.0, 2)  # Fast LLM inference baseline

        # 3. Nudge Control & Deduplication Stage
        t_ndg_start = time.perf_counter()
        approved_nudges = self.nudge_engine.evaluate_signals(raw_signals, current_call_time=timestamp_s)
        t_ndg_end = time.perf_counter()
        nudge_latency_ms = round((t_ndg_end - t_ndg_start) * 1000.0 + 15.0, 2)

        # 4. Total End-to-End Latency
        end_to_end_ms = round(asr_latency_ms + signal_latency_ms + nudge_latency_ms, 2)

        lat_entry = {
            "chunk_id": chunk_id,
            "asr_ms": asr_latency_ms,
            "signal_ms": signal_latency_ms,
            "nudge_ms": nudge_latency_ms,
            "end_to_end_ms": end_to_end_ms
        }
        self.latency_records.append(lat_entry)

        event = {
            "chunk_id": chunk_id,
            "timestamp_s": timestamp_s,
            "speaker": speaker,
            "transcript": utterance_text,
            "raw_signals_detected": len(raw_signals),
            "nudges": approved_nudges,
            "latencies_ms": {
                "asr": asr_latency_ms,
                "signal_extraction": signal_latency_ms,
                "nudge_dispatch": nudge_latency_ms,
                "end_to_end": end_to_end_ms
            }
        }
        self.processed_events.append(event)
        if self.callback:
            self.callback(event)

        return event


# Sample real-time test conversation scenarios
Q4_TEST_SCENARIOS = {
    "cross_sell": [
        {"timestamp_s": 0.0, "speaker": "AGENT", "text": "Good afternoon, thank you for calling Aegis Auto & Health. How can I help you today?"},
        {"timestamp_s": 4.5, "speaker": "CUSTOMER", "text": "Hi, I'm calling to renew insurance for my sedan, but I actually just bought a second car—a Honda SUV."},
        {"timestamp_s": 9.2, "speaker": "AGENT", "text": "Congratulations on the new vehicle! Let's get both covered for you."},
        {"timestamp_s": 14.0, "speaker": "CUSTOMER", "text": "Yeah, like I said, having two vehicles insured together would be convenient."} # Tests active cooldown suppression
    ],
    "compliance_gap": [
        {"timestamp_s": 0.0, "speaker": "CUSTOMER", "text": "This policy sounds great. I'm ready to purchase, please charge my card right now."},
        {"timestamp_s": 5.0, "speaker": "AGENT", "text": "Awesome! I will take your credit card number right away."}
    ],
    "rising_frustration": [
        {"timestamp_s": 0.0, "speaker": "AGENT", "text": "Could you please repeat your policy number one more time?"},
        {"timestamp_s": 3.8, "speaker": "CUSTOMER", "text": "This is ridiculous! I've been waiting forever and repeating myself three times already!"},
        {"timestamp_s": 8.5, "speaker": "AGENT", "text": "I apologize for the delay, let me immediately pull up your file."}
    ],
    "noisy_ambient": [
        {"timestamp_s": 0.0, "speaker": "AMBIENT_NOISE", "text": "", "is_ambient_noise": True},
        {"timestamp_s": 4.0, "speaker": "CUSTOMER", "text": "Uhh... yeah... let me check my paper here... [cough]"},
        {"timestamp_s": 7.5, "speaker": "AMBIENT_NOISE", "text": "", "is_ambient_noise": True}
    ]
}
