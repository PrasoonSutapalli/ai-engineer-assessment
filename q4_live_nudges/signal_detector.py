"""
Real-time Conversational Signal Extraction Engine for Question 4.
Detects:
1. Missed Cross-Sell / Upsell Opportunities
2. Compliance & Regulatory Gaps (Skipped Disclosures)
3. Customer Frustration & Negative Sentiment Escalation
4. Payment Difficulty & Churn Risks
"""

import time
import re
from typing import Dict, Any, List, Optional


class SignalExtractionEngine:
    """
    Analyzes live streaming utterance chunks to identify business signals,
    regulatory compliance risks, and sentiment friction.
    """

    def __init__(self):
        # Patterns for Missed Cross-Sell Opportunities
        self.cross_sell_patterns = [
            (r'\b(second car|another car|two vehicles|truck|motorcycle|second vehicle)\b', "MULTI_VEHICLE_DISCOUNT", "Customer mentioned second vehicle. Suggest multi-vehicle bundle (15% discount)."),
            (r'\b(my kids|my wife|my husband|whole family|family members|daughter|son)\b', "FAMILY_FLOATER_UPGRADE", "Customer mentioned family members. Recommend upgrading to Family Floater plan."),
            (r'\b(business|commercial|company fleet|startup|employees)\b', "SME_COMMERCIAL_PACKAGE", "Customer mentioned business operations. Offer Group Health / SME commercial coverage.")
        ]

        # Patterns for Compliance Gaps & Regulatory Risks
        self.compliance_risk_patterns = [
            (r'\b(guaranteed return|no risk|never lose money|100% payout always)\b', "MISLEADING_GUARANTEE", "Agent made absolute return claim. Issue required regulatory disclaimer immediately."),
            (r'\b(skip the paperwork|don\'t mention diabetes|hide the condition)\b', "UNDERWRITING_NON_DISCLOSURE", "Potential non-disclosure detected. Remind agent that undisclosed PED voids claims."),
            (r'\b(ready to purchase|charge my card|sign me up)\b', "MISSING_FREE_LOOK_DISCLOSURE", "Customer ready to buy. Remind agent to state mandatory 30-day Free Look & Cancellation rights.")
        ]

        # Patterns for Rising Frustration / Sentiment Friction
        self.frustration_patterns = [
            (r'\b(ridiculous|waste of time|terrible service|been waiting forever|on hold|frustrated|angry|useless)\b', "HIGH_FRUSTRATION", "Customer expressing irritation. Acknowledge frustration and de-escalate tone before pitching."),
            (r'\b(already told you|repeating myself|listen to me|you\'re not listening)\b', "REPETITION_FRUSTRATION", "Customer repeating details. Summarize their points to demonstrate active listening.")
        ]

        # Patterns for Payment Difficulty / Churn Risk
        self.payment_patterns = [
            (r'\b(can\'t afford|too expensive|out of my budget|lost my job|tight on cash|no money right now)\b', "PAYMENT_DIFFICULTY", "Customer experiencing budget constraints. Offer flexible monthly auto-debit or split-deductible option.")
        ]

    def analyze_utterance(self, speaker: str, text: str, call_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extracts actionable conversational signals from a single streaming utterance.
        Returns a list of candidate signals with confidence scores and latency timestamp.
        """
        signals = []
        text_lower = text.lower()
        t_start = time.perf_counter()

        # 1. Check Missed Opportunities (Customer channel)
        if speaker.upper() == "CUSTOMER":
            for pattern, code, nudge_msg in self.cross_sell_patterns:
                if re.search(pattern, text_lower):
                    signals.append({
                        "signal_type": "MISSED_OPPORTUNITY",
                        "signal_code": code,
                        "priority": "MEDIUM",
                        "confidence": 0.92,
                        "nudge_text": nudge_msg,
                        "trigger_excerpt": text,
                        "action_category": "CROSS_SELL_PROMPT"
                    })

            # Check Frustration
            for pattern, code, nudge_msg in self.frustration_patterns:
                if re.search(pattern, text_lower):
                    signals.append({
                        "signal_type": "RISING_FRUSTRATION",
                        "signal_code": code,
                        "priority": "HIGH",
                        "confidence": 0.88,
                        "nudge_text": nudge_msg,
                        "trigger_excerpt": text,
                        "action_category": "SENTIMENT_DE_ESCALATION"
                    })

            # Check Payment Difficulty
            for pattern, code, nudge_msg in self.payment_patterns:
                if re.search(pattern, text_lower):
                    signals.append({
                        "signal_type": "PAYMENT_DIFFICULTY",
                        "signal_code": code,
                        "priority": "HIGH",
                        "confidence": 0.90,
                        "nudge_text": nudge_msg,
                        "trigger_excerpt": text,
                        "action_category": "AFFORDABILITY_SUPPORT"
                    })

        # 2. Check Compliance Risks (Agent or Customer channel)
        for pattern, code, nudge_msg in self.compliance_risk_patterns:
            if re.search(pattern, text_lower):
                signals.append({
                    "signal_type": "COMPLIANCE_GAP",
                    "signal_code": code,
                    "priority": "CRITICAL",
                    "confidence": 0.95,
                    "nudge_text": nudge_msg,
                    "trigger_excerpt": text,
                    "action_category": "MANDATORY_REGULATORY_DISCLOSURE"
                })

        extraction_latency_ms = (time.perf_counter() - t_start) * 1000.0
        for s in signals:
            s["extraction_latency_ms"] = round(extraction_latency_ms, 2)

        return signals
