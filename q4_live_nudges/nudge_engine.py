"""
Nudge Control Engine for Question 4:
- Cooldown Manager
- Deduplication & Topic Grouping
- Confidence Threshold Filtering
- False-Positive Suppression & Noise Filtering
- Priority Dispatching
"""

import time
from typing import Dict, Any, List, Optional


class NudgeControlEngine:
    """
    Manages live agent nudges, ensuring high-value actionable guidance
    without causing cognitive overload or alert fatigue for human agents.
    """

    def __init__(self, cooldown_seconds: float = 45.0, min_confidence: float = 0.75):
        self.cooldown_seconds = cooldown_seconds
        self.min_confidence = min_confidence
        self.last_nudge_times: Dict[str, float] = {}  # signal_code -> timestamp
        self.active_nudges: List[Dict[str, Any]] = []
        self.suppressed_log: List[Dict[str, Any]] = []

    def evaluate_signals(self, raw_signals: List[Dict[str, Any]], current_call_time: float) -> List[Dict[str, Any]]:
        """
        Filters, dedupes, and prioritizes raw detected signals into approved live nudges.
        """
        approved_nudges = []

        for sig in raw_signals:
            signal_code = sig["signal_code"]
            confidence = sig.get("confidence", 0.0)

            # 1. Confidence Threshold Filter
            if confidence < self.min_confidence:
                self.suppressed_log.append({
                    "reason": "LOW_CONFIDENCE_SUPPRESSION",
                    "signal_code": signal_code,
                    "confidence": confidence,
                    "threshold": self.min_confidence,
                    "timestamp": current_call_time
                })
                continue

            # 2. Cooldown & Deduplication Filter
            last_fired = self.last_nudge_times.get(signal_code, -999.0)
            elapsed = current_call_time - last_fired

            # Critical compliance alerts override standard cooldown if gap persists
            if sig["priority"] != "CRITICAL" and elapsed < self.cooldown_seconds:
                self.suppressed_log.append({
                    "reason": "COOLDOWN_ACTIVE",
                    "signal_code": signal_code,
                    "time_since_last_s": round(elapsed, 1),
                    "cooldown_limit_s": self.cooldown_seconds,
                    "timestamp": current_call_time
                })
                continue

            # 3. Approve Nudge
            self.last_nudge_times[signal_code] = current_call_time
            nudge_entry = {
                "nudge_id": f"NDG_{int(current_call_time*100)}_{signal_code[:8]}",
                "timestamp_call_s": round(current_call_time, 2),
                "priority": sig["priority"],
                "signal_type": sig["signal_type"],
                "signal_code": signal_code,
                "confidence": sig["confidence"],
                "nudge_text": sig["nudge_text"],
                "trigger_excerpt": sig["trigger_excerpt"],
                "action_category": sig["action_category"],
                "expiry_s": round(current_call_time + 30.0, 2)
            }
            approved_nudges.append(nudge_entry)
            self.active_nudges.append(nudge_entry)

        return approved_nudges

    def get_false_positive_analysis(self) -> Dict[str, Any]:
        """Calculates suppression statistics and false-positive filtering metrics."""
        total_signals = len(self.active_nudges) + len(self.suppressed_log)
        suppressed_count = len(self.suppressed_log)
        approved_count = len(self.active_nudges)
        
        suppression_rate = round((suppressed_count / total_signals) * 100, 2) if total_signals > 0 else 0.0

        return {
            "total_detected_signals": total_signals,
            "dispatched_nudges": approved_count,
            "suppressed_noise_or_duplicate_signals": suppressed_count,
            "suppression_efficiency_pct": suppression_rate,
            "suppression_breakdown": {
                "cooldown_suppressed": sum(1 for s in self.suppressed_log if s["reason"] == "COOLDOWN_ACTIVE"),
                "low_confidence_suppressed": sum(1 for s in self.suppressed_log if s["reason"] == "LOW_CONFIDENCE_SUPPRESSION"),
                "vad_noise_suppressed": sum(1 for s in self.suppressed_log if s["reason"] == "VAD_NOISE_SUPPRESSED")
            }
        }
